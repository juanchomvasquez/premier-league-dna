"""Historical facts must never become fabricated wheel or narrative inputs."""
import base64
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

from pl_dna.historical import SEASON_FACTS, season_facts, sourced_season_card, observed_wheel_svg
import test_dashboard


class HistoricalTests(unittest.TestCase):
    def test_facts_have_sources_and_unavailable_is_not_zero(self):
        for name in SEASON_FACTS:
            record = season_facts(name)
            self.assertEqual(record["competition"], "Premier League")
            self.assertFalse(record["similarity_ready"])
            self.assertEqual(record["comparable_wheel_metrics"], [])
            self.assertTrue(record["sources"])
            self.assertTrue(all(s["url"].startswith("https://") for s in record["sources"]))
        self.assertIsNone(season_facts("Gerrard-inspired")["assists"])
        self.assertIn("—", sourced_season_card("Gerrard-inspired", show_career=False))
        self.assertIsNone(season_facts("Unknown-inspired"))
        self.assertIn("SOURCE COVERAGE PENDING", sourced_season_card("Unknown-inspired"))
        # A consumer cannot change the shared source snapshot.
        record = season_facts("Lampard-inspired")
        record["goals"] = 999
        self.assertEqual(season_facts("Lampard-inspired")["goals"], 22)

    def test_complete_catalogue_and_position_specific_facts(self):
        from pl_dna.presentation import LEGEND_CLUBS
        self.assertEqual(set(SEASON_FACTS), set(LEGEND_CLUBS))
        self.assertEqual(len(SEASON_FACTS), 25)
        cech = season_facts("Cech-inspired")
        self.assertEqual((cech["appearances"], cech["clean_sheets"], cech["goals_conceded"]), (35, 24, 13))
        card = sourced_season_card("Cech-inspired")
        self.assertIn("PL clean sheets", card)
        self.assertNotIn("PL assists", card)
        self.assertIsNone(season_facts("Schmeichel-inspired")["goals_conceded"])
        self.assertIn("—", sourced_season_card("Schmeichel-inspired"))
        self.assertEqual(season_facts("Shearer-inspired")["club"], "Blackburn Rovers")
        self.assertEqual(season_facts("Fabregas-inspired")["club"], "Chelsea")
        self.assertEqual(season_facts('Keane-inspired')['season'],'1999/00')
        self.assertEqual(season_facts('Baines-inspired')['assists'],5)
        self.assertIsNone(season_facts('Bergkamp-inspired')['appearances'])
        for name in LEGEND_CLUBS:
            self.assertNotIn("SOURCE COVERAGE PENDING", sourced_season_card(name))

    def test_observed_only_wheel_never_draws_or_scales_against_a_hidden_reference(self):
        rows = [{"measurement": label, "count": 1, "observed_rate": 10, "reference_rate": 9999}
                for label in ("Shots", "Passes", "Recoveries")]
        svg = observed_wheel_svg(rows, "Example", 40, True)
        ET.fromstring(svg)
        self.assertIn('>40</text>', svg)
        self.assertNotIn("9999", svg)
        self.assertNotIn('stroke="#b69aff"', svg)
        self.assertNotIn("versus", svg)

    def test_default_app_displays_sourced_totals_without_claiming_historical_similarity(self):
        with patch("pl_dna.microsoft_provider.create_provider_from_env", new=Mock()) as provider:
            at = test_dashboard.DashboardTests().app()
            body = test_dashboard.html(at)
            self.assertIn("2009/10", body)
            self.assertIn("SOURCED SEASON FACTS", body)
            self.assertIn("22</strong>", body)
            self.assertIn("14</strong>", body)
            self.assertNotIn("Closest measured rate", body)
            self.assertFalse(at.checkbox(key="illustrative_overlay").value)
            image = at.get("image")[0].proto.imgs[0]
            svg = base64.b64decode(image.url.split(",", 1)[1]).decode()
            self.assertNotIn('stroke="#b69aff"', svg)
            at.slider(key="minute").set_value(90).run()
            self.assertEqual(list(at.exception), [])
            self.assertIn("22</strong>", test_dashboard.html(at))
            provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
