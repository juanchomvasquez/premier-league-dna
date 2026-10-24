"""Audience changes must preserve evidence and explicit-call boundaries."""
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from pl_dna.roles import ROLE_DEFINITIONS, generate_role_events, analyze_role_player


def html(at):
    return "\n".join(element.proto.body for element in at.get("html"))


class DashboardTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()

    def assert_healthy(self, at):
        self.assertEqual([e.message for e in at.exception], [])

    def test_all_roles_and_audiences_preserve_the_same_window_counts(self):
        data = generate_role_events(42)
        at = self.app()
        for role in ROLE_DEFINITIONS:
            at.selectbox(key="position").select(role).run()
            at.slider(key="minute").set_value(90).run()
            for view in ("Match so far", "Last 15 minutes"):
                at.radio(key="window_view").set_value(view).run()
                start = 0 if view == "Match so far" else 75
                for audience in ("Fan", "Broadcaster", "Expert"):
                    with self.subTest(role=role, view=view, audience=audience):
                        at.radio(key="audience").set_value(audience).run()
                        self.assert_healthy(at)
                        player = next(s.value for s in at.selectbox if s.label == "Player")
                        report = analyze_role_player(data, player, start, 90)
                        self.assertEqual(at.metric[0].value, str(report["action_sequences"]))
                        self.assertIn(f"minutes ({start}, 90]", html(at))
                        self.assertIn("schematic", html(at))
                        if audience == "Expert":
                            rates = next(df.value for df in at.dataframe if "Per 100 sequences" in df.value.columns)
                            self.assertEqual(rates["Count"].tolist(), [m["count"] for m in report["measurements"]])
                        if audience == "Broadcaster":
                            self.assertEqual(len(at.code), 1)

    def test_model_requires_click_and_old_result_is_hidden_after_context_changes(self):
        provider = Mock(side_effect=lambda payload: {"lead": payload["comparisons"][0]["id"], "support": None})
        with patch("pl_dna.microsoft_provider.create_provider_from_env", return_value=provider) as factory:
            at = self.app()
            at.radio(key="insight_source").set_value("Microsoft AI").run()
            factory.assert_not_called()
            at.button(key="generate_match_analysis").click().run()
            self.assert_healthy(at)
            self.assertEqual(provider.call_count, 1)
            self.assertTrue(any("Microsoft AI chose" in c.value for c in at.caption))
            at.radio(key="audience").set_value("Broadcaster").run()
            at.slider(key="minute").set_value(1).run()
            self.assert_healthy(at)
            self.assertEqual(provider.call_count, 1)
            self.assertFalse(any("Microsoft AI chose" in c.value for c in at.caption))
            self.assertIn("Insufficient sample", html(at))
            self.assertNotIn('role="meter"', html(at))
            at.selectbox(key="insight_language").select("Spanish").run()
            self.assertTrue(any("currently available in English" in c.value for c in at.info))

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
