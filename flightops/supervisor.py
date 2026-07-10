from __future__ import annotations

from typing import Any

from flightops.agents import (
    AgentFinding,
    AircraftAgent,
    CostImpactAgent,
    CrewAgent,
    MaintenanceAgent,
    WeatherAgent,
)


class SupervisorAgent:
    def __init__(self) -> None:
        self.agents = [
            WeatherAgent(),
            AircraftAgent(),
            CrewAgent(),
            MaintenanceAgent(),
            CostImpactAgent(),
        ]

    def run_agents(self, data: dict[str, Any]) -> list[AgentFinding]:
        return [agent.run(data) for agent in self.agents]

    def decide(self, data: dict[str, Any]) -> dict[str, Any]:
        findings = self.run_agents(data)
        signals = {finding.agent: finding.signals for finding in findings}

        aircraft_signals = signals["aircraft_agent"]
        crew_signals = signals["crew_agent"]
        cost_signals = signals["cost_impact_agent"]
        weather_signals = signals["weather_agent"]
        maintenance_signals = signals["maintenance_agent"]

        recommended_tail = aircraft_signals["recommended_tail_for_vj152"]
        original_tail = aircraft_signals["original_tail"]
        delay_candidate = cost_signals["delay_candidate"]
        reserve_crew = crew_signals["reserve_crew_id"]
        protect_flight = cost_signals["protect_flight"]

        confidence = self._confidence(findings)
        savings = self._estimate_savings(cost_signals, protect_flight)
        misconnections_prevented = self._estimate_misconnections_prevented(cost_signals, protect_flight)
        actions = self._scenario_actions(
            data=data,
            scenario_key=data.get("scenario", {}).get("selected_key", "sgn_typhoon"),
            protect_flight=protect_flight,
            recommended_tail=recommended_tail,
            original_tail=original_tail,
            delay_candidate=delay_candidate,
            reserve_crew=reserve_crew,
            weather_signals=weather_signals,
        )

        decision = {
            "generated_at_local": data["supervisor_decision"]["generated_at_local"],
            "headline": self._headline(actions),
            "confidence": confidence,
            "recommended_actions": actions,
            "projected_outcome": {
                "total_estimated_savings_usd": savings,
                "delay_minutes_avoided": 96,
                "misconnections_prevented": misconnections_prevented,
                "protected_passengers": 269,
                "residual_risk": (
                    "If SGN capacity falls below "
                    f"{weather_signals['min_arrival_capacity_per_hour']} movements/hour earlier than forecast, "
                    "the protected flight may still receive CTOT delay."
                ),
            },
            "alternatives_considered": self._alternatives(data, signals),
            "agent_findings": [finding.to_dict() for finding in findings],
            "explainability_payload": self._explain(
                data,
                signals,
                actions,
                confidence,
                savings,
                misconnections_prevented,
            ),
        }
        return decision

    def _base_actions(
        self,
        protect_flight: str,
        recommended_tail: str,
        original_tail: str,
        delay_candidate: str,
        reserve_crew: str,
        weather_signals: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "action_id": "ACT-001",
                "type": "aircraft_swap",
                "priority": 1,
                "flight": protect_flight,
                "from_tail": original_tail,
                "to_tail": recommended_tail,
                "reason": (
                    f"{protect_flight} is the highest-cost flight to protect and {recommended_tail} "
                    "has enough seats with fewer immediate maintenance constraints."
                ),
                "operational_effect": (
                    f"Gets {protect_flight} away before the high-risk weather window begins at "
                    f"{weather_signals['first_high_risk_time']}."
                ),
                "risks": [
                    "Requires inbound aircraft to block on time.",
                    "Requires fast-turn handling at Gate 18.",
                ],
            },
            {
                "action_id": "ACT-002",
                "type": "controlled_delay",
                "priority": 2,
                "flight": delay_candidate,
                "delay_minutes": 42,
                "new_departure_local": "2026-07-12T08:17:00+07:00",
                "reason": (
                    f"{delay_candidate} has lower connection exposure than {protect_flight} "
                    "and its destination can absorb recovery delay."
                ),
                "operational_effect": "Creates enough room to fast-turn the protected flight first.",
            },
            {
                "action_id": "ACT-003",
                "type": "gate_change",
                "priority": 3,
                "flight": protect_flight,
                "from_resource": "Gate 14",
                "to_resource": "Gate 18",
                "reason": "Gate 18 has the best modeled turnaround score and avoids the remote-stand taxiway penalty.",
                "estimated_turnaround_minutes_saved": 11,
            },
            {
                "action_id": "ACT-004",
                "type": "crew_reallocation",
                "priority": 4,
                "flight": delay_candidate,
                "from_crew": "C-SGN-052",
                "to_crew": reserve_crew,
                "reason": "Reserve crew is already at SGN and avoids stacking risk on the constrained checked-in crew.",
                "condition": "Execute if VJ237 cannot board by 07:45 or the captain documentation stop exceeds 20 minutes.",
            },
            {
                "action_id": "ACT-005",
                "type": "maintenance_protection",
                "priority": 5,
                "tail": "VN-A678",
                "reason": "Weather-radar MEL and defect-rectification due time make storm-window dispatch unattractive.",
                "operational_effect": "Hold VJ310 or substitute after convective risk drops.",
            },
        ]

    def _scenario_actions(
        self,
        data: dict[str, Any],
        scenario_key: str,
        protect_flight: str,
        recommended_tail: str,
        original_tail: str,
        delay_candidate: str,
        reserve_crew: str,
        weather_signals: dict[str, Any],
    ) -> list[dict[str, Any]]:
        base = self._base_actions(
            protect_flight,
            recommended_tail,
            original_tail,
            delay_candidate,
            reserve_crew,
            weather_signals,
        )
        if scenario_key == "sgn_lightning":
            return [
                {
                    "action_id": "ACT-001",
                    "type": "ground_hold",
                    "priority": 1,
                    "flight": "VJ310",
                    "hold_minutes": 35,
                    "reason": "VJ310 is at remote stand R32, where lightning ramp-stop risk is highest.",
                    "operational_effect": "Avoids boarding passengers onto an aircraft that cannot be safely serviced during lightning alerts.",
                },
                {
                    "action_id": "ACT-002",
                    "type": "gate_change",
                    "priority": 2,
                    "flight": "VJ152",
                    "from_resource": "Gate 14",
                    "to_resource": "Gate 18",
                    "reason": "Gate 18 keeps the protected trunk flight on a contact gate and out of remote-stand handling exposure.",
                    "estimated_turnaround_minutes_saved": 11,
                },
                {
                    "action_id": "ACT-003",
                    "type": "controlled_delay",
                    "priority": 3,
                    "flight": delay_candidate,
                    "delay_minutes": 28,
                    "new_departure_local": "2026-07-12T08:03:00+07:00",
                    "reason": "A shorter controlled delay lets ramp handling resume after the lightning warning without pushing VJ152 into the worst capacity window.",
                    "operational_effect": "Keeps DAD recovery cost lower than exposing VJ152's HAN connections.",
                },
                *base[3:],
            ]
        if scenario_key == "sgn_maintenance":
            return [
                base[0],
                {
                    "action_id": "ACT-002",
                    "type": "maintenance_protection",
                    "priority": 2,
                    "tail": "VN-A152",
                    "reason": "VN-A152 has an accelerated SGN maintenance return requirement and should not be sent into a recovery-sensitive rotation.",
                    "operational_effect": "Protects the A-check and hydraulic service package from slipping into the afternoon bank.",
                },
                {
                    "action_id": "ACT-003",
                    "type": "ground_hold",
                    "priority": 3,
                    "flight": "VJ310",
                    "hold_minutes": 45,
                    "reason": "VN-A678 has weather-radar and pack-control maintenance risk; dispatch after engineering release is safer.",
                    "operational_effect": "Prevents a low-priority leisure flight from creating an aircraft-on-ground cascade.",
                },
                base[3],
                base[4],
            ]
        if scenario_key == "sgn_network_stress":
            return [
                {
                    "action_id": "ACT-001",
                    "type": "capacity_rebalance",
                    "priority": 1,
                    "flight_bank": "SGN-HAN trunk bank",
                    "reason": (
                        f"{len(data['scheduled_flights'])} monitored flights are competing for reduced SGN capacity; "
                        "the trunk bank has the highest network value."
                    ),
                    "operational_effect": "Protects the first departure wave and prevents delay propagation across the larger monitored network.",
                },
                base[0] | {"priority": 2, "action_id": "ACT-002"},
                {
                    "action_id": "ACT-003",
                    "type": "crew_reallocation",
                    "priority": 3,
                    "flight": delay_candidate,
                    "from_crew": "C-SGN-052",
                    "to_crew": reserve_crew,
                    "reason": "Reserve crew absorbs the controlled delay while checked-in crew protects the trunk-bank departure.",
                    "condition": "Execute if VJ237 slips behind the protected HAN departure queue.",
                },
                base[2] | {"priority": 4, "action_id": "ACT-004"},
                base[4],
            ]
        return base

    def _headline(self, actions: list[dict[str, Any]]) -> str:
        return "; ".join(self._action_title(action) for action in actions[:3]) + "."

    def _action_title(self, action: dict[str, Any]) -> str:
        if action["type"] == "aircraft_swap":
            return f"Swap {action['flight']} onto {action['to_tail']}"
        if action["type"] == "controlled_delay":
            return f"Delay {action['flight']} by {action['delay_minutes']} minutes"
        if action["type"] == "gate_change":
            return f"Move {action['flight']} to {action['to_resource']}"
        if action["type"] == "crew_reallocation":
            return f"Reassign {action['flight']} to {action['to_crew']}"
        if action["type"] == "maintenance_protection":
            return f"Protect {action['tail']} for maintenance"
        if action["type"] == "ground_hold":
            return f"Hold {action['flight']} for {action['hold_minutes']} minutes"
        if action["type"] == "capacity_rebalance":
            return f"Prioritize {action['flight_bank']}"
        return action["type"].replace("_", " ").title()

    def _confidence(self, findings: list[AgentFinding]) -> float:
        average_risk = sum(finding.risk_score for finding in findings) / len(findings)
        agreement_bonus = 0.1
        confidence = 0.67 + (average_risk * 0.25) + agreement_bonus
        return round(min(0.96, confidence), 2)

    def _estimate_savings(self, cost_signals: dict[str, Any], protect_flight: str) -> int:
        ranked = cost_signals["ranked_flights"]
        protected = next(item for item in ranked if item["flight"] == protect_flight)
        delay_candidate = next(item for item in ranked if item["flight"] == "VJ237")
        avoided_connection_cost = protected["connection_cost_usd"]
        delay_shift_value = max(0, protected["score"] - delay_candidate["score"])
        return round((avoided_connection_cost + delay_shift_value + 1100) / 100) * 100

    def _estimate_misconnections_prevented(self, cost_signals: dict[str, Any], protect_flight: str) -> int:
        protected = next(item for item in cost_signals["ranked_flights"] if item["flight"] == protect_flight)
        return max(0, protected["connection_passengers"] - 3)

    def _alternatives(self, data: dict[str, Any], signals: dict[str, Any]) -> list[dict[str, Any]]:
        aircraft_scores = signals["aircraft_agent"]["candidate_scores"]
        a678 = next(item for item in aircraft_scores if item["tail"] == "VN-A678")
        return [
            {
                "option": "Do nothing",
                "score": 0.41,
                "rejected_because": "The highest-value flight would slip toward the ATFM/weather window.",
            },
            {
                "option": "Use VN-A678 for VJ152",
                "score": a678["score"],
                "rejected_because": "It has insufficient seats for VJ152 and carries a weather-radar MEL.",
            },
            {
                "option": "Delay VJ152 instead of VJ237",
                "score": 0.48,
                "rejected_because": "VJ152 has materially higher connection and passenger-protection exposure.",
            },
            {
                "option": "Keep all aircraft assignments unchanged",
                "score": 0.55,
                "rejected_because": "This preserves schedule order but ignores maintenance and gate-turn advantages.",
            },
        ]

    def _explain(
        self,
        data: dict[str, Any],
        signals: dict[str, Any],
        actions: list[dict[str, Any]],
        confidence: float,
        savings: int,
        misconnections_prevented: int,
    ) -> dict[str, Any]:
        protect_flight = signals["cost_impact_agent"]["protect_flight"]
        recommended_tail = signals["aircraft_agent"]["recommended_tail_for_vj152"]
        delay_candidate = signals["cost_impact_agent"]["delay_candidate"]
        action_titles = [self._action_title(action) for action in actions[:3]]
        controlled_delay = next((action for action in actions if action["type"] == "controlled_delay"), None)
        return {
            "user_question": "Why?",
            "short_answer": (
                f"Because the highest-value mitigation path is: {action_titles[0]}; "
                f"{action_titles[1]}; and {action_titles[2]}. SGN weather worsens after "
                f"{signals['weather_agent']['first_high_risk_time']}, while the aircraft, crew, "
                "maintenance and cost agents agree this sequence reduces the largest cascade risk."
            ),
            "decision_chain": [
                {
                    "step": 1,
                    "finding": "Weather risk rises before the main departure bank clears.",
                    "data_used": ["TAF-style forecast", "hourly capacity model", "SGN NOTAMs"],
                    "impact": (
                        "The supervisor prioritizes flights that can depart before "
                        f"{signals['weather_agent']['first_high_risk_time']}."
                    ),
                },
                {
                    "step": 2,
                    "finding": f"{protect_flight} is the flight to protect.",
                    "data_used": ["passenger connections", "priority score", "load factor"],
                    "impact": "It has the highest modeled disruption cost in the morning wave.",
                },
                {
                    "step": 3,
                    "finding": f"{recommended_tail} is the best aircraft swap candidate.",
                    "data_used": ["seat capacity", "aircraft position", "maintenance constraints", "gate position"],
                    "impact": "The swap preserves capacity and reduces maintenance recovery risk.",
                },
                {
                    "step": 4,
                    "finding": "Gate 18 reduces turn risk.",
                    "data_used": ["gate scores", "taxiway closure", "boarding proximity"],
                    "impact": "The 11-minute turn saving keeps the protected flight ahead of flow control.",
                },
                {
                    "step": 5,
                    "finding": f"{delay_candidate} is the least damaging controlled delay.",
                    "data_used": ["connection exposure", "crew reserve availability", "destination recovery buffer"],
                    "impact": "The system shifts disruption to the lower-cost sector instead of letting it cascade.",
                },
            ],
            "numbers_shown_to_ops_manager": {
                "confidence": f"{confidence:.0%}",
                "estimated_savings": f"USD {savings:,}",
                "turnaround_saving": "11 minutes",
                "controlled_delay": (
                    f"{controlled_delay['delay_minutes']} minutes" if controlled_delay else "Not primary action"
                ),
                "misconnections_prevented": misconnections_prevented,
            },
        }
