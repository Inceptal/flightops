from __future__ import annotations

import unittest

from app import SCENARIO_OPTIONS, load_scenario, run_agents


class ScenarioVariantTests(unittest.TestCase):
    def test_all_scenarios_generate_core_recommendation(self) -> None:
        for scenario_key in SCENARIO_OPTIONS:
            with self.subTest(scenario_key=scenario_key):
                data = load_scenario(scenario_key)
                decision = run_agents(data)
                first_action = decision["recommended_actions"][0]
                self.assertEqual(first_action["flight"], "VJ152")
                self.assertEqual(first_action["to_tail"], "VN-A237")

    def test_network_stress_scenario_has_high_volume_data(self) -> None:
        data = load_scenario("sgn_network_stress")
        self.assertGreaterEqual(len(data["scheduled_flights"]), 40)
        self.assertGreaterEqual(len(data["fleet"]), 20)
        self.assertGreaterEqual(len(data["crew_rosters"]), 20)


if __name__ == "__main__":
    unittest.main()
