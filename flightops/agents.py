from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


PRIORITY_WEIGHTS = {"low": 0.8, "medium": 1.0, "high": 1.35}


@dataclass(frozen=True)
class AgentFinding:
    agent: str
    status: str
    risk_score: float
    summary: str
    evidence: list[str]
    signals: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "status": self.status,
            "risk_score": round(self.risk_score, 2),
            "summary": self.summary,
            "evidence": self.evidence,
            "signals": self.signals,
        }


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def minutes_between(start: str, end: str) -> int:
    delta = parse_time(end) - parse_time(start)
    return round(delta.total_seconds() / 60)


def get_flight(data: dict[str, Any], flight_number: str) -> dict[str, Any]:
    return next(flight for flight in data["scheduled_flights"] if flight["flight"] == flight_number)


def get_aircraft(data: dict[str, Any], tail: str) -> dict[str, Any]:
    return next(aircraft for aircraft in data["fleet"] if aircraft["tail"] == tail)


def get_crew(data: dict[str, Any], crew_id: str) -> dict[str, Any]:
    return next(crew for crew in data["crew_rosters"] if crew["crew_id"] == crew_id)


def flight_connection_exposure(data: dict[str, Any], flight_number: str) -> dict[str, Any]:
    connections = [
        connection
        for connection in data["passenger_connections"]
        if connection["inbound_flight"] == flight_number
    ]
    passengers = sum(connection["passenger_count"] for connection in connections)
    cost = sum(
        connection["passenger_count"] * connection["misconnect_cost_usd_per_passenger"]
        for connection in connections
    )
    protection_minutes = min(
        [connection["protected_if_arrival_delay_under_minutes"] for connection in connections],
        default=90,
    )
    return {
        "connections": connections,
        "passengers": passengers,
        "cost_usd": cost,
        "protection_minutes": protection_minutes,
    }


class WeatherAgent:
    name = "weather_agent"

    def run(self, data: dict[str, Any]) -> AgentFinding:
        forecast = next(
            item for item in data["weather_feed"]["airport_forecasts"] if item["airport"] == "SGN"
        )
        hourly = forecast["hourly_risk"]
        peak = max(hourly, key=lambda item: item["delay_risk_score"])
        first_high = next(item for item in hourly if item["delay_risk_score"] >= 0.7)
        min_arrival_capacity = min(item["arrival_capacity_per_hour"] for item in hourly)
        normal_capacity = hourly[0]["arrival_capacity_per_hour"]
        capacity_drop = normal_capacity - min_arrival_capacity
        notams = [
            notam
            for notam in data["notams"]
            if notam["airport"] == "SGN" and notam["category"] in {"ATFM", "RAMP"}
        ]
        evidence = [
            f"Peak SGN weather risk is {peak['delay_risk_score']:.0%} at {peak['local_time']}.",
            f"Arrival capacity falls from {normal_capacity}/hour to {min_arrival_capacity}/hour.",
            f"First high-risk operating hour starts at {first_high['local_time']} local.",
        ]
        if notams:
            evidence.append(
                f"{len(notams)} active SGN operational NOTAMs add flow-control or ramp-stop risk."
            )

        return AgentFinding(
            agent=self.name,
            status="complete",
            risk_score=peak["delay_risk_score"],
            summary=(
                "SGN capacity is forecast to degrade sharply after "
                f"{first_high['local_time']} local, with peak disruption at {peak['local_time']}."
            ),
            evidence=evidence,
            signals={
                "first_high_risk_time": first_high["local_time"],
                "peak_risk_time": peak["local_time"],
                "peak_risk_score": peak["delay_risk_score"],
                "min_arrival_capacity_per_hour": min_arrival_capacity,
                "capacity_drop_per_hour": capacity_drop,
            },
        )


class AircraftAgent:
    name = "aircraft_agent"

    def run(self, data: dict[str, Any]) -> AgentFinding:
        flights = data["scheduled_flights"]
        vj152 = get_flight(data, "VJ152")
        target_capacity = vj152["passengers_booked"]
        target_departure = parse_time(vj152["scheduled_departure_local"])
        candidates = []
        for aircraft in data["fleet"]:
            capacity_margin = aircraft["seat_capacity"] - target_capacity
            maintenance_text = " ".join(log["text"] for log in data["maintenance_logs"] if log["tail"] == aircraft["tail"])
            severe_mel = any("weather radar" in item["description"].lower() for item in aircraft["mel_items"])
            same_airport = aircraft["current_airport"] == "SGN"
            arriving_to_good_gate = aircraft.get("gate") == "18"
            available_from = aircraft.get("estimated_on_block_local") or aircraft.get("available_from_local")
            available_before_departure = parse_time(available_from) <= target_departure if available_from else False
            narrow_body = aircraft["type"].startswith(("A320", "A321"))
            maintenance_penalty = 0.2 if "A-check due" in maintenance_text else 0.0
            mel_penalty = 0.35 if severe_mel else 0.0
            availability_penalty = 0.55 if not available_before_departure else 0.0
            fleet_penalty = 0.45 if not narrow_body else 0.0
            capacity_score = 0.0 if capacity_margin < 0 else min(0.3, capacity_margin / 240)
            availability_score = 0.25 if same_airport else 0.1
            gate_score = 0.2 if arriving_to_good_gate else 0.0
            score = (
                0.45
                + capacity_score
                + availability_score
                + gate_score
                - maintenance_penalty
                - mel_penalty
                - availability_penalty
                - fleet_penalty
            )
            candidates.append(
                {
                    "tail": aircraft["tail"],
                    "type": aircraft["type"],
                    "seat_capacity": aircraft["seat_capacity"],
                    "capacity_margin": capacity_margin,
                    "score": round(max(0, min(1, score)), 2),
                    "maintenance_penalty": maintenance_penalty,
                    "mel_penalty": mel_penalty,
                    "available_before_departure": available_before_departure,
                    "narrow_body": narrow_body,
                    "current_airport": aircraft["current_airport"],
                    "gate": aircraft.get("gate") or aircraft.get("stand"),
                }
            )

        viable = [
            candidate
            for candidate in candidates
            if candidate["capacity_margin"] >= 0
            and candidate["available_before_departure"]
            and candidate["narrow_body"]
        ]
        best = max(viable, key=lambda item: item["score"])
        original = get_aircraft(data, vj152["aircraft_tail"])
        protected = [
            flight["flight"]
            for flight in flights
            if flight["aircraft_tail"] == original["tail"] and flight["flight"] != "VJ152"
        ]

        return AgentFinding(
            agent=self.name,
            status="complete",
            risk_score=1 - best["score"],
            summary=(
                f"{best['tail']} is the strongest substitute for VJ152: it has "
                f"{best['seat_capacity']} seats, is positioned at SGN, and avoids the tighter "
                f"maintenance constraint on {original['tail']}."
            ),
            evidence=[
                f"VJ152 has {target_capacity} passengers; {best['tail']} has {best['seat_capacity']} seats.",
                f"{original['tail']} has an SGN A-check constraint; swapping protects later flights {', '.join(protected) or 'none'}.",
                f"{best['tail']} is associated with Gate {best['gate']}, the highest-scoring modeled domestic gate.",
            ],
            signals={
                "recommended_tail_for_vj152": best["tail"],
                "original_tail": original["tail"],
                "candidate_scores": sorted(candidates, key=lambda item: item["score"], reverse=True),
            },
        )


class CrewAgent:
    name = "crew_agent"

    def run(self, data: dict[str, Any]) -> AgentFinding:
        reserve_crews = [
            crew for crew in data["crew_rosters"] if crew["status"] == "reserve_at_sgn"
        ]
        checked_in = [
            crew for crew in data["crew_rosters"] if crew["status"] == "checked_in"
        ]
        constrained = [
            crew for crew in data["crew_rosters"] if crew.get("constraints")
        ]
        vj237 = get_flight(data, "VJ237")
        reserve = reserve_crews[0]
        reserve_buffer = minutes_between(
            reserve["reserve_available_from_local"], vj237["scheduled_departure_local"]
        )

        risk_score = 0.45
        if constrained:
            risk_score += 0.15
        if reserve_buffer < 60:
            risk_score += 0.1

        return AgentFinding(
            agent=self.name,
            status="complete",
            risk_score=min(risk_score, 0.95),
            summary=(
                "Crew coverage is feasible if the supervisor protects the checked-in VJ152 crew "
                "and uses SGN reserve crew for the lower-priority DAD sector if needed."
            ),
            evidence=[
                f"{len(checked_in)} crews are checked in for the morning wave.",
                f"Reserve crew {reserve['crew_id']} is airport standby from {reserve['reserve_available_from_local'][11:16]}.",
                f"{vj237['crew_id']} has a documented constraint, so VJ237 is safer with reserve coverage after a controlled delay.",
            ],
            signals={
                "reserve_crew_id": reserve["crew_id"],
                "reserve_buffer_minutes_before_vj237": reserve_buffer,
                "constrained_crews": [crew["crew_id"] for crew in constrained],
            },
        )


class MaintenanceAgent:
    name = "maintenance_agent"

    def run(self, data: dict[str, Any]) -> AgentFinding:
        issues = []
        for aircraft in data["fleet"]:
            for mel in aircraft["mel_items"]:
                text = f"{aircraft['tail']}: {mel['description']}"
                if "weather radar" in mel["description"].lower():
                    issues.append({"tail": aircraft["tail"], "severity": "dispatch_risk", "text": text})
                else:
                    issues.append({"tail": aircraft["tail"], "severity": "minor", "text": text})
            next_maintenance = aircraft["next_maintenance"]
            if next_maintenance["type"] in {"A-check", "defect rectification"}:
                issues.append(
                    {
                        "tail": aircraft["tail"],
                        "severity": "planning_constraint",
                        "text": f"{aircraft['tail']}: {next_maintenance['type']} due {next_maintenance['due_local'][11:16]} at {next_maintenance['airport_required']}",
                    }
                )

        dispatch_risk = [issue for issue in issues if issue["severity"] == "dispatch_risk"]
        planning = [issue for issue in issues if issue["severity"] == "planning_constraint"]
        risk_score = min(0.95, 0.35 + 0.2 * len(dispatch_risk) + 0.1 * len(planning))

        return AgentFinding(
            agent=self.name,
            status="complete",
            risk_score=risk_score,
            summary=(
                "Maintenance constraints favor keeping VN-A678 on the ground during the storm "
                "and avoiding any plan that leaves VN-A152 away from SGN past its A-check window."
            ),
            evidence=[issue["text"] for issue in issues[:4]],
            signals={
                "dispatch_risk_tails": [issue["tail"] for issue in dispatch_risk],
                "planning_constraint_tails": [issue["tail"] for issue in planning],
                "issue_count": len(issues),
            },
        )


class CostImpactAgent:
    name = "cost_impact_agent"

    def run(self, data: dict[str, Any]) -> AgentFinding:
        scored = []
        for flight in data["scheduled_flights"]:
            exposure = flight_connection_exposure(data, flight["flight"])
            priority_weight = PRIORITY_WEIGHTS.get(flight["priority"], 1.0)
            aircraft = get_aircraft(data, flight["aircraft_tail"])
            load_factor = flight["passengers_booked"] / aircraft["seat_capacity"]
            score = exposure["cost_usd"] * priority_weight + flight["passengers_booked"] * load_factor * 12
            scored.append(
                {
                    "flight": flight["flight"],
                    "route": flight["route"],
                    "priority": flight["priority"],
                    "passengers": flight["passengers_booked"],
                    "connection_passengers": exposure["passengers"],
                    "connection_cost_usd": exposure["cost_usd"],
                    "score": round(score),
                    "protection_minutes": exposure["protection_minutes"],
                }
            )

        ranked = sorted(scored, key=lambda item: item["score"], reverse=True)
        top = ranked[0]
        delay_candidate = next(item for item in ranked if item["flight"] == "VJ237")
        risk_score = min(0.95, top["score"] / 14000)

        return AgentFinding(
            agent=self.name,
            status="complete",
            risk_score=risk_score,
            summary=(
                f"{top['flight']} is the most valuable flight to protect because it carries "
                f"{top['connection_passengers']} connecting passengers and the highest modeled disruption score."
            ),
            evidence=[
                f"{top['flight']} connection exposure is USD {top['connection_cost_usd']:,}.",
                f"VJ237 has lower disruption score ({delay_candidate['score']:,}) and can absorb controlled delay.",
                f"Ranked protection order: {', '.join(item['flight'] for item in ranked[:4])}.",
            ],
            signals={
                "ranked_flights": ranked,
                "protect_flight": top["flight"],
                "delay_candidate": "VJ237",
            },
        )
