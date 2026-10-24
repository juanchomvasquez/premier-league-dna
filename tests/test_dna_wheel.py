"""The visual must preserve evidence rates and never fabricate history."""
import base64
import unittest
import xml.etree.ElementTree as ET

from pl_dna.roles import ROLE_DEFINITIONS, PLAYERS, analyze_role_player, generate_role_events
from pl_dna.dna_wheel import wheel_data, radar_svg, reference_card
import test_dashboard


class WheelTests(unittest.TestCase):
    def test_all_positions_retain_exact_rates_and_use_valid_svg(self):
        events = generate_role_events(42)
        for player, role in PLAYERS.items():
            definition = ROLE_DEFINITIONS[role]
            report = analyze_role_player(events, player, 0, 90)
            for profile in definition["profiles"]:
                with self.subTest(role=role, profile=profile):
                    rows = wheel_data(definition, report, profile)
                    self.assertEqual([r["observed_rate"] for r in rows],
                                     [100 * m["count"] / report["action_sequences"] for m in report["measurements"]])
                    self.assertEqual([r["reference_rate"] for r in rows], definition["profiles"][profile])
                    svg = radar_svg(rows, player, profile)
                    ET.fromstring(svg)
                    self.assertIn('stroke-dasharray="7 5"', svg)
                    self.assertIn('stroke="#39dfbc"', svg)
                    card = reference_card(definition, profile, rows)
                    self.assertIn("Not selected yet", card)
                    self.assertIn("No historical index score yet", card)

    def test_empty_sample_and_overflow_are_not_drawn_as_reliable_or_clipped(self):
        definition = ROLE_DEFINITIONS["CM"]
        report = {"action_sequences": 0, "measurements": [{"measurement": m, "count": 0} for m in definition["metrics"]]}
        rows = wheel_data(definition, report, "Box-to-box attacker")
        svg = radar_svg(rows, "Test", "Lampard", show_observed=False)
        self.assertNotIn('stroke="#39dfbc"', svg)
        self.assertTrue(all(row["observed_rate"] is None for row in rows))
        rows[0]["reference_rate"] = 150
        self.assertIn('>160</text>', radar_svg(rows, "Test", "Reference", False))

    def test_reference_selector_changes_wheel_without_changing_evidence(self):
        at = test_dashboard.DashboardTests().app()
        initial_counts = [m.value for m in at.metric]
        at.selectbox(key="dna_reference_Central midfield").select("Deep distributor").run()
        self.assertEqual(list(at.exception), [])
        self.assertEqual([m.value for m in at.metric], initial_counts)
        self.assertIn("Scholes Index", test_dashboard.html(at))
        self.assertNotIn("Lampard Index", test_dashboard.html(at))
        # st.image serves the SVG as a data URI rather than sanitizable inline HTML.
        image = at.get("image")[0].proto.imgs[0]
        svg = base64.b64decode(image.url.split(",", 1)[1]).decode()
        self.assertIn("selected synthetic performance only", svg)
        self.assertNotIn('stroke="#b69aff"', svg)
        at.checkbox(key="illustrative_overlay").check().run()
        image = at.get("image")[0].proto.imgs[0]
        svg = base64.b64decode(image.url.split(",", 1)[1]).decode()
        self.assertIn("Scholes-inspired", svg)
        at.slider(key="minute").set_value(1).run()
        self.assertEqual(list(at.exception), [])
        image = at.get("image")[0].proto.imgs[0]
        svg = base64.b64decode(image.url.split(",", 1)[1]).decode()
        self.assertNotIn('stroke="#39dfbc"', svg)


if __name__ == "__main__":
    unittest.main()
