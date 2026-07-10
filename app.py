from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


DATA_PATH = Path("demo-data/flightops-ai-typhoon-sgn-2026-07-12.json")


@st.cache_data
def load_demo_data() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def flight_table(data: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for flight in data["scheduled_flights"]:
        rows.append(
            {
                "Flight": flight["flight"],
                "Route": flight["route"],
                "STD": flight["scheduled_departure_local"][11:16],
                "Aircraft": flight["aircraft_tail"],
                "Gate/Stand": flight.get("planned_gate") or flight.get("planned_stand"),
                "Passengers": flight["passengers_booked"],
                "Priority": flight["priority"],
                "Status": flight["status_at_snapshot"].replace("_", " "),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    st.set_page_config(
        page_title="FlightOps AI",
        page_icon=":airplane:",
        layout="wide",
    )

    data = load_demo_data()
    decision = data["supervisor_decision"]
    outcome = decision["projected_outcome"]

    st.title("FlightOps AI")
    st.caption("Autonomous operations copilot demo for Vietjet disruption management")

    metric_cols = st.columns(4)
    metric_cols[0].metric("Confidence", f"{decision['confidence']:.0%}")
    metric_cols[1].metric("Estimated savings", f"US${outcome['total_estimated_savings_usd']:,}")
    metric_cols[2].metric("Delay avoided", f"{outcome['delay_minutes_avoided']} min")
    metric_cols[3].metric("Misconnections prevented", outcome["misconnections_prevented"])

    st.subheader("Supervisor Recommendation")
    st.write(decision["headline"])

    st.subheader("Morning Wave")
    st.dataframe(flight_table(data), use_container_width=True, hide_index=True)

    st.subheader("Specialist Agent Findings")
    for finding in data["agent_findings"]:
        with st.expander(finding["agent"].replace("_", " ").title(), expanded=True):
            st.write(finding["summary"])
            st.progress(finding["risk_score"])
            st.markdown("Evidence:")
            for evidence in finding["evidence"]:
                st.markdown(f"- {evidence}")

    st.subheader('Ops Manager Asks: "Why?"')
    st.write(data["explainability_payload"]["short_answer"])

    for step in data["explainability_payload"]["decision_chain"]:
        st.markdown(f"**{step['step']}. {step['finding']}**")
        st.write(step["impact"])


if __name__ == "__main__":
    main()
