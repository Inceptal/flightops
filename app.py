from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from flightops.supervisor import SupervisorAgent


DATA_PATH = Path("demo-data/flightops-ai-typhoon-sgn-2026-07-12.json")
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


@st.cache_data
def load_demo_data() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def run_agents(data: dict[str, Any]) -> dict[str, Any]:
    return SupervisorAgent().decide(data)


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
        div[data-testid="stVerticalBlock"] {
            gap: 0.75rem;
        }
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 1.25rem;
            max-width: 1420px;
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
            width: 38px;
            height: 38px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            background: #d71920;
            color: #fff;
            font-weight: 800;
            letter-spacing: 0;
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
            padding: 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }
        .card h2, .card h3 {
            margin: 0 0 0.7rem;
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
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.65rem;
        }
        .metric-tile {
            border: 1px solid #e2e7ef;
            border-radius: 8px;
            background: #fbfcfe;
            padding: 0.78rem;
            min-height: 84px;
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
            font-size: 1.45rem;
            font-weight: 800;
            margin-top: 0.22rem;
            letter-spacing: 0;
        }
        .recommendation {
            border-color: #bfe7d5;
            background: linear-gradient(180deg, #ffffff 0%, #f5fff9 100%);
        }
        .action-row {
            display: grid;
            grid-template-columns: 2rem 1fr;
            gap: 0.7rem;
            padding: 0.72rem 0;
            border-top: 1px solid #dceee5;
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
        .action-title {
            font-size: 1rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: 0;
        }
        .action-reason {
            margin: 0.18rem 0 0;
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.4;
        }
        .agent-card {
            border: 1px solid #dfe5ee;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.78rem;
            min-height: 142px;
        }
        .agent-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.45rem;
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
            margin: 0.45rem 0 0.55rem;
        }
        .bar span {
            display: block;
            height: 100%;
            background: linear-gradient(90deg, #ffc400 0%, #d71920 100%);
        }
        .why-step {
            display: grid;
            grid-template-columns: 1.8rem 1fr;
            gap: 0.65rem;
            padding: 0.65rem 0;
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
        .why-title {
            font-weight: 800;
            margin: 0;
            font-size: 0.9rem;
        }
        .why-impact {
            margin: 0.16rem 0 0;
            color: var(--muted);
            font-size: 0.83rem;
            line-height: 1.4;
        }
        .weather-strip {
            display: flex;
            gap: 0.35rem;
            margin-top: 0.75rem;
        }
        .weather-hour {
            flex: 1;
            border-radius: 6px;
            padding: 0.48rem 0.35rem;
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
        @media (max-width: 900px) {
            div[data-testid="stHorizontalBlock"] {
                flex-wrap: wrap;
            }
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }
            .topbar {
                align-items: flex-start;
                flex-direction: column;
            }
            .metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .metric-value {
                font-size: 1.2rem;
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


def main() -> None:
    st.set_page_config(
        page_title="FlightOps AI",
        page_icon=":airplane:",
        layout="wide",
    )

    data = load_demo_data()
    decision = run_agents(data)
    inject_styles()
    render_topbar(data)

    left_col, center_col, right_col = st.columns([1.0, 1.45, 1.1], gap="medium")
    with left_col:
        render_metrics(decision)
        render_weather_snapshot(data)

    with center_col:
        render_recommendation(decision)
        st.markdown('<div class="section-title"><h2>Affected Flights</h2></div>', unsafe_allow_html=True)
        flights = flight_table(data)
        st.dataframe(
            style_flight_table(flights),
            use_container_width=True,
            hide_index=True,
            height=220,
        )
        st.markdown(
            '<div class="table-note">Focused morning wave for the 2-3 minute demo.</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        render_why(decision)
        render_alternatives(decision)

    render_agents(decision)


if __name__ == "__main__":
    main()
