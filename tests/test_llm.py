from __future__ import annotations

import unittest
from pathlib import Path

from flightops.llm import LLMExplanationAgent
from flightops.run_agents import load_data
from flightops.supervisor import SupervisorAgent


class LLMExplanationAgentTests(unittest.TestCase):
    def test_falls_back_without_bedrock_environment(self) -> None:
        data = load_data(Path("demo-data/flightops-ai-typhoon-sgn-2026-07-12.json"))
        decision = SupervisorAgent().decide(data)
        briefing = LLMExplanationAgent().run(data, decision)

        self.assertFalse(briefing.enabled)
        self.assertEqual(briefing.provider, "deterministic-fallback")
        self.assertIn("FlightOps AI recommends", briefing.text)
        self.assertIn("agent_findings", briefing.evidence_bundle)


if __name__ == "__main__":
    unittest.main()
