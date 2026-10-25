"""The unified dashboard preserves evidence and explicit-call boundaries."""
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from pl_dna.roles import ROLE_DEFINITIONS, generate_role_events, analyze_role_player


def html(at):
    return "\n".join(element.proto.body for element in at.get("html"))


class DashboardTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run().radio(key="data_source").set_value("Eight-position synthetic demo").run()

    def assert_healthy(self, at):
        self.assertEqual([e.message for e in at.exception], [])

    def test_all_roles_preserve_counts_in_the_unified_dashboard(self):
        data = generate_role_events(42)
        at = self.app()
        self.assertFalse(any(r.key == "audience" for r in at.radio))
        for role in ROLE_DEFINITIONS:
            at.selectbox(key="position").select(role).run()
            at.slider(key="minute").set_value(90).run()
            for view in ("Match so far", "Last 15 minutes"):
                with self.subTest(role=role, view=view):
                    at.radio(key="window_view").set_value(view).run()
                    start = 0 if view == "Match so far" else 75
                    self.assert_healthy(at)
                    player = next(s.value for s in at.selectbox if s.label == "Player")
                    report = analyze_role_player(data, player, start, 90)
                    self.assertEqual(at.metric[0].value, str(report["action_sequences"]))
                    self.assertIn(f"minutes ({start}, 90]", html(at))
                    self.assertIn("schematic", html(at))
                    rates = next(df.value for df in at.dataframe if "Per 100 sequences" in df.value.columns)
                    self.assertEqual(rates["Count"].tolist(), [m["count"] for m in report["measurements"]])
                    self.assertEqual(len(at.code), 1)

    def test_synthetic_mode_routes_azure_to_recorded_comparison_without_calling(self):
        with patch("pl_dna.microsoft_provider.create_provider_from_env", new=Mock()) as factory:
            at = self.app()
            at.radio(key="insight_source").set_value("Microsoft AI").run()
            self.assert_healthy(at)
            self.assertTrue(any("This season & live" in c.value for c in at.info))
            factory.assert_not_called()

    def test_updated_striker_cards_include_henry_and_rooney_without_changing_data(self):
        at = self.app()
        at.selectbox(key="position").select("ST").run()
        at.slider(key="minute").set_value(90).run()
        self.assert_healthy(at)
        body = html(at)
        self.assertEqual(body.count('class="profile-card"'), 4)
        for name in ("Shearer", "Drogba", "Henry", "Rooney"):
            self.assertIn(f"{name}-inspired", body)
        self.assertEqual(at.metric[0].value, "60")


if __name__ == "__main__":
    unittest.main()
