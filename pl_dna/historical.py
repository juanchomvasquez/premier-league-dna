"""Small, attributed PL season fact snapshots. Never used as similarity inputs.

Sourced facts have different definitions/units from the action-sequence wheel.
Missing values remain None; there is deliberately no index scoring function.
"""
from copy import deepcopy
from html import escape
import xml.etree.ElementTree as ET

CHECKED_ON = "2026-10-23"
CHELSEA_SOURCE = {
    "title": "Chelsea FC · PL seasons with 20+ goal contributions",
    "url": "https://www.chelseafc.com/en/news/article/chelsea-players-with-20-plus-goal-contributions-in-a-premier-league-season",
}

SEASON_FACTS = {
    "Lampard-inspired": {
        "player": "Frank Lampard", "club": "Chelsea", "season": "2009/10",
        "appearances": 36, "goals": 22, "assists": 14,
        "selection": "His highest-scoring Premier League season; a selected attacking peak, not a claim about every aspect of his game.",
        "sources": [CHELSEA_SOURCE],
        "coverage_note": "No comparable box-arrival, progressive-pass, carry or switch rates are loaded for this season.",
    },
    "Gerrard-inspired": {
        "player": "Steven Gerrard", "club": "Liverpool", "season": "2008/09",
        "appearances": 31, "goals": 16, "assists": None,
        "selection": "Selected for his Premier League scoring peak, confirmed in Liverpool FC's retrospective.",
        "sources": [
            {"title": "Liverpool FC · Gerrard's league scoring peak", "url": "https://www.liverpoolfc.com/news/first-team/162268-br-gerrard-didn-t-need-words-from-me"},
            {"title": "StatMuse · Gerrard 2008/09 appearances", "url": "https://www.statmuse.com/fc/ask/steven-gerrard-stats-in-2009?l=eu5"},
        ],
        "coverage_note": "Assist totals differ across the sources checked, so that field is withheld. No comparable wheel rates are loaded.",
    },
    "Scholes-inspired": {
        "player": "Paul Scholes", "club": "Manchester United", "season": "2002/03",
        "appearances": 33, "goals": 14, "assists": 3,
        "selection": "His highest-scoring PL season. This is an attacking peak, not a measured benchmark of his later deep-distributing role.",
        "sources": [
            {"title": "Premier League · Scholes Hall of Fame profile", "url": "https://www.premierleague.com/es/news/1653178"},
            {"title": "StatMuse · Scholes 2002/03 appearances and assists", "url": "https://www.statmuse.com/fc/ask?q=paul+scholes+stats+2002%2F03"},
        ],
        "coverage_note": "Appearances and assists follow StatMuse's season snapshot. Advanced pre-2006/07 coverage is limited; no passing-style benchmark is inferred.",
    },
    "Drogba-inspired": {
        "player": "Didier Drogba", "club": "Chelsea", "season": "2009/10",
        "appearances": 32, "goals": 29, "assists": 10,
        "selection": "Selected for his highest-scoring Premier League season.",
        "sources": [CHELSEA_SOURCE], "coverage_note": "Goal involvement totals do not measure target-forward or aerial playing style. No comparable wheel rates are loaded.",
    },
    "Hazard-inspired": {
        "player": "Eden Hazard", "club": "Chelsea", "season": "2018/19",
        "appearances": 37, "goals": 16, "assists": 15,
        "selection": "Selected for his Premier League peak in combined goals and assists.",
        "sources": [CHELSEA_SOURCE, {"title": "Chelsea FC · 2018/19 season statistics (32 starts + 5 substitute appearances)", "url": "https://www.chelseafc.com/en/news/article/europa-league-and-premier-league-stats-in-2018-19"}],
        "coverage_note": "Appearances use the contemporary Chelsea season report (32 starts + 5 substitute appearances). Season totals do not measure dribbling or carrying style. No comparable wheel rates are loaded.",
    },
    "Fabregas-inspired": {
        "player": "Cesc Fabregas", "club": "Chelsea", "season": "2014/15",
        "appearances": 34, "goals": 3, "assists": 18,
        "selection": "Selected Chelsea-era creative peak. This is not claimed to be his best season across all clubs or all measures.",
        "sources": [CHELSEA_SOURCE], "coverage_note": "Assists are not equivalent to chances created, through balls or final-third entries. No comparable wheel rates are loaded.",
    },
}


def season_facts(name):
    """Return a separate snapshot with explicit coverage rather than fake zeros."""
    record = SEASON_FACTS.get(name)
    if record is None:
        return None
    result = deepcopy(record)
    result.update(competition="Premier League", checked_on=CHECKED_ON,
                  comparable_wheel_metrics=[], similarity_ready=False)
    return result


def sourced_season_card(name):
    from pl_dna.presentation import LEGEND_CLUBS, CLUB_COLOURS
    record = season_facts(name)
    club = record["club"] if record else LEGEND_CLUBS.get(name, "Club not assigned")
    accent, tint = CLUB_COLOURS.get(club, ("#b69aff", "#221c36"))
    heading = name.removesuffix("-inspired") + " Index"
    opening = (f'<section class="dna-reference" style="border-top:4px solid {accent};background:linear-gradient(145deg,{tint},#101d30);">'
               '<div class="eyebrow">LEGEND SEASON / SOURCE CHECK</div>'
               f'<h3>{escape(heading)}</h3>')
    if record is None:
        return (opening + f'<p>{escape(club)}</p><div class="dna-status">SOURCE COVERAGE PENDING</div>'
                '<p>A historical season has not been loaded for this legend yet.</p>'
                '<p class="dna-note">The wheel shows only the selected synthetic performance. No historical reference values or index score are invented.</p></section>')
    facts = ''.join(f'<div class="season-fact"><strong>{record[key] if record[key] is not None else "—"}</strong>'
                    f'<span>{label}</span></div>' for key, label in
                    (("appearances", "PL appearances"), ("goals", "PL goals"), ("assists", "PL assists")))
    sources = ''.join(f'<li><a href="{escape(source["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(source["title"])}</a></li>' for source in record["sources"])
    return (opening + f'<p>{escape(record["player"])} · {escape(club)} · {record["season"]}</p>'
            '<div class="dna-status">SOURCED SEASON FACTS</div>'
            '<p class="dna-note">Full Premier League season totals · not the selected match window</p>'
            f'<div class="season-facts">{facts}</div><p>{escape(record["selection"])}</p>'
            f'<p class="dna-note">{escape(record["coverage_note"])}</p>'
            f'<ul class="season-sources">{sources}</ul><p class="dna-note">Source check: {CHECKED_ON}. '
            'Historical style index unavailable: compatible event rates have not been loaded.</p></section>')


def observed_wheel_svg(rows, player, scale_max, show_observed):
    """Only the synthetic shape; remove the fixture polygon and its legend claims."""
    from pl_dna.dna_wheel import radar_svg
    # Hidden fixture rates must not influence the observed-only chart scale.
    observed_rows = [dict(row, reference_rate=0) for row in rows]
    root = ET.fromstring(radar_svg(observed_rows, player, "", show_observed, scale_max))
    ns = "{http://www.w3.org/2000/svg}"
    for element in list(root):
        if element.tag == ns + "polygon" and element.get("stroke") == "#b69aff":
            root.remove(element)
        if element.tag == ns + "desc":
            element.text = f"{player}: selected synthetic performance only. Historical comparison unavailable. All axes use rates per 100 recorded sequences."
        if element.tag == ns + "text" and element.text == "PERFORMANCE SHAPE / DESIGN PREVIEW":
            element.text = "SELECTED PERFORMANCE / SYNTHETIC EVENTS"
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return ET.tostring(root, encoding="unicode")
