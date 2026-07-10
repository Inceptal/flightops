from __future__ import annotations

import unittest

from app import SCENARIO_OPTIONS, impact_options, load_scenario, run_agents, weather_panel_details


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

    def test_network_stress_scenario_has_full_action_package(self) -> None:
        data = load_scenario("sgn_network_stress")
        decision = run_agents(data)
        action_types = {action["type"] for action in decision["recommended_actions"]}
        self.assertGreaterEqual(len(decision["recommended_actions"]), 8)
        self.assertIn("departure_metering", action_types)
        self.assertIn("passenger_protection", action_types)
        self.assertIn("recovery_buffer", action_types)

    def test_impact_comparison_shows_remaining_misconnects(self) -> None:
        data = load_scenario("sgn_network_stress")
        decision = run_agents(data)
        ai_row = next(item for item in impact_options(decision) if item["option"] == "AI recommendation")
        self.assertEqual(ai_row["misconnects"], 3)
        self.assertEqual(decision["projected_outcome"]["misconnections_prevented"], 38)

    def test_weather_panel_details_are_scenario_specific(self) -> None:
        details = {
            scenario_key: weather_panel_details(load_scenario(scenario_key))
            for scenario_key in SCENARIO_OPTIONS
        }
        storm_names = {item["storm_name"] for item in details.values()}
        peak_drivers = {item["peak_driver"] for item in details.values()}
        self.assertGreaterEqual(len(storm_names), 4)
        self.assertGreaterEqual(len(peak_drivers), 3)
        self.assertIn("SGN Capacity Compression Window", storm_names)
        self.assertIn("SGN Heat And Convective Recovery Window", storm_names)


if __name__ == "__main__":
    unittest.main()
