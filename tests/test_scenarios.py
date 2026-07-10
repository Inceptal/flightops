from __future__ import annotations

import unittest

from app import SCENARIO_OPTIONS, load_scenario, run_agents


class ScenarioVariantTests(unittest.TestCase):
    def test_all_scenarios_generate_recommendations(self) -> None:
        for scenario_key in SCENARIO_OPTIONS:
            with self.subTest(scenario_key=scenario_key):
                data = load_scenario(scenario_key)
                decision = run_agents(data)
                self.assertGreaterEqual(len(decision["recommended_actions"]), 3)
                self.assertTrue(decision["headline"])

    def test_scenarios_have_distinct_first_actions(self) -> None:
        expected_first_action_types = {
            "sgn_typhoon": "aircraft_swap",
            "sgn_lightning": "ground_hold",
            "sgn_maintenance": "aircraft_swap",
            "sgn_network_stress": "capacity_rebalance",
        }
        for scenario_key, expected_type in expected_first_action_types.items():
            with self.subTest(scenario_key=scenario_key):
                data = load_scenario(scenario_key)
                decision = run_agents(data)
                self.assertEqual(decision["recommended_actions"][0]["type"], expected_type)

    def test_network_stress_scenario_has_high_volume_data(self) -> None:
        data = load_scenario("sgn_network_stress")
        self.assertGreaterEqual(len(data["scheduled_flights"]), 40)
        self.assertGreaterEqual(len(data["fleet"]), 20)
        self.assertGreaterEqual(len(data["crew_rosters"]), 20)


if __name__ == "__main__":
    unittest.main()
