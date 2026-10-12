import unittest

from backend.generate_data import (
    apply_event_effect,
    compute_future_supply,
    generate_base_supply,
)


class SupplyGenerationTests(unittest.TestCase):
    def test_zone_and_time_patterns_are_reflected_in_base_supply(self):
        self.assertGreater(
            generate_base_supply(hour=8, day_of_week=0, zone="Z4"),
            generate_base_supply(hour=23, day_of_week=0, zone="Z3"),
        )

    def test_event_effect_does_not_change_demand_without_event(self):
        self.assertEqual(apply_event_effect(100, 0), 100)

    def test_future_supply_is_never_negative(self):
        prediction = compute_future_supply(
            current_supply=1,
            reserve_bookings=100,
            weather_severity=2,
            event_density=2,
            hour=23,
            day_of_week=6,
            zone="Z1",
        )
        self.assertGreaterEqual(prediction, 0)


if __name__ == "__main__":
    unittest.main()
