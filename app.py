from __future__ import annotations

import copy
import html
import json
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from flightops.llm import LLMExplanationAgent
from flightops.supervisor import SupervisorAgent


DATA_PATH = Path("demo-data/flightops-ai-typhoon-sgn-2026-07-12.json")
LOGO_PATH = Path("assets/vietjet-air-logo.svg")
SCENARIO_OPTIONS = {
    "sgn_typhoon": "Typhoon approaching SGN",
    "sgn_lightning": "Lightning ramp stop at SGN",
    "sgn_maintenance": "Maintenance cascade at SGN",
    "sgn_network_stress": "High-volume network stress",
}
AGENT_LABELS = {
    "weather_agent": "Weather",
    "aircraft_agent": "Aircraft",
    "crew_agent": "Crew",
    "maintenance_agent": "Maintenance",
    "cost_impact_agent": "Cost",
}
AGENT_BADGES = {
    "weather_agent": "WX",
    "aircraft_agent": "AC",
    "crew_agent": "CR",
    "maintenance_agent": "MX",
    "cost_impact_agent": "$",
}
AGENT_ACCENTS = {
    "weather_agent": "red",
    "aircraft_agent": "blue",
    "crew_agent": "purple",
    "maintenance_agent": "amber",
    "cost_impact_agent": "green",
    "supervisor_agent": "blue",
}
AGENT_ICON_BADGES = {
    "weather_agent": "WX",
    "aircraft_agent": "AC",
    "crew_agent": "CR",
    "maintenance_agent": "MX",
    "cost_impact_agent": "$",
    "supervisor_agent": "SV",
}
AGENT_SHORT_SUMMARIES = {
    "weather_agent": "SGN capacity drops after 08:00; peak disruption at 10:00.",
    "aircraft_agent": "VN-A237 is the best aircraft swap for VJ152.",
    "crew_agent": "Reserve crew can absorb VJ237 after the controlled delay.",
    "maintenance_agent": "Hold VN-A678 due weather-radar MEL and rectification slot.",
    "cost_impact_agent": "VJ152 has the highest disruption and connection cost.",
}
TIMELINE_DEMO_SECONDS = 60
TIMELINE_SIMULATED_HOURS = 12
TIMELINE_START_LOCAL = "2026-07-12T05:40:00+07:00"
TIMELINE_MILESTONES = [
    {
        "second": 0,
        "scenario": "sgn_typhoon",
        "event": "Weather Agent opens typhoon disruption watch for SGN morning bank.",
        "accepted": "Baseline monitoring started",
        "cumulative_savings": 0,
        "flights_recovered": 0,
    },
    {
        "second": 8,
        "scenario": "sgn_typhoon",
        "event": "Supervisor package accepted: protect VJ152, delay VJ237, move VJ152 to Gate 18.",
        "accepted": "VJ152 swap package",
        "cumulative_savings": 18200,
        "flights_recovered": 3,
    },
    {
        "second": 16,
        "scenario": "sgn_lightning",
        "event": "Lightning ramp-stop warning received; remote-stand handling paused in bursts.",
        "accepted": "VJ310 ground hold",
        "cumulative_savings": 32700,
        "flights_recovered": 7,
    },
    {
        "second": 25,
        "scenario": "sgn_maintenance",
        "event": "Maintenance Agent flags VN-A152 return limit and VN-A678 storm-window dispatch risk.",
        "accepted": "Maintenance protection package",
        "cumulative_savings": 54800,
        "flights_recovered": 12,
    },
    {
        "second": 36,
        "scenario": "sgn_network_stress",
        "event": "High-volume bank detected: 43 flights competing for reduced SGN capacity.",
        "accepted": "Network metering package",
        "cumulative_savings": 81900,
        "flights_recovered": 24,
    },
    {
        "second": 48,
        "scenario": "sgn_network_stress",
        "event": "Passenger protection actions accepted for 13 connection groups across HAN, DAD and CXR.",
        "accepted": "Passenger protection package",
        "cumulative_savings": 111600,
        "flights_recovered": 34,
    },
    {
        "second": 60,
        "scenario": "sgn_typhoon",
        "event": "12-hour run complete: afternoon recovery buffers absorbed residual disruption.",
        "accepted": "Recovery complete",
        "cumulative_savings": 126400,
        "flights_recovered": 41,
    },
]


@st.cache_data
def load_demo_data() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def load_scenario(scenario_key: str) -> dict[str, Any]:
    data = copy.deepcopy(load_demo_data())
    if scenario_key == "sgn_lightning":
        apply_lightning_scenario(data)
    elif scenario_key == "sgn_maintenance":
        apply_maintenance_scenario(data)
    elif scenario_key == "sgn_network_stress":
        apply_network_stress_scenario(data)
    else:
        data["scenario"]["status_label"] = "Typhoon risk near SGN"
        data["scenario"]["summary"] = "Typhoon disruption at Ho Chi Minh City"
    data["scenario"]["selected_key"] = scenario_key
    return data


def apply_lightning_scenario(data: dict[str, Any]) -> None:
    data["scenario"]["id"] = "flightops-ai-sgn-lightning-ramp-stop-2026-07-12"
    data["scenario"]["name"] = "Lightning ramp-stop at SGN"
    data["scenario"]["status_label"] = "Lightning ramp stop near SGN"
    data["scenario"]["summary"] = "Lightning warning blocks exposed ground handling during the morning bank."
    data["weather_feed"]["storm"]["name"] = "Convective Cell Line Bravo"
    data["weather_feed"]["storm"]["classification"] = "severe convective line"
    for item in data["weather_feed"]["airport_forecasts"][0]["hourly_risk"]:
        if item["local_time"] in {"07:00", "08:00"}:
            item["delay_risk_score"] = min(0.94, item["delay_risk_score"] + 0.18)
            item["main_driver"] = "lightning within 5 NM and ramp handling suspension risk"
        if item["local_time"] == "09:00":
            item["departure_capacity_per_hour"] = 9
            item["arrival_capacity_per_hour"] = 9
    data["notams"][1]["text"] = "LIGHTNING WARNING PROCEDURE ACTIVE. RAMP HANDLING SUSPENSION EXPECTED IN 15-25 MIN BURSTS."
    data["notams"][1]["ops_impact"] = "Fast-turn flights at remote stands likely lose 15-25 minutes."


def apply_maintenance_scenario(data: dict[str, Any]) -> None:
    data["scenario"]["id"] = "flightops-ai-sgn-maintenance-cascade-2026-07-12"
    data["scenario"]["name"] = "Maintenance cascade at SGN"
    data["scenario"]["status_label"] = "Maintenance cascade at SGN"
    data["scenario"]["summary"] = "Weather disruption combines with two narrow-body maintenance constraints."
    data["weather_feed"]["storm"]["name"] = "SGN Heat And Convective Recovery Window"
    data["weather_feed"]["storm"]["classification"] = "maintenance-sensitive convective recovery"
    for item in data["weather_feed"]["airport_forecasts"][0]["hourly_risk"]:
        if item["local_time"] in {"08:00", "09:00", "10:00"}:
            item["main_driver"] = "wet ramp, peak heat and engineering release buffers"
        if item["local_time"] == "10:00":
            item["delay_risk_score"] = max(item["delay_risk_score"], 0.88)
    data["notams"][0]["text"] = "DUE WX AND MAINTENANCE RECOVERY CONSTRAINTS, EXPECT CTOT SENSITIVITY FOR LATE ENGINEERING RELEASES."
    data["notams"][0]["ops_impact"] = "Narrow-body rotations with maintenance return limits should avoid long ground holds."
    data["fleet"][0]["next_maintenance"]["due_local"] = "2026-07-12T13:20:00+07:00"
    data["fleet"][0]["next_maintenance"]["due_in_flight_hours"] = 4.3
    data["maintenance_logs"].append(
        {
            "tail": "VN-A152",
            "logged_at_local": "2026-07-12T05:28:00+07:00",
            "severity": "planning_constraint",
            "text": "Hydraulic service inspection added to A-check package; aircraft must return SGN no later than 13:05.",
        }
    )
    data["fleet"][3]["mel_items"].append(
        {
            "code": "21-52-03",
            "description": "Pack 2 temperature control intermittent",
            "operational_restriction": "Avoid high-delay ground holds during peak heat unless engineering accepts.",
            "expires_local": "2026-07-13T20:00:00+07:00",
        }
    )
    data["scheduled_flights"][3]["status_at_snapshot"] = "maintenance_hold_pending_engineering_release"


def apply_network_stress_scenario(data: dict[str, Any]) -> None:
    data["scenario"]["id"] = "flightops-ai-sgn-network-stress-2026-07-12"
    data["scenario"]["name"] = "High-volume SGN network stress"
    data["scenario"]["status_label"] = "High-volume network stress"
    data["scenario"]["summary"] = "Large morning bank with many monitored flights, crews, aircraft and passenger flows."
    data["weather_feed"]["storm"]["name"] = "SGN Capacity Compression Window"
    data["weather_feed"]["storm"]["classification"] = "network-wide flow restriction"
    data["notams"][0]["text"] = "NETWORK GDP ACTIVE. SGN DOMESTIC DEPARTURE METERING REQUIRED DURING MORNING BANK."
    data["notams"][0]["ops_impact"] = "Departure release rate capped; trunk-bank flights should be prioritized."
    data["notams"][2]["text"] = "GATE AND TAXIWAY COMPRESSION EXPECTED DUE HIGH-VOLUME BANK AND TWY W4 CLOSURE."
    data["notams"][2]["ops_impact"] = "Gate conflicts and taxi-out queues likely unless rotations are metered."
    routes = ["SGN-HAN", "SGN-DAD", "SGN-CXR", "SGN-PQC", "SGN-HUI", "SGN-HPH", "SGN-VCA", "SGN-BMV"]
    tails = []
    for index in range(18):
        tail = f"VN-B{700 + index}"
        tails.append(tail)
        data["fleet"].append(
            {
                "tail": tail,
                "type": "A321-271N" if index % 3 else "A320-214",
                "seat_capacity": 240 if index % 3 else 180,
                "base": "SGN",
                "current_airport": "SGN" if index % 4 else "HAN",
                "current_state": "monitored_rotation",
                "available_from_local": f"2026-07-12T{6 + index % 4:02d}:{(index * 7) % 60:02d}:00+07:00",
                "utilization_last_24h_hours": round(6.5 + (index % 8) * 0.7, 1),
                "mel_items": [],
                "next_maintenance": {
                    "type": "line check",
                    "due_local": "2026-07-12T23:30:00+07:00",
                    "airport_required": "SGN",
                },
            }
        )
    for index in range(16):
        crew_id = f"C-SGN-X{index + 1:02d}"
        data["crew_rosters"].append(
            {
                "crew_id": crew_id,
                "role_set": "A320/A321 mixed",
                "qualified_types": ["A320", "A321"],
                "report_local": f"2026-07-12T{5 + index % 3:02d}:{(index * 11) % 60:02d}:00+07:00",
                "duty_end_limit_local": f"2026-07-12T{17 + index % 4:02d}:{(index * 11) % 60:02d}:00+07:00",
                "assigned_flights": [],
                "status": "monitored",
                "constraints": [],
            }
        )
    for index in range(36):
        route = routes[index % len(routes)]
        tail = tails[index % len(tails)]
        hour = 6 + (index // 7)
        minute = (index * 9) % 60
        passengers = 108 + (index * 13) % 68
        flight_number = f"VJ{900 + index}"
        data["scheduled_flights"].append(
            {
                "flight": flight_number,
                "route": route,
                "scheduled_departure_local": f"2026-07-12T{hour:02d}:{minute:02d}:00+07:00",
                "scheduled_arrival_local": f"2026-07-12T{hour + 1:02d}:{(minute + 20) % 60:02d}:00+07:00",
                "aircraft_tail": tail,
                "planned_gate": str(10 + (index % 18)),
                "passengers_booked": passengers,
                "checked_bags": round(passengers * 0.58),
                "crew_id": f"C-SGN-X{index % 16 + 1:02d}",
                "priority": "medium" if index % 5 else "low",
                "business_context": "Additional monitored flight in high-volume network stress scenario.",
                "status_at_snapshot": "monitored_for_downstream_delay",
            }
        )
        if index % 4 == 0:
            data["passenger_connections"].append(
                {
                    "id": f"CONN-STRESS-{index:02d}",
                    "inbound_flight": flight_number,
                    "connecting_airport": route.split("-")[1],
                    "outbound_flight": f"VJ{1200 + index}",
                    "outbound_route": f"{route.split('-')[1]}-SGN",
                    "passenger_count": 4 + index % 6,
                    "scheduled_connection_minutes": 115,
                    "protected_if_arrival_delay_under_minutes": 60,
                    "misconnect_cost_usd_per_passenger": 80,
                }
            )
    for item in data["weather_feed"]["airport_forecasts"][0]["hourly_risk"]:
        item["arrival_capacity_per_hour"] = max(6, item["arrival_capacity_per_hour"] - 2)
        item["departure_capacity_per_hour"] = max(8, item["departure_capacity_per_hour"] - 3)
        item["main_driver"] = "reduced SGN capacity and high-volume departure bank"


@st.cache_data
def run_agents(data: dict[str, Any]) -> dict[str, Any]:
    return SupervisorAgent().decide(data)


@st.cache_data
def run_llm_briefing(data: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return LLMExplanationAgent().run(data, decision).to_dict()


@st.cache_data
def load_logo_data_uri() -> str:
    logo_bytes = LOGO_PATH.read_bytes()
    encoded = base64.b64encode(logo_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def flight_table(data: dict[str, Any]) -> pd.DataFrame:
    impact_by_flight = {
        "VJ152": "Protect",
        "VJ237": "Controlled delay",
        "VJ205": "Inbound feed",
        "VJ310": "Hold for MX/weather",
        "VJ801": "Protect BKK slot",
    }
    risk_by_flight = {
        "VJ152": "High",
        "VJ237": "Medium",
        "VJ205": "Medium",
        "VJ310": "High",
        "VJ801": "High",
    }
    rows = []
    for flight in data["scheduled_flights"]:
        if flight["flight"] not in impact_by_flight:
            continue
        rows.append(
            {
                "Flight": flight["flight"],
                "Route": flight["route"],
                "STD": flight["scheduled_departure_local"][11:16],
                "Aircraft": flight["aircraft_tail"],
                "Gate/Stand": flight.get("planned_gate") or flight.get("planned_stand"),
                "Passengers": flight["passengers_booked"],
                "Priority": flight["priority"],
                "Risk": risk_by_flight[flight["flight"]],
                "Ops impact": impact_by_flight[flight["flight"]],
            }
        )
    return pd.DataFrame(rows)


def style_flight_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def color_risk(value: str) -> str:
        if value == "High":
            return "background-color: #fff1f1; color: #9f1218; font-weight: 800;"
        if value == "Medium":
            return "background-color: #fff7df; color: #765000; font-weight: 800;"
        return "background-color: #edfdf5; color: #126044; font-weight: 800;"

    def color_priority(value: str) -> str:
        if value == "high":
            return "color: #9f1218; font-weight: 800;"
        if value == "medium":
            return "color: #765000; font-weight: 800;"
        return "color: #126044; font-weight: 800;"

    return df.style.map(color_risk, subset=["Risk"]).map(color_priority, subset=["Priority"])


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f6f7f9;
            --panel: #ffffff;
            --panel-border: #d9dee7;
            --text: #18202b;
            --muted: #687386;
            --red: #d71920;
            --yellow: #ffc400;
            --green: #14845b;
            --amber: #b76800;
            --slate: #334155;
        }
        .stApp {
            background: var(--bg);
            color: var(--text);
        }
        header[data-testid="stHeader"],
        #MainMenu,
        footer {
            display: none;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.75rem;
        }
        .block-container {
            padding-top: 0.75rem;
            padding-bottom: 1.25rem;
            max-width: 1480px;
        }
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.9rem 1rem;
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            background: var(--panel);
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
        }
        .brand-mark {
            width: 145px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            border: 1px solid #f0c8c8;
            background: #ffffff;
            padding: 0.35rem 0.45rem;
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.65);
        }
        .brand-mark img {
            display: block;
            max-width: 100%;
            max-height: 34px;
            object-fit: contain;
        }
        .brand h1 {
            font-size: 1.35rem;
            line-height: 1.1;
            margin: 0;
            letter-spacing: 0;
        }
        .brand p, .status-sub {
            margin: 0.15rem 0 0;
            color: var(--muted);
            font-size: 0.86rem;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.45rem 0.65rem;
            border-radius: 999px;
            border: 1px solid #f4c6c6;
            background: #fff2f2;
            color: #9f1218;
            font-size: 0.86rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .card {
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            background: var(--panel);
            padding: 0.95rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
            min-width: 0;
        }
        .card h2, .card h3 {
            margin: 0 0 0.62rem;
            letter-spacing: 0;
        }
        .card h2 {
            font-size: 1.05rem;
        }
        .card h3 {
            font-size: 0.95rem;
        }
        .muted {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.4;
            overflow-wrap: break-word;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.55rem;
        }
        .metric-tile {
            border: 1px solid #e2e7ef;
            border-radius: 8px;
            background: #fbfcfe;
            padding: 0.72rem;
            min-height: 76px;
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        .metric-value {
            color: var(--text);
            font-size: 1.35rem;
            font-weight: 800;
            margin-top: 0.16rem;
            letter-spacing: 0;
        }
        .recommendation {
            border-color: #bfe7d5;
            border-left: 5px solid var(--green);
            background: linear-gradient(180deg, #ffffff 0%, #f5fff9 100%);
        }
        .rec-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.15rem;
        }
        .rec-head h2 {
            margin: 0;
        }
        .recommended-label {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: #eafaf2;
            color: #126044;
            font-size: 0.74rem;
            font-weight: 900;
            white-space: nowrap;
        }
        .action-row {
            display: grid;
            grid-template-columns: 2rem 1fr;
            gap: 0.68rem;
            padding: 0.68rem 0;
            border-top: 1px solid #dceee5;
            min-width: 0;
        }
        .action-row > div {
            min-width: 0;
        }
        .action-row:first-of-type {
            border-top: 0;
            padding-top: 0;
        }
        .step-dot {
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: var(--green);
            color: #fff;
            font-size: 0.78rem;
            font-weight: 800;
        }
        .step-dot.delay {
            background: #b76800;
        }
        .step-dot.gate {
            background: #2663b8;
        }
        .action-title {
            font-size: 0.98rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: 0;
            overflow-wrap: break-word;
        }
        .action-reason {
            margin: 0.18rem 0 0;
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.34;
            overflow-wrap: break-word;
        }
        .action-subhead {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.6rem;
            margin-top: 0.72rem;
            padding-top: 0.72rem;
            border-top: 1px solid #dceee5;
        }
        .action-subhead h3 {
            margin: 0;
            font-size: 0.86rem;
        }
        .action-count {
            color: #126044;
            font-size: 0.72rem;
            font-weight: 900;
            white-space: nowrap;
        }
        .secondary-actions {
            display: grid;
            gap: 0.42rem;
            margin-top: 0.48rem;
        }
        .secondary-action {
            display: grid;
            grid-template-columns: 1.5rem 1fr;
            gap: 0.52rem;
            align-items: start;
            border: 1px solid #dbe8e2;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.74);
            padding: 0.5rem;
        }
        .secondary-action .step-dot {
            width: 1.25rem;
            height: 1.25rem;
            font-size: 0.68rem;
        }
        .secondary-title {
            margin: 0;
            color: var(--text);
            font-size: 0.8rem;
            font-weight: 900;
        }
        .secondary-reason {
            margin: 0.08rem 0 0;
            color: var(--muted);
            font-size: 0.74rem;
            line-height: 1.25;
        }
        .before-after {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.5rem;
            margin-top: 0.62rem;
            padding-top: 0.62rem;
            border-top: 1px solid #dceee5;
        }
        .impact-cell {
            border: 1px solid #dbe8e2;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.78);
            padding: 0.52rem;
        }
        .impact-label {
            color: var(--muted);
            font-size: 0.68rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.02em;
            margin-bottom: 0.2rem;
        }
        .impact-change {
            display: flex;
            align-items: center;
            gap: 0.3rem;
            font-size: 0.94rem;
            font-weight: 900;
        }
        .before {
            color: #9f1218;
        }
        .after {
            color: #126044;
        }
        .agent-card {
            border: 1px solid #dfe5ee;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.72rem;
            min-height: 118px;
            border-top: 4px solid #dfe5ee;
        }
        .agent-card.red {
            border-top-color: #d71920;
            background: linear-gradient(180deg, #ffffff 0%, #fff8f8 100%);
        }
        .agent-card.blue {
            border-top-color: #2663b8;
            background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);
        }
        .agent-card.purple {
            border-top-color: #7c55c7;
            background: linear-gradient(180deg, #ffffff 0%, #faf7ff 100%);
        }
        .agent-card.amber {
            border-top-color: #b76800;
            background: linear-gradient(180deg, #ffffff 0%, #fffaf0 100%);
        }
        .agent-card.green {
            border-top-color: #14845b;
            background: linear-gradient(180deg, #ffffff 0%, #f5fff9 100%);
        }
        .agent-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.34rem;
        }
        .agent-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 800;
        }
        .badge {
            display: grid;
            place-items: center;
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 6px;
            background: #eef2f7;
            color: var(--slate);
            font-size: 0.72rem;
            font-weight: 900;
        }
        .icon-badge {
            display: grid;
            place-items: center;
            width: 1.75rem;
            height: 1.75rem;
            border-radius: 7px;
            background: #eef2f7;
            color: var(--slate);
            font-size: 0.68rem;
            font-weight: 900;
            line-height: 1;
            letter-spacing: 0;
            flex: 0 0 auto;
        }
        .icon-badge.red {
            background: #fff1f1;
            color: #9f1218;
        }
        .icon-badge.blue {
            background: #edf5ff;
            color: #235aa6;
        }
        .icon-badge.purple {
            background: #f4efff;
            color: #6842a6;
        }
        .icon-badge.amber {
            background: #fff7df;
            color: #765000;
        }
        .icon-badge.green {
            background: #eafaf2;
            color: #126044;
        }
        .risk {
            color: var(--amber);
            font-size: 0.78rem;
            font-weight: 800;
        }
        .bar {
            height: 7px;
            background: #e8edf4;
            border-radius: 999px;
            overflow: hidden;
            margin: 0.36rem 0 0.45rem;
        }
        .bar span {
            display: block;
            height: 100%;
            background: linear-gradient(90deg, #ffc400 0%, #d71920 100%);
        }
        .agent-card.blue .bar span {
            background: linear-gradient(90deg, #6bb7ff 0%, #2663b8 100%);
        }
        .agent-card.purple .bar span {
            background: linear-gradient(90deg, #c9b6ff 0%, #7c55c7 100%);
        }
        .agent-card.amber .bar span {
            background: linear-gradient(90deg, #ffd166 0%, #b76800 100%);
        }
        .agent-card.green .bar span {
            background: linear-gradient(90deg, #63d99c 0%, #14845b 100%);
        }
        .why-step {
            display: grid;
            grid-template-columns: 1.8rem 1fr;
            gap: 0.62rem;
            padding: 0.58rem 0;
            border-top: 1px solid #e3e8f0;
        }
        .why-step:first-of-type {
            border-top: 0;
            padding-top: 0;
        }
        .why-num {
            width: 1.55rem;
            height: 1.55rem;
            border-radius: 6px;
            display: grid;
            place-items: center;
            background: #fff4cc;
            color: #765000;
            font-size: 0.78rem;
            font-weight: 900;
        }
        .why-num.red {
            background: #fff1f1;
            color: #9f1218;
        }
        .why-num.blue {
            background: #edf5ff;
            color: #235aa6;
        }
        .why-num.purple {
            background: #f4efff;
            color: #6842a6;
        }
        .why-num.green {
            background: #eafaf2;
            color: #126044;
        }
        .why-num.amber {
            background: #fff7df;
            color: #765000;
        }
        .why-title {
            font-weight: 800;
            margin: 0;
            font-size: 0.86rem;
        }
        .why-impact {
            margin: 0.16rem 0 0;
            color: var(--muted);
            font-size: 0.8rem;
            line-height: 1.32;
        }
        .weather-strip {
            display: flex;
            gap: 0.35rem;
            margin-top: 0.75rem;
        }
        .weather-hour {
            flex: 1;
            border-radius: 6px;
            padding: 0.44rem 0.3rem;
            text-align: center;
            background: #f1f5f9;
            color: #334155;
            font-size: 0.78rem;
            font-weight: 800;
        }
        .weather-hour.hot {
            background: #fff1f1;
            color: #af161c;
        }
        .weather-hour.warn {
            background: #fff7df;
            color: #835a00;
        }
        .flight-note {
            color: var(--muted);
            font-size: 0.8rem;
            margin-top: 0.5rem;
        }
        .weather-meta {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.5rem;
            margin-top: 0.65rem;
        }
        .weather-meta-item {
            border: 1px solid #e2e7ef;
            border-radius: 8px;
            background: #fbfcfe;
            padding: 0.52rem;
        }
        .weather-meta-label {
            color: var(--muted);
            font-size: 0.66rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        .weather-meta-value {
            color: var(--text);
            font-size: 0.8rem;
            font-weight: 900;
            margin-top: 0.08rem;
            line-height: 1.25;
        }
        .constraint-list {
            display: grid;
            gap: 0.38rem;
            margin-top: 0.62rem;
        }
        .constraint-item {
            border-left: 3px solid var(--amber);
            background: #fffaf0;
            border-radius: 6px;
            padding: 0.42rem 0.5rem;
        }
        .constraint-title {
            margin: 0;
            color: var(--text);
            font-size: 0.76rem;
            font-weight: 900;
        }
        .constraint-impact {
            margin: 0.08rem 0 0;
            color: var(--muted);
            font-size: 0.72rem;
            line-height: 1.25;
        }
        .section-title {
            border: 1px solid var(--panel-border);
            border-radius: 8px 8px 0 0;
            background: var(--panel);
            border-bottom: 0;
            padding: 0.85rem 1rem 0.25rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        .section-title h2 {
            margin: 0;
            font-size: 1.05rem;
            letter-spacing: 0;
        }
        .table-note {
            border: 1px solid var(--panel-border);
            border-top: 0;
            border-radius: 0 0 8px 8px;
            background: var(--panel);
            padding: 0.2rem 1rem 0.75rem;
            color: var(--muted);
            font-size: 0.8rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        .agents-title {
            margin-top: 0.75rem;
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            background: var(--panel);
            padding: 0.85rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        .agents-title h2 {
            margin: 0;
            font-size: 1.05rem;
        }
        .dashboard-shell {
            display: flex;
            flex-direction: column;
            gap: 0.85rem;
            min-width: 0;
            overflow-x: hidden;
        }
        .timeline-card {
            border: 1px solid #c8daf4;
            border-left: 5px solid var(--blue);
            border-radius: 8px;
            background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);
            padding: 0.9rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        .timeline-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.8rem;
            margin-bottom: 0.65rem;
        }
        .timeline-title {
            margin: 0;
            font-size: 1.02rem;
            font-weight: 900;
        }
        .timeline-sub {
            margin: 0.12rem 0 0;
            color: var(--muted);
            font-size: 0.78rem;
        }
        .timeline-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.3rem 0.58rem;
            border-radius: 999px;
            background: #edf5ff;
            color: #235aa6;
            font-size: 0.74rem;
            font-weight: 900;
            white-space: nowrap;
        }
        .timeline-progress {
            height: 0.55rem;
            border-radius: 999px;
            background: #e7eef8;
            overflow: hidden;
        }
        .timeline-progress span {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #2663b8 0%, #14845b 100%);
        }
        .timeline-metrics {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.55rem;
            margin-top: 0.65rem;
        }
        .timeline-metric {
            border: 1px solid #d8e5f6;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.78);
            padding: 0.55rem;
        }
        .timeline-label {
            color: var(--muted);
            font-size: 0.66rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }
        .timeline-value {
            color: var(--text);
            font-size: 0.96rem;
            font-weight: 900;
            margin-top: 0.08rem;
        }
        .timeline-events {
            display: grid;
            gap: 0.36rem;
            margin-top: 0.65rem;
        }
        .timeline-event {
            display: grid;
            grid-template-columns: 3.1rem 1fr;
            gap: 0.52rem;
            align-items: start;
            border-top: 1px solid #d8e5f6;
            padding-top: 0.4rem;
            color: var(--muted);
            font-size: 0.76rem;
            line-height: 1.28;
        }
        .timeline-event:first-child {
            border-top: 0;
            padding-top: 0;
        }
        .timeline-event-time {
            color: var(--text);
            font-weight: 900;
            font-variant-numeric: tabular-nums;
        }
        .cockpit-grid {
            display: grid;
            grid-template-columns: minmax(260px, 0.84fr) minmax(440px, 1.38fr) minmax(310px, 1.04fr);
            gap: 0.85rem;
            align-items: start;
        }
        .stack {
            display: flex;
            flex-direction: column;
            gap: 0.85rem;
            min-width: 0;
        }
        .impact-stack {
            order: 1;
        }
        .decision-stack {
            order: 2;
        }
        .why-stack {
            order: 3;
        }
        .flight-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.84rem;
        }
        .flight-table th {
            color: var(--muted);
            font-size: 0.72rem;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 0.02em;
            padding: 0.55rem 0.45rem;
            border-bottom: 1px solid #e4e9f1;
            white-space: nowrap;
        }
        .flight-table td {
            padding: 0.63rem 0.45rem;
            border-bottom: 1px solid #edf1f5;
            vertical-align: top;
        }
        .flight-table tr:last-child td {
            border-bottom: 0;
        }
        .flight-id {
            font-weight: 900;
            color: var(--text);
        }
        .table-scroll {
            overflow-x: auto;
            max-width: 100%;
            -webkit-overflow-scrolling: touch;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.18rem 0.46rem;
            font-size: 0.72rem;
            font-weight: 900;
            white-space: nowrap;
        }
        .pill-high {
            background: #fff1f1;
            color: #9f1218;
        }
        .pill-medium {
            background: #fff7df;
            color: #765000;
        }
        .pill-low {
            background: #edfdf5;
            color: #126044;
        }
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.7rem;
        }
        .alternatives-list {
            display: grid;
            gap: 0.55rem;
            margin-top: 0.15rem;
        }
        .alternative {
            border-top: 1px solid #e4e9f1;
            padding-top: 0.55rem;
        }
        .alternative:first-child {
            border-top: 0;
            padding-top: 0;
        }
        .alternative-title {
            margin: 0;
            font-size: 0.86rem;
            font-weight: 900;
        }
        .alternative-reason {
            margin: 0.12rem 0 0;
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.35;
        }
        .trace-list {
            display: grid;
            gap: 0.52rem;
        }
        .trace-item {
            display: grid;
            grid-template-columns: 1.85rem 1fr;
            gap: 0.55rem;
            align-items: start;
            padding-top: 0.52rem;
            border-top: 1px solid #e4e9f1;
        }
        .trace-item:first-child {
            padding-top: 0;
            border-top: 0;
        }
        .trace-title {
            margin: 0;
            font-size: 0.84rem;
            font-weight: 900;
        }
        .trace-detail {
            margin: 0.08rem 0 0;
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.3;
        }
        .ai-briefing {
            border-left: 5px solid #7c55c7;
            background: linear-gradient(180deg, #ffffff 0%, #faf7ff 100%);
        }
        .ai-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.55rem;
        }
        .ai-head h2 {
            margin: 0;
        }
        .ai-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: #f4efff;
            color: #6842a6;
            font-size: 0.72rem;
            font-weight: 900;
            white-space: nowrap;
        }
        .ai-badge.off {
            background: #eef2f7;
            color: #475569;
        }
        .briefing-text {
            color: var(--text);
            font-size: 0.84rem;
            line-height: 1.42;
            white-space: pre-wrap;
        }
        .event-list {
            display: grid;
            gap: 0.55rem;
        }
        .event-item {
            display: grid;
            grid-template-columns: 3.05rem 1fr;
            gap: 0.6rem;
            align-items: start;
            padding-top: 0.56rem;
            border-top: 1px solid #e4e9f1;
        }
        .event-item:first-child {
            border-top: 0;
            padding-top: 0;
        }
        .event-time {
            color: var(--text);
            font-size: 0.78rem;
            font-weight: 900;
            font-variant-numeric: tabular-nums;
        }
        .event-head {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            color: var(--text);
            font-size: 0.8rem;
            font-weight: 900;
        }
        .event-head .icon-badge {
            width: 1.42rem;
            height: 1.42rem;
            border-radius: 6px;
            font-size: 0.56rem;
        }
        .event-text {
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.32;
            margin-top: 0.08rem;
        }
        .control-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.5rem;
            margin-top: 0.55rem;
            padding-top: 0.62rem;
            border-top: 1px solid #dceee5;
        }
        .control-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.36rem;
            min-height: 2.35rem;
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            background: #ffffff;
            color: var(--text);
            font-size: 0.82rem;
            font-weight: 900;
            font-family: inherit;
            white-space: nowrap;
        }
        .control-button.approve {
            border-color: #bfe7d5;
            background: #eafaf2;
            color: #126044;
        }
        .control-button.simulate {
            border-color: #c8daf4;
            background: #edf5ff;
            color: #235aa6;
        }
        .control-button.reject {
            border-color: #f4c6c6;
            background: #fff1f1;
            color: #9f1218;
        }
        .control-icon {
            display: grid;
            place-items: center;
            width: 1.05rem;
            height: 1.05rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.72);
            font-size: 0.76rem;
            line-height: 1;
        }
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
        }
        .comparison-table th {
            color: var(--muted);
            font-size: 0.7rem;
            text-align: left;
            text-transform: uppercase;
            letter-spacing: 0.02em;
            padding: 0.46rem 0.34rem;
            border-bottom: 1px solid #e4e9f1;
            white-space: nowrap;
        }
        .comparison-table td {
            padding: 0.56rem 0.34rem;
            border-bottom: 1px solid #edf1f5;
            vertical-align: top;
            font-weight: 700;
        }
        .comparison-table tr:last-child td {
            border-bottom: 0;
        }
        .comparison-table .recommended-row td {
            background: #f5fff9;
            color: #126044;
            font-weight: 900;
        }
        .comparison-table .recommended-row td:first-child {
            border-radius: 8px 0 0 8px;
        }
        .comparison-table .recommended-row td:last-child {
            border-radius: 0 8px 8px 0;
        }
        .ops-brief {
            border-left: 5px solid #2663b8;
            background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);
        }
        .consensus-item {
            display: grid;
            grid-template-columns: 1.85rem 1fr;
            gap: 0.55rem;
            align-items: start;
            padding-top: 0.52rem;
            border-top: 1px solid #e4e9f1;
        }
        .consensus-item:first-child {
            padding-top: 0;
            border-top: 0;
        }
        @media (max-width: 900px) {
            .cockpit-grid, .agent-grid {
                grid-template-columns: 1fr;
            }
            .decision-stack {
                order: 1;
            }
            .impact-stack {
                order: 2;
            }
            .why-stack {
                order: 3;
            }
            .block-container {
                padding-left: 0.7rem;
                padding-right: 0.7rem;
            }
            .topbar {
                align-items: flex-start;
                flex-direction: column;
            }
            .metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .timeline-head {
                align-items: flex-start;
                flex-direction: column;
            }
            .timeline-metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .metric-value {
                font-size: 1.2rem;
            }
            .before-after {
                grid-template-columns: 1fr;
            }
            .control-row {
                grid-template-columns: 1fr;
            }
            .flight-table {
                min-width: 640px;
            }
            .comparison-table {
                min-width: 430px;
            }
            .weather-meta {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(data: dict[str, Any]) -> None:
    snapshot = data["scenario"]["snapshot_time_local"]
    st.markdown(
        f"""
        <div class="topbar">
            <div class="brand">
                <div class="brand-mark">VJ</div>
                <div>
                    <h1>FlightOps AI</h1>
                    <p>Autonomous operations copilot for disruption management</p>
                </div>
            </div>
            <div>
                <div class="status-pill">Typhoon risk near SGN</div>
                <p class="status-sub">Snapshot {snapshot[11:16]} ICT | 6-hour planning horizon</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(decision: dict[str, Any]) -> None:
    outcome = decision["projected_outcome"]
    metrics = [
        ("Confidence", f"{decision['confidence']:.0%}"),
        ("Savings", f"US${outcome['total_estimated_savings_usd']:,}"),
        ("Delay avoided", f"{outcome['delay_minutes_avoided']} min"),
        ("Misconnections prevented", str(outcome["misconnections_prevented"])),
    ]
    html = ['<div class="card"><h2>Scenario Impact</h2><div class="metric-grid">']
    for label, value in metrics:
        html.append(
            f"""
            <div class="metric-tile">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
            </div>
            """
        )
    html.append("</div></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_weather_snapshot(data: dict[str, Any]) -> None:
    forecast = data["weather_feed"]["airport_forecasts"][0]["hourly_risk"]
    hour_html = []
    for item in forecast:
        css_class = "hot" if item["delay_risk_score"] >= 0.75 else "warn" if item["delay_risk_score"] >= 0.55 else ""
        hour_html.append(
            f'<div class="weather-hour {css_class}">{item["local_time"]}<br>{item["delay_risk_score"]:.0%}</div>'
        )
    st.markdown(
        f"""
        <div class="card">
            <h2>Weather And NOTAM Risk</h2>
            <div class="muted">
                SGN capacity drops sharply from 08:00 as thunderstorm, windshear and flow-control risk build.
            </div>
            <div class="weather-strip">{''.join(hour_html)}</div>
            <div class="flight-note">Active constraints: ATFM flow management, lightning ramp-stop risk, taxiway W4 closure.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendation(decision: dict[str, Any]) -> None:
    actions = decision["recommended_actions"][:3]
    html = ['<div class="card recommendation"><h2>Supervisor Recommendation</h2>']
    for action in actions:
        if action["type"] == "aircraft_swap":
            title = f"Swap {action['flight']} onto {action['to_tail']}"
        elif action["type"] == "controlled_delay":
            title = f"Delay {action['flight']} by {action['delay_minutes']} min"
        else:
            title = f"Move {action['flight']} to {action['to_resource']}"
        html.append(
            f"""
            <div class="action-row">
                <div class="step-dot">{action['priority']}</div>
                <div>
                    <p class="action-title">{title}</p>
                    <p class="action-reason">{action['reason']}</p>
                </div>
            </div>
            """
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_agents(decision: dict[str, Any]) -> None:
    st.markdown('<div class="agents-title"><h2>Specialist Agents</h2></div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for index, finding in enumerate(decision["agent_findings"]):
        label = AGENT_LABELS[finding["agent"]]
        badge = AGENT_BADGES[finding["agent"]]
        risk = finding["risk_score"]
        with cols[index]:
            st.markdown(
                f"""
                <div class="agent-card">
                    <div class="agent-head">
                        <div class="agent-label"><span class="badge">{badge}</span>{label}</div>
                        <div class="risk">{risk:.0%}</div>
                    </div>
                    <div class="bar"><span style="width: {risk * 100:.0f}%"></span></div>
                    <div class="muted">{finding["summary"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_why(decision: dict[str, Any]) -> None:
    payload = decision["explainability_payload"]
    html = [f'<div class="card"><h2>Why?</h2><div class="muted">{payload["short_answer"]}</div>']
    for step in payload["decision_chain"]:
        html.append(
            f"""
            <div class="why-step">
                <div class="why-num">{step['step']}</div>
                <div>
                    <p class="why-title">{step['finding']}</p>
                    <p class="why-impact">{step['impact']}</p>
                </div>
            </div>
            """
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_alternatives(decision: dict[str, Any]) -> None:
    with st.expander("Rejected alternatives", expanded=False):
        for alternative in decision["alternatives_considered"]:
            st.markdown(f"**{alternative['option']}**")
            st.caption(alternative["rejected_because"])


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def risk_pill(value: str) -> str:
    return f'<span class="pill pill-{esc(value.lower())}">{esc(value)}</span>'


def agent_badge(agent: str) -> str:
    accent = AGENT_ACCENTS.get(agent, "blue")
    label = AGENT_ICON_BADGES.get(agent, "AI")
    return f'<span class="icon-badge {esc(accent)}">{esc(label)}</span>'


def action_title(action: dict[str, Any]) -> str:
    if action["type"] == "aircraft_swap":
        return f"Swap {action['flight']} onto {action['to_tail']}"
    if action["type"] == "controlled_delay":
        return f"Delay {action['flight']} by {action['delay_minutes']} min"
    if action["type"] == "gate_change":
        return f"Move {action['flight']} to {action['to_resource']}"
    if action["type"] == "ground_hold":
        return f"Hold {action['flight']} for {action['hold_minutes']} min"
    if action["type"] == "maintenance_protection":
        return f"Protect {action['tail']} for maintenance"
    if action["type"] == "crew_reallocation":
        return f"Reassign {action['flight']} to {action['to_crew']}"
    if action["type"] == "capacity_rebalance":
        return f"Prioritize {action['flight_bank']}"
    if action["type"] == "departure_metering":
        return f"Meter {action['flight_bank']}"
    if action["type"] == "passenger_protection":
        return f"Protect {action['connection_groups']} connection groups"
    if action["type"] == "recovery_buffer":
        return f"Add {action['buffer_minutes']} min recovery buffers"
    return action["type"].replace("_", " ").title()


def action_dot_class(action_type: str) -> str:
    if action_type in {"controlled_delay", "ground_hold", "maintenance_protection"}:
        return " delay"
    if action_type in {"gate_change", "crew_reallocation", "departure_metering", "recovery_buffer"}:
        return " gate"
    if action_type == "passenger_protection":
        return " delay"
    return ""


def monitor_events(data: dict[str, Any], decision: dict[str, Any]) -> list[tuple[str, str, str]]:
    first_action = action_title(decision["recommended_actions"][0])
    scenario_key = data["scenario"].get("selected_key", "sgn_typhoon")
    scenario_event = {
        "sgn_typhoon": "Typhoon track update increases SGN flow-control probability.",
        "sgn_lightning": "Lightning cells trigger remote-stand handling risk alert.",
        "sgn_maintenance": "New maintenance constraint detected on VN-A152 rotation.",
        "sgn_network_stress": "Morning bank exceeds reduced SGN capacity threshold.",
    }.get(scenario_key, "Operational disruption signal detected.")
    return [
        ("05:40", "weather_agent", scenario_event),
        ("05:42", "maintenance_agent", "Aircraft constraints checked against storm-window dispatch."),
        ("05:44", "crew_agent", "Reserve crew coverage confirmed for the lower-cost delay candidate."),
        ("05:45", "supervisor_agent", f"Recommendation package opened: {first_action}."),
        (
            "05:46",
            "cost_impact_agent",
            f"Impact model estimates US${decision['projected_outcome']['total_estimated_savings_usd']:,} avoidable disruption.",
        ),
    ]


def weather_panel_details(data: dict[str, Any]) -> dict[str, Any]:
    forecast = data["weather_feed"]["airport_forecasts"][0]["hourly_risk"]
    peak = max(forecast, key=lambda item: item["delay_risk_score"])
    min_departure_capacity = min(item["departure_capacity_per_hour"] for item in forecast)
    min_arrival_capacity = min(item["arrival_capacity_per_hour"] for item in forecast)
    notams = data.get("notams", [])[:3]
    return {
        "storm_name": data["weather_feed"]["storm"]["name"],
        "classification": data["weather_feed"]["storm"]["classification"],
        "peak_time": peak["local_time"],
        "peak_risk": f"{peak['delay_risk_score']:.0%}",
        "peak_driver": peak["main_driver"],
        "capacity": f"{min_departure_capacity} dep/hr | {min_arrival_capacity} arr/hr",
        "constraints": [
            {
                "title": f"{notam['category']} {notam['id']}",
                "impact": notam["ops_impact"],
            }
            for notam in notams
        ],
    }


def impact_options(decision: dict[str, Any]) -> list[dict[str, Any]]:
    outcome = decision["projected_outcome"]
    ai_cost = max(4200, outcome["total_estimated_savings_usd"] - 10500)
    baseline_misconnects = 41
    ai_misconnects = max(0, baseline_misconnects - outcome["misconnections_prevented"])
    return [
        {
            "option": "Do nothing",
            "delay": 138,
            "misconnects": baseline_misconnects,
            "cost": ai_cost + outcome["total_estimated_savings_usd"],
        },
        {"option": "Delay protected flight", "delay": 96, "misconnects": 17, "cost": ai_cost + 9400},
        {"option": "AI recommendation", "delay": 42, "misconnects": ai_misconnects, "cost": ai_cost},
    ]


def agent_consensus_items(decision: dict[str, Any]) -> list[tuple[str, str, str]]:
    actions = decision["recommended_actions"]
    first = action_title(actions[0])
    second = action_title(actions[1])
    third = action_title(actions[2])
    return [
        ("weather_agent", "Weather", "Prioritize moves before the highest-risk SGN capacity window."),
        ("aircraft_agent", "Aircraft", f"Supports: {first}."),
        ("crew_agent", "Crew", "Reserve coverage is available for the shifted disruption."),
        ("maintenance_agent", "Maintenance", "Avoids dispatching aircraft with narrow engineering buffers."),
        ("cost_impact_agent", "Cost", f"Best package: {first}; {second}; {third}."),
    ]


def timeline_stage(elapsed_seconds: float) -> dict[str, Any]:
    stage = TIMELINE_MILESTONES[0]
    for milestone in TIMELINE_MILESTONES:
        if elapsed_seconds >= milestone["second"]:
            stage = milestone
        else:
            break
    return stage


def timeline_event_log(elapsed_seconds: float) -> list[dict[str, Any]]:
    return [
        milestone
        for milestone in TIMELINE_MILESTONES
        if milestone["second"] <= elapsed_seconds
    ]


def timeline_clock(elapsed_seconds: float) -> str:
    simulated_minutes = int(
        min(elapsed_seconds, TIMELINE_DEMO_SECONDS)
        / TIMELINE_DEMO_SECONDS
        * TIMELINE_SIMULATED_HOURS
        * 60
    )
    current = datetime.fromisoformat(TIMELINE_START_LOCAL) + timedelta(minutes=simulated_minutes)
    return current.isoformat()


def timeline_snapshot(milestone: dict[str, Any]) -> dict[str, Any]:
    data = load_scenario(milestone["scenario"])
    data["scenario"]["snapshot_time_local"] = timeline_clock(milestone["second"])
    decision = run_agents(data)
    weather = weather_panel_details(data)
    primary = decision["recommended_actions"][:3]
    secondary = decision["recommended_actions"][3:]
    return {
        "second": milestone["second"],
        "clock": timeline_clock(milestone["second"])[11:16],
        "scenario": SCENARIO_OPTIONS[milestone["scenario"]],
        "status": data["scenario"]["status_label"],
        "event": milestone["event"],
        "accepted": milestone["accepted"],
        "cumulativeSavings": milestone["cumulative_savings"],
        "flightsRecovered": milestone["flights_recovered"],
        "acceptedCount": max(0, len(timeline_event_log(milestone["second"])) - 1),
        "dataScope": (
            f"{len(data['scheduled_flights'])} flights | "
            f"{len(data['fleet'])} aircraft | "
            f"{len(data['crew_rosters'])} crews | "
            f"{len(data['passenger_connections'])} connection groups"
        ),
        "confidence": f"{decision['confidence']:.0%}",
        "savings": f"US${milestone['cumulative_savings']:,}",
        "misconnectionsPrevented": decision["projected_outcome"]["misconnections_prevented"],
        "actions": [
            {"title": action_title(action), "reason": action["reason"], "priority": action["priority"]}
            for action in primary
        ],
        "secondaryActions": [
            {"title": action_title(action), "reason": action["reason"], "priority": action["priority"]}
            for action in secondary[:5]
        ],
        "agents": [
            {
                "agent": finding["agent"],
                "label": AGENT_LABELS[finding["agent"]],
                "badge": AGENT_ICON_BADGES[finding["agent"]],
                "accent": AGENT_ACCENTS[finding["agent"]],
                "score": f"{finding['risk_score']:.0%}",
                "width": int(finding["risk_score"] * 100),
                "summary": finding["summary"],
            }
            for finding in decision["agent_findings"]
        ],
        "weather": {
            "storm": weather["storm_name"],
            "peak": f"{weather['peak_time']} | {weather['peak_risk']}",
            "capacity": weather["capacity"],
            "driver": weather["peak_driver"],
        },
        "brief": (
            f"Accepted: {milestone['accepted']}. Current cumulative savings are "
            f"US${milestone['cumulative_savings']:,}, with {milestone['flights_recovered']} flights recovered."
        ),
    }


def build_timeline_player_html() -> str:
    snapshots = [timeline_snapshot(milestone) for milestone in TIMELINE_MILESTONES]
    events = TIMELINE_MILESTONES
    payload = json.dumps({"snapshots": snapshots, "events": events})
    return f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    :root {{
        --bg: #f5f7fb;
        --panel: #ffffff;
        --line: #dfe5ee;
        --text: #111827;
        --muted: #667085;
        --red: #d71920;
        --blue: #2663b8;
        --green: #14845b;
        --amber: #b76800;
        --purple: #7c55c7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .shell {{
        max-width: 1480px;
        margin: 0 auto;
        padding: 12px;
        display: grid;
        gap: 12px;
    }}
    .topbar, .card {{
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--panel);
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }}
    .topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 14px 16px;
    }}
    .brand {{ display: flex; align-items: center; gap: 12px; }}
    .logo {{
        width: 136px;
        height: 42px;
        display: grid;
        place-items: center;
        border: 1px solid #f0c8c8;
        border-radius: 8px;
        color: #d71920;
        font-weight: 900;
        font-style: italic;
    }}
    h1, h2, h3, p {{ margin: 0; }}
    h1 {{ font-size: 22px; line-height: 1.1; }}
    h2 {{ font-size: 18px; margin-bottom: 10px; }}
    h3 {{ font-size: 14px; }}
    .muted {{ color: var(--muted); font-size: 14px; line-height: 1.4; }}
    .status-pill {{
        display: inline-flex;
        padding: 7px 11px;
        border-radius: 999px;
        background: #fff2f2;
        color: #9f1218;
        border: 1px solid #f4c6c6;
        font-weight: 900;
        font-size: 14px;
    }}
    .player {{
        border: 1px solid #c8daf4;
        border-left: 5px solid var(--blue);
        border-radius: 8px;
        background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);
        padding: 14px;
    }}
    .player-head {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        margin-bottom: 12px;
    }}
    .controls {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    button {{
        border: 1px solid #c8daf4;
        border-radius: 8px;
        background: #edf5ff;
        color: #235aa6;
        font-weight: 900;
        padding: 9px 13px;
        cursor: pointer;
        font: inherit;
    }}
    button.primary {{ background: #eafaf2; color: #126044; border-color: #bfe7d5; }}
    .progress {{ height: 9px; border-radius: 999px; background: #e7eef8; overflow: hidden; }}
    .progress span {{
        display: block;
        height: 100%;
        width: 0%;
        background: linear-gradient(90deg, var(--blue) 0%, var(--green) 100%);
        transition: width 420ms ease;
    }}
    .metrics {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
        margin-top: 12px;
    }}
    .metric, .weather-cell {{
        border: 1px solid #d8e5f6;
        border-radius: 8px;
        background: rgba(255,255,255,0.8);
        padding: 10px;
    }}
    .label {{
        color: var(--muted);
        font-size: 11px;
        font-weight: 900;
        text-transform: uppercase;
    }}
    .value {{ font-size: 18px; font-weight: 900; margin-top: 2px; }}
    .grid {{
        display: grid;
        grid-template-columns: minmax(280px, .86fr) minmax(420px, 1.36fr) minmax(300px, 1fr);
        gap: 12px;
        align-items: start;
    }}
    .stack {{ display: grid; gap: 12px; }}
    .card {{ padding: 14px; }}
    .recommendation {{
        border-left: 5px solid var(--green);
        background: linear-gradient(180deg, #ffffff 0%, #f5fff9 100%);
    }}
    .action {{
        display: grid;
        grid-template-columns: 32px 1fr;
        gap: 10px;
        padding: 10px 0;
        border-top: 1px solid #dceee5;
    }}
    .action:first-of-type {{ border-top: 0; padding-top: 0; }}
    .dot {{
        width: 28px;
        height: 28px;
        border-radius: 999px;
        display: grid;
        place-items: center;
        background: var(--green);
        color: #fff;
        font-weight: 900;
        font-size: 13px;
    }}
    .action-title {{ font-size: 17px; font-weight: 900; }}
    .action-reason {{ color: var(--muted); font-size: 14px; line-height: 1.35; margin-top: 3px; }}
    .secondary {{
        display: grid;
        gap: 7px;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #dceee5;
    }}
    .secondary-item {{
        border: 1px solid #dbe8e2;
        border-radius: 8px;
        padding: 8px;
        background: rgba(255,255,255,0.78);
        color: var(--muted);
        font-size: 13px;
    }}
    .weather-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; }}
    .agent-grid {{ display: grid; gap: 8px; }}
    .agent {{
        border: 1px solid var(--line);
        border-radius: 8px;
        border-top: 4px solid var(--blue);
        padding: 10px;
        background: #fff;
    }}
    .agent.red {{ border-top-color: var(--red); background: #fff8f8; }}
    .agent.blue {{ border-top-color: var(--blue); background: #f6faff; }}
    .agent.purple {{ border-top-color: var(--purple); background: #faf7ff; }}
    .agent.amber {{ border-top-color: var(--amber); background: #fffaf0; }}
    .agent.green {{ border-top-color: var(--green); background: #f5fff9; }}
    .agent-head {{ display: flex; justify-content: space-between; gap: 8px; align-items: center; }}
    .agent-name {{ display: flex; gap: 8px; align-items: center; font-weight: 900; }}
    .badge {{
        width: 28px;
        height: 28px;
        border-radius: 7px;
        display: grid;
        place-items: center;
        background: #eef2f7;
        font-size: 11px;
        font-weight: 900;
    }}
    .bar {{ height: 7px; background: #e8edf4; border-radius: 999px; overflow: hidden; margin: 8px 0; }}
    .bar span {{ display: block; height: 100%; width: 0%; transition: width 420ms ease; background: linear-gradient(90deg, #ffc400 0%, #d71920 100%); }}
    .events {{ display: grid; gap: 9px; }}
    .event {{
        display: grid;
        grid-template-columns: 46px 1fr;
        gap: 8px;
        border-top: 1px solid #e4e9f1;
        padding-top: 9px;
        color: var(--muted);
        font-size: 14px;
        line-height: 1.35;
    }}
    .event:first-child {{ border-top: 0; padding-top: 0; }}
    .event-time {{ color: var(--text); font-weight: 900; }}
    .fade {{ transition: opacity 220ms ease, transform 220ms ease; }}
    .fade.updating {{ opacity: .45; transform: translateY(2px); }}
    @media (max-width: 900px) {{
        .shell {{ padding: 8px; }}
        .topbar, .player-head {{ align-items: flex-start; flex-direction: column; }}
        .grid {{ grid-template-columns: 1fr; }}
        .metrics, .weather-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .logo {{ width: 124px; }}
    }}
</style>
</head>
<body>
<div class="shell">
    <div class="topbar">
        <div class="brand">
            <div class="logo">vietjetAir.com</div>
            <div>
                <h1>FlightOps AI</h1>
                <p class="muted">Autonomous operations copilot for disruption management</p>
            </div>
        </div>
        <div>
            <div class="status-pill" id="status">Timeline demo</div>
            <p class="muted" id="scope">12-hour autonomous operations run</p>
        </div>
    </div>

    <div class="player">
        <div class="player-head">
            <div>
                <h2>12-Hour Autonomous Ops Run</h2>
                <p class="muted fade" id="activeEvent">Ready.</p>
            </div>
            <div class="controls">
                <button class="primary" id="playBtn">Start</button>
                <button id="pauseBtn">Pause</button>
                <button id="resetBtn">Reset</button>
            </div>
        </div>
        <div class="progress"><span id="progress"></span></div>
        <div class="metrics">
            <div class="metric"><div class="label">Sim Clock</div><div class="value" id="clock">05:40 ICT</div></div>
            <div class="metric"><div class="label">Accepted Packages</div><div class="value" id="acceptedCount">0</div></div>
            <div class="metric"><div class="label">Flights Recovered</div><div class="value" id="flightsRecovered">0</div></div>
            <div class="metric"><div class="label">Cumulative Savings</div><div class="value" id="cumulativeSavings">US$0</div></div>
        </div>
    </div>

    <div class="grid">
        <div class="stack">
            <div class="card">
                <h2>Scenario Impact</h2>
                <div class="metrics">
                    <div class="metric"><div class="label">Confidence</div><div class="value" id="confidence">--</div></div>
                    <div class="metric"><div class="label">Savings</div><div class="value" id="stageSavings">--</div></div>
                    <div class="metric"><div class="label">Misconnects Prevented</div><div class="value" id="misconnections">--</div></div>
                    <div class="metric"><div class="label">Current Package</div><div class="value" id="package">--</div></div>
                </div>
            </div>
            <div class="card">
                <h2>Weather And NOTAM Risk</h2>
                <div class="weather-grid">
                    <div class="weather-cell"><div class="label">Weather System</div><div class="value" id="weatherStorm">--</div></div>
                    <div class="weather-cell"><div class="label">Peak Risk</div><div class="value" id="weatherPeak">--</div></div>
                    <div class="weather-cell"><div class="label">Capacity Floor</div><div class="value" id="weatherCapacity">--</div></div>
                    <div class="weather-cell"><div class="label">Main Driver</div><div class="value" id="weatherDriver">--</div></div>
                </div>
            </div>
            <div class="card">
                <h2>Autonomous Monitor</h2>
                <div class="events" id="events"></div>
            </div>
        </div>

        <div class="stack">
            <div class="card recommendation">
                <h2>Supervisor Action Package</h2>
                <div id="actions"></div>
                <div class="secondary" id="secondaryActions"></div>
            </div>
            <div class="card">
                <h2>Live Ops Brief</h2>
                <p class="muted fade" id="brief"></p>
            </div>
        </div>

        <div class="stack">
            <div class="card">
                <h2>Specialist Agents</h2>
                <div class="agent-grid" id="agents"></div>
            </div>
        </div>
    </div>
</div>
<script>
const DATA = {payload};
const duration = {TIMELINE_DEMO_SECONDS};
let elapsed = 0;
let running = false;
let timer = null;
let activeIndex = -1;

const money = (value) => "US$" + value.toLocaleString();
const byId = (id) => document.getElementById(id);

function clockFor(second) {{
    const startMinutes = 5 * 60 + 40;
    const simulatedMinutes = Math.floor(Math.max(0, Math.min(duration, second)) / duration * 12 * 60);
    const total = startMinutes + simulatedMinutes;
    const hours = Math.floor(total / 60) % 24;
    const minutes = total % 60;
    return String(hours).padStart(2, "0") + ":" + String(minutes).padStart(2, "0");
}}

function stageFor(second) {{
    let current = DATA.snapshots[0];
    for (const snapshot of DATA.snapshots) {{
        if (second >= snapshot.second) current = snapshot;
    }}
    return current;
}}

function indexFor(second) {{
    let idx = 0;
    DATA.snapshots.forEach((snapshot, i) => {{
        if (second >= snapshot.second) idx = i;
    }});
    return idx;
}}

function setText(id, value) {{
    const el = byId(id);
    if (el.textContent !== String(value)) {{
        el.classList.add("updating");
        setTimeout(() => {{
            el.textContent = value;
            el.classList.remove("updating");
        }}, 120);
    }}
}}

function render(second) {{
    elapsed = Math.max(0, Math.min(duration, second));
    const snapshot = stageFor(elapsed);
    const idx = indexFor(elapsed);
    byId("progress").style.width = Math.round(elapsed / duration * 100) + "%";
    byId("playBtn").textContent = running ? "Running" : (elapsed > 0 && elapsed < duration ? "Resume" : "Start");
    setText("status", snapshot.status);
    const liveClock = clockFor(elapsed);
    setText("scope", "Snapshot " + liveClock + " ICT | " + snapshot.dataScope);
    setText("activeEvent", snapshot.event);
    setText("clock", liveClock + " ICT");
    setText("acceptedCount", snapshot.acceptedCount);
    setText("flightsRecovered", snapshot.flightsRecovered);
    setText("cumulativeSavings", money(snapshot.cumulativeSavings));
    setText("confidence", snapshot.confidence);
    setText("stageSavings", snapshot.savings);
    setText("misconnections", snapshot.misconnectionsPrevented);
    setText("package", snapshot.accepted);
    setText("weatherStorm", snapshot.weather.storm);
    setText("weatherPeak", snapshot.weather.peak);
    setText("weatherCapacity", snapshot.weather.capacity);
    setText("weatherDriver", snapshot.weather.driver);
    setText("brief", snapshot.brief);

    if (idx !== activeIndex) {{
        activeIndex = idx;
        byId("actions").innerHTML = snapshot.actions.map(action => `
            <div class="action">
                <div class="dot">${{action.priority}}</div>
                <div>
                    <p class="action-title">${{action.title}}</p>
                    <p class="action-reason">${{action.reason}}</p>
                </div>
            </div>
        `).join("");
        byId("secondaryActions").innerHTML = `<h3>Secondary Actions</h3>` + snapshot.secondaryActions.map(action => `
            <div class="secondary-item"><strong>${{action.priority}}. ${{action.title}}</strong><br>${{action.reason}}</div>
        `).join("");
        byId("agents").innerHTML = snapshot.agents.map(agent => `
            <div class="agent ${{agent.accent}}">
                <div class="agent-head">
                    <div class="agent-name"><span class="badge">${{agent.badge}}</span>${{agent.label}}</div>
                    <strong>${{agent.score}}</strong>
                </div>
                <div class="bar"><span style="width:${{agent.width}}%"></span></div>
                <p class="muted">${{agent.summary}}</p>
            </div>
        `).join("");
    }}
    byId("events").innerHTML = DATA.events
        .filter(event => event.second <= elapsed)
        .slice(-6)
        .map(event => `<div class="event"><div class="event-time">+${{event.second}}s</div><div>${{event.event}}</div></div>`)
        .join("");
    if (elapsed >= duration) {{
        running = false;
        if (timer) clearInterval(timer);
    }}
}}

function start() {{
    if (elapsed >= duration) elapsed = 0;
    if (timer) clearInterval(timer);
    running = true;
    const startedAt = performance.now() - elapsed * 1000;
    timer = setInterval(() => {{
        render((performance.now() - startedAt) / 1000);
    }}, 250);
    render(elapsed);
}}

function pause() {{
    running = false;
    if (timer) clearInterval(timer);
    render(elapsed);
}}

byId("playBtn").addEventListener("click", start);
byId("pauseBtn").addEventListener("click", pause);
byId("resetBtn").addEventListener("click", () => {{
    pause();
    elapsed = 0;
    activeIndex = -1;
    render(0);
}});
render(0);
</script>
</body>
</html>
"""


def build_dashboard_html(
    data: dict[str, Any], decision: dict[str, Any], llm_briefing: dict[str, Any]
) -> str:
    snapshot = data["scenario"]["snapshot_time_local"]
    outcome = decision["projected_outcome"]
    payload = decision["explainability_payload"]
    logo_src = load_logo_data_uri()
    status_label = data["scenario"].get("status_label", "Typhoon risk near SGN")
    scenario_summary = data["scenario"].get(
        "summary",
        "SGN capacity drops sharply from 08:00 as thunderstorm, windshear and flow-control risk build.",
    )
    data_scope = (
        f"{len(data['scheduled_flights'])} flights | "
        f"{len(data['fleet'])} aircraft | "
        f"{len(data['crew_rosters'])} crews | "
        f"{len(data['passenger_connections'])} connection groups"
    )
    timeline = data.get("timeline_demo")
    timeline_html = ""
    if timeline:
        timeline_events_html = "".join(
            f"""
            <div class="timeline-event">
                <div class="timeline-event-time">+{esc(event['second'])}s</div>
                <div>{esc(event['event'])}</div>
            </div>
            """
            for event in timeline["events"][-4:]
        )
        timeline_html = f"""
            <div class="timeline-card">
                <div class="timeline-head">
                    <div>
                        <p class="timeline-title">12-Hour Autonomous Ops Run</p>
                        <p class="timeline-sub">{esc(timeline['active_event'])}</p>
                    </div>
                    <span class="timeline-pill">{'Running' if timeline['running'] else 'Paused'} | {esc(timeline['simulated_hours'])}h simulated</span>
                </div>
                <div class="timeline-progress"><span style="width: {timeline['progress'] * 100:.0f}%"></span></div>
                <div class="timeline-metrics">
                    <div class="timeline-metric">
                        <div class="timeline-label">Sim Clock</div>
                        <div class="timeline-value">{esc(timeline['clock'][11:16])} ICT</div>
                    </div>
                    <div class="timeline-metric">
                        <div class="timeline-label">Accepted Packages</div>
                        <div class="timeline-value">{esc(timeline['accepted_count'])}</div>
                    </div>
                    <div class="timeline-metric">
                        <div class="timeline-label">Flights Recovered</div>
                        <div class="timeline-value">{esc(timeline['flights_recovered'])}</div>
                    </div>
                    <div class="timeline-metric">
                        <div class="timeline-label">Cumulative Savings</div>
                        <div class="timeline-value">US${timeline['cumulative_savings']:,}</div>
                    </div>
                </div>
                <div class="timeline-events">{timeline_events_html}</div>
            </div>
        """

    metrics = [
        ("Confidence", f"{decision['confidence']:.0%}"),
        ("Savings", f"US${outcome['total_estimated_savings_usd']:,}"),
        ("Delay avoided", f"{outcome['delay_minutes_avoided']} min"),
        ("Misconnections prevented", outcome["misconnections_prevented"]),
    ]
    metric_html = "".join(
        f"""
        <div class="metric-tile">
            <div class="metric-label">{esc(label)}</div>
            <div class="metric-value">{esc(value)}</div>
        </div>
        """
        for label, value in metrics
    )

    forecast = data["weather_feed"]["airport_forecasts"][0]["hourly_risk"]
    weather_details = weather_panel_details(data)
    weather_html = "".join(
        f"""
        <div class="weather-hour {'hot' if item['delay_risk_score'] >= 0.75 else 'warn' if item['delay_risk_score'] >= 0.55 else ''}">
            {esc(item['local_time'])}<br>{item['delay_risk_score']:.0%}
        </div>
        """
        for item in forecast
    )
    constraint_html = "".join(
        f"""
        <div class="constraint-item">
            <p class="constraint-title">{esc(item['title'])}</p>
            <p class="constraint-impact">{esc(item['impact'])}</p>
        </div>
        """
        for item in weather_details["constraints"]
    )

    primary_actions = decision["recommended_actions"][:3]
    secondary_actions = decision["recommended_actions"][3:]
    action_html = []
    for action in primary_actions:
        title = action_title(action)
        dot_class = action_dot_class(action["type"])
        action_html.append(
            f"""
            <div class="action-row">
                <div class="step-dot{dot_class}">{action['priority']}</div>
                <div>
                    <p class="action-title">{esc(title)}</p>
                    <p class="action-reason">{esc(action['reason'])}</p>
                </div>
            </div>
            """
        )
    secondary_action_html = "".join(
        f"""
        <div class="secondary-action">
            <div class="step-dot{action_dot_class(action['type'])}">{esc(action['priority'])}</div>
            <div>
                <p class="secondary-title">{esc(action_title(action))}</p>
                <p class="secondary-reason">{esc(action['reason'])}</p>
            </div>
        </div>
        """
        for action in secondary_actions
    )
    secondary_block = (
        f"""
        <div class="action-subhead">
            <h3>Secondary Actions</h3>
            <span class="action-count">{len(secondary_actions)} execution actions</span>
        </div>
        <div class="secondary-actions">{secondary_action_html}</div>
        """
        if secondary_actions
        else ""
    )

    monitor_html = "".join(
        f"""
        <div class="event-item">
            <div class="event-time">{esc(time)}</div>
            <div class="event-body">
                <div class="event-head">{agent_badge(agent)}{esc(AGENT_LABELS.get(agent, 'Supervisor'))} Agent</div>
                <div class="event-text">{esc(text)}</div>
            </div>
        </div>
        """
        for time, agent, text in monitor_events(data, decision)
    )

    impact_rows_html = "".join(
        f"""
        <tr class="{'recommended-row' if item['option'] == 'AI recommendation' else ''}">
            <td>{esc(item['option'])}</td>
            <td>{esc(item['delay'])} min</td>
            <td>{esc(item['misconnects'])}</td>
            <td>US${item['cost']:,}</td>
        </tr>
        """
        for item in impact_options(decision)
    )

    control_html = "".join(
        f"""
        <button class="control-button {button_class}" type="button">
            <span class="control-icon">{icon}</span>
            <span>{label}</span>
        </button>
        """
        for label, icon, button_class in [
            ("Approve", "&check;", "approve"),
            ("Simulate", "&#8635;", "simulate"),
            ("Reject", "&times;", "reject"),
        ]
    )

    flight_rows = []
    for row in flight_table(data).to_dict("records"):
        flight_rows.append(
            f"""
            <tr>
                <td><span class="flight-id">{esc(row['Flight'])}</span></td>
                <td>{esc(row['Route'])}</td>
                <td>{esc(row['STD'])}</td>
                <td>{esc(row['Aircraft'])}</td>
                <td>{esc(row['Gate/Stand'])}</td>
                <td>{esc(row['Passengers'])}</td>
                <td>{risk_pill(row['Risk'])}</td>
                <td>{esc(row['Ops impact'])}</td>
            </tr>
            """
        )

    why_html = []
    why_colors = ["red", "green", "blue", "purple", "amber"]
    for step in payload["decision_chain"]:
        color = why_colors[(step["step"] - 1) % len(why_colors)]
        why_html.append(
            f"""
            <div class="why-step">
                <div class="why-num {color}">{esc(step['step'])}</div>
                <div>
                    <p class="why-title">{esc(step['finding'])}</p>
                    <p class="why-impact">{esc(step['impact'])}</p>
                </div>
            </div>
            """
        )

    agent_html = []
    for finding in decision["agent_findings"]:
        agent = finding["agent"]
        risk = finding["risk_score"]
        accent = AGENT_ACCENTS[agent]
        agent_html.append(
            f"""
            <div class="agent-card {accent}">
                <div class="agent-head">
                    <div class="agent-label">{agent_badge(agent)}{esc(AGENT_LABELS[agent])}</div>
                    <div class="risk">{risk:.0%}</div>
                </div>
                <div class="bar"><span style="width: {risk * 100:.0f}%"></span></div>
                <div class="muted">{esc(AGENT_SHORT_SUMMARIES[agent])}</div>
            </div>
            """
        )

    alternatives_html = "".join(
        f"""
        <div class="alternative">
            <p class="alternative-title">{esc(alternative['option'])}</p>
            <p class="alternative-reason">{esc(alternative['rejected_because'])}</p>
        </div>
        """
        for alternative in decision["alternatives_considered"][:3]
    )
    trace_items = [
        ("weather_agent", "Weather", "High-risk window begins at 08:00; peak SGN disruption at 10:00."),
        ("aircraft_agent", "Aircraft", "VN-A237 is eligible, at SGN, and matches VJ152 capacity."),
        ("crew_agent", "Crew", "Reserve crew C-SGN-R12 can cover VJ237 after delay."),
        ("maintenance_agent", "Maintenance", "VN-A678 stays protected due radar MEL and 09:30 rectification."),
        ("cost_impact_agent", "Cost", "Protecting VJ152 prevents the largest connection-cost cascade."),
    ]
    trace_html = "".join(
        f"""
        <div class="trace-item">
            {agent_badge(agent)}
            <div>
                <p class="trace-title">{esc(title)}</p>
                <p class="trace-detail">{esc(detail)}</p>
            </div>
        </div>
        """
        for agent, title, detail in trace_items
    )
    consensus_html = "".join(
        f"""
        <div class="consensus-item">
            {agent_badge(agent)}
            <div>
                <p class="trace-title">{esc(title)}</p>
                <p class="trace-detail">{esc(detail)}</p>
            </div>
        </div>
        """
        for agent, title, detail in agent_consensus_items(decision)
    )
    ops_brief = (
        f"Recommendation package ready for duty manager approval. {decision['headline']} "
        f"Estimated savings: US${outcome['total_estimated_savings_usd']:,}. "
        f"Confidence: {decision['confidence']:.0%}. Residual risk: {outcome['residual_risk']}"
    )
    llm_enabled = llm_briefing["enabled"]
    llm_badge = (
        f"Claude via AWS Bedrock" if llm_enabled else "Fallback briefing"
    )
    llm_badge_class = "ai-badge" if llm_enabled else "ai-badge off"

    return f"""
        <div class="dashboard-shell">
            <div class="topbar">
                <div class="brand">
                    <div class="brand-mark">
                        <img src="{logo_src}" alt="VietJet Air logo">
                    </div>
                    <div>
                        <h1>FlightOps AI</h1>
                        <p>Autonomous operations copilot for disruption management</p>
                    </div>
                </div>
                <div>
                    <div class="status-pill">{esc(status_label)}</div>
                    <p class="status-sub">Snapshot {esc(snapshot[11:16])} ICT | 6-hour horizon | {esc(data_scope)}</p>
                </div>
            </div>
            {timeline_html}

            <div class="cockpit-grid">
                <div class="stack impact-stack">
                    <div class="card">
                        <h2>Scenario Impact</h2>
                        <div class="metric-grid">{metric_html}</div>
                    </div>
                    <div class="card">
                        <h2>Weather And NOTAM Risk</h2>
                        <div class="muted">{esc(scenario_summary)}</div>
                        <div class="weather-strip">{weather_html}</div>
                        <div class="weather-meta">
                            <div class="weather-meta-item">
                                <div class="weather-meta-label">Weather System</div>
                                <div class="weather-meta-value">{esc(weather_details['storm_name'])}</div>
                            </div>
                            <div class="weather-meta-item">
                                <div class="weather-meta-label">Peak Risk</div>
                                <div class="weather-meta-value">{esc(weather_details['peak_time'])} | {esc(weather_details['peak_risk'])}</div>
                            </div>
                            <div class="weather-meta-item">
                                <div class="weather-meta-label">Capacity Floor</div>
                                <div class="weather-meta-value">{esc(weather_details['capacity'])}</div>
                            </div>
                            <div class="weather-meta-item">
                                <div class="weather-meta-label">Main Driver</div>
                                <div class="weather-meta-value">{esc(weather_details['peak_driver'])}</div>
                            </div>
                        </div>
                        <div class="constraint-list">{constraint_html}</div>
                    </div>
                    <div class="card monitor-card">
                        <h2>Autonomous Monitor</h2>
                        <div class="event-list">{monitor_html}</div>
                    </div>
                </div>

                <div class="stack decision-stack">
                    <div class="card recommendation">
                        <div class="rec-head">
                            <h2>Supervisor Action Package</h2>
                            <span class="recommended-label">{len(primary_actions)} primary | {len(secondary_actions)} secondary</span>
                        </div>
                        {''.join(action_html)}
                        {secondary_block}
                        <div class="control-row">{control_html}</div>
                        <div class="before-after">
                            <div class="impact-cell">
                                <div class="impact-label">Misconnects</div>
                                <div class="impact-change"><span class="before">41</span><span>&rarr;</span><span class="after">3</span></div>
                            </div>
                            <div class="impact-cell">
                                <div class="impact-label">Delay Exposure</div>
                                <div class="impact-change"><span class="before">138 min</span><span>&rarr;</span><span class="after">42 min</span></div>
                            </div>
                            <div class="impact-cell">
                                <div class="impact-label">Cost Risk</div>
                                <div class="impact-change"><span class="before">US$25.9k</span><span>&rarr;</span><span class="after">US$7.7k</span></div>
                            </div>
                        </div>
                    </div>
                    <div class="card">
                        <h2>Scenario Impact Comparison</h2>
                        <table class="comparison-table">
                            <thead>
                                <tr>
                                    <th>Option</th>
                                    <th>Delay</th>
                                    <th>Misconnects</th>
                                    <th>Cost</th>
                                </tr>
                            </thead>
                            <tbody>{impact_rows_html}</tbody>
                        </table>
                    </div>
                    <div class="card">
                        <h2>Affected Flights</h2>
                        <div class="table-scroll">
                            <table class="flight-table">
                                <thead>
                                    <tr>
                                        <th>Flight</th>
                                        <th>Route</th>
                                        <th>STD</th>
                                        <th>Aircraft</th>
                                        <th>Gate</th>
                                        <th>Pax</th>
                                        <th>Risk</th>
                                        <th>Ops Impact</th>
                                    </tr>
                                </thead>
                                <tbody>{''.join(flight_rows)}</tbody>
                            </table>
                        </div>
                        <div class="flight-note">Focused morning wave for the 2-3 minute demo.</div>
                    </div>
                </div>

                <div class="stack why-stack">
                    <div class="card ai-briefing">
                        <div class="ai-head">
                            <h2>LLM Ops Briefing</h2>
                            <span class="{llm_badge_class}">{esc(llm_badge)}</span>
                        </div>
                        <div class="briefing-text">{esc(llm_briefing['text'])}</div>
                    </div>
                    <div class="card ops-brief">
                        <div class="ai-head">
                            <h2>Duty Manager Brief</h2>
                            <span class="ai-badge off">Copy-ready</span>
                        </div>
                        <div class="briefing-text">{esc(ops_brief)}</div>
                    </div>
                    <div class="card">
                        <h2>Ops Manager asks: Why?</h2>
                        <div class="muted">{esc(payload['short_answer'])}</div>
                        {''.join(why_html)}
                    </div>
                    <div class="card">
                        <h2>Agent Consensus</h2>
                        <div class="trace-list">{consensus_html}</div>
                    </div>
                    <div class="card">
                        <h2>Decision Trace</h2>
                        <div class="trace-list">{trace_html}</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Specialist Agents</h2>
                <div class="agent-grid">{''.join(agent_html)}</div>
            </div>
            <div class="card">
                <h2>Rejected Alternatives</h2>
                <div class="alternatives-list">{alternatives_html}</div>
            </div>
        </div>
        """


def render_dashboard(
    data: dict[str, Any], decision: dict[str, Any], llm_briefing: dict[str, Any]
) -> None:
    st.html(build_dashboard_html(data, decision, llm_briefing))
    with st.expander("LLM evidence bundle"):
        st.caption(
            "The LLM briefing is grounded on this structured agent evidence. "
            "If AWS Bedrock is not configured, the app uses the deterministic fallback briefing."
        )
        st.json(llm_briefing["evidence_bundle"])
        if llm_briefing.get("error"):
            st.caption(f"LLM fallback reason: {llm_briefing['error']}")


def render_timeline_demo() -> None:
    components.html(build_timeline_player_html(), height=1900, scrolling=True)


def main() -> None:
    st.set_page_config(
        page_title="FlightOps AI",
        page_icon=":airplane:",
        layout="wide",
    )

    inject_styles()
    demo_mode = st.query_params.get("demo")
    if demo_mode == "timeline":
        render_timeline_demo()
        return

    selected_scenario = st.selectbox(
        "Scenario",
        options=list(SCENARIO_OPTIONS),
        format_func=lambda key: SCENARIO_OPTIONS[key],
        index=0,
    )
    data = load_scenario(selected_scenario)
    decision = run_agents(data)
    llm_briefing = run_llm_briefing(data, decision)
    render_dashboard(data, decision, llm_briefing)


if __name__ == "__main__":
    main()
