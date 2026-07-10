from __future__ import annotations

import unittest
from pathlib import Path

from flightops.run_agents import run_scenario


class FlightOpsAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.decision = run_scenario(Path("demo-data/flightops-ai-typhoon-sgn-2026-07-12.json"))

    def test_supervisor_recommends_aircraft_swap(self) -> None:
        action = self.decision["recommended_actions"][0]
        self.assertEqual(action["type"], "aircraft_swap")
        self.assertEqual(action["flight"], "VJ152")
        self.assertEqual(action["to_tail"], "VN-A237")

    def test_all_specialist_agents_return_findings(self) -> None:
        agents = {finding["agent"] for finding in self.decision["agent_findings"]}
        self.assertEqual(
            agents,
            {
                "weather_agent",
                "aircraft_agent",
                "crew_agent",
                "maintenance_agent",
                "cost_impact_agent",
            },
        )

    def test_explainability_payload_is_generated(self) -> None:
        payload = self.decision["explainability_payload"]
        self.assertIn("VJ152", payload["short_answer"])
        self.assertEqual(len(payload["decision_chain"]), 5)


if __name__ == "__main__":
    unittest.main()
