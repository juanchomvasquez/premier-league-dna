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


# Selected seasons: all values in a record belong to the same PL campaign.
SEASON_FACTS.update({'Schmeichel-inspired': {'player': 'Peter Schmeichel',
                         'club': 'Manchester United',
                         'season': '1995/96',
                         'appearances': 36,
                         'goals': None,
                         'assists': None,
                         'selection': 'Selected for his Premier League Player of the Season campaign.',
                         'sources': [{'title': 'Premier League · 1995/96 review',
                                      'url': 'https://www.premierleague.com/en/news/59007'},
                                     {'title': 'StatMuse · Schmeichel season clean sheets and appearances',
                                      'url': 'https://www.statmuse.com/fc/ask/peter-schmeichel-clean-sheets-career?l=eu5'}],
                         'coverage_note': 'Clean sheets follow StatMuse. Goals conceded are withheld because '
                                          'checked providers differ. Clean sheets depend on the team as well '
                                          'as the goalkeeper. No compatible historical wheel rates are '
                                          'loaded.',
                         'clean_sheets': 18,
                         'goals_conceded': None,
                         'display_fields': [('appearances', 'PL appearances'),
                                            ('clean_sheets', 'PL clean sheets'),
                                            ('goals_conceded', 'Goals conceded')]},
 'Cech-inspired': {'player': 'Petr Čech',
                   'club': 'Chelsea',
                   'season': '2004/05',
                   'appearances': 35,
                   'goals': None,
                   'assists': None,
                   'selection': 'Selected for his record 24-clean-sheet Premier League season.',
                   'sources': [{'title': 'Premier League · Cech 2004/05 record season',
                                'url': 'https://www.premierleague.com/es/news/3251101'}],
                   'coverage_note': 'Clean sheets do not measure shot difficulty or distribution. These are '
                                    'individual appearance-based season totals. No compatible historical '
                                    'wheel rates are loaded.',
                   'clean_sheets': 24,
                   'goals_conceded': 13,
                   'display_fields': [('appearances', 'PL appearances'),
                                      ('clean_sheets', 'PL clean sheets'),
                                      ('goals_conceded', 'Goals conceded')]},
 'Alisson-inspired': {'player': 'Alisson',
                      'club': 'Liverpool',
                      'season': '2018/19',
                      'appearances': 38,
                      'goals': None,
                      'assists': None,
                      'selection': 'Selected for his first Premier League Golden Glove season.',
                      'sources': [{'title': 'Premier League · 2018/19 Golden Glove',
                                   'url': 'https://www.premierleague.com/en/news/1215933/alisson-wins-201819-premier-league-golden-glove-award'},
                                  {'title': 'StatMuse · Alisson season appearances and goals conceded',
                                   'url': 'https://www.statmuse.com/fc/ask/alisson-most-clean-sheets-in-a-premier-league-season'}],
                      'coverage_note': 'The PL confirms 21 clean sheets; appearances and goals conceded '
                                       'follow StatMuse. Clean sheets depend on the whole team. No '
                                       'compatible historical wheel rates are loaded.',
                      'clean_sheets': 21,
                      'goals_conceded': 22,
                      'display_fields': [('appearances', 'PL appearances'),
                                         ('clean_sheets', 'PL clean sheets'),
                                         ('goals_conceded', 'Goals conceded')]},
 'Terry-inspired': {'player': 'John Terry',
                    'club': 'Chelsea',
                    'season': '2004/05',
                    'appearances': 36,
                    'goals': 3,
                    'assists': 1,
                    'selection': 'Selected for Chelsea’s record defensive title-winning season, not a claim '
                                 'that one player caused the team record.',
                    'sources': [{'title': 'UEFA · Chelsea 2005 title winners',
                                 'url': 'https://www.uefa.com/news/0221-0e908247b46c-2ddcbd6061e9-1000--snap-shot-chelsea-s-2005-title-winners-a-decade-on/'},
                                {'title': 'StatMuse · Terry 2004/05 season',
                                 'url': 'https://www.statmuse.com/fc/ask?q=john+terry+in+chelsea+in+04-05+pl'}],
                    'coverage_note': 'Individual clean-sheet credits and assists follow StatMuse; clean '
                                     'sheets use provider appearance-credit rules and are not a measure of '
                                     'isolated defensive ability. No compatible historical wheel rates are '
                                     'loaded.',
                    'clean_sheets': 25,
                    'display_fields': [('appearances', 'PL appearances'),
                                       ('clean_sheets', 'PL clean sheets'),
                                       ('goals', 'PL goals')]},
 'Vidic-inspired': {'player': 'Nemanja Vidić',
                    'club': 'Manchester United',
                    'season': '2008/09',
                    'appearances': 34,
                    'goals': 4,
                    'assists': 1,
                    'selection': 'Selected for his Premier League Player of the Season campaign.',
                    'sources': [{'title': 'Premier League · Player of the Season winners',
                                 'url': 'https://www.premierleague.com/en/news/3489431'},
                                {'title': 'StatMuse · Vidic season clean sheets',
                                 'url': 'https://www.statmuse.com/fc/ask/vidic-total-clean-sheets'}],
                    'coverage_note': 'Season totals follow StatMuse. Clean sheets use provider '
                                     'appearance-credit rules and depend on team performance. No compatible '
                                     'historical wheel rates are loaded.',
                    'clean_sheets': 23,
                    'display_fields': [('appearances', 'PL appearances'),
                                       ('clean_sheets', 'PL clean sheets'),
                                       ('goals', 'PL goals')]},
 'Van Dijk-inspired': {'player': 'Virgil van Dijk',
                       'club': 'Liverpool',
                       'season': '2018/19',
                       'appearances': 38,
                       'goals': 4,
                       'assists': 2,
                       'selection': 'Selected for his Premier League Player of the Season campaign.',
                       'sources': [{'title': 'Premier League · Van Dijk season award',
                                    'url': 'https://www.premierleague.com/en/news/1214766'},
                                   {'title': 'StatMuse · Van Dijk 2018/19 season',
                                    'url': 'https://www.statmuse.com/fc/ask/van-dijk-2019'}],
                       'coverage_note': 'Season totals follow StatMuse. Clean sheets use provider '
                                        'appearance-credit rules and do not isolate individual defensive '
                                        'ability. No compatible historical wheel rates are loaded.',
                       'clean_sheets': 20,
                       'display_fields': [('appearances', 'PL appearances'),
                                          ('clean_sheets', 'PL clean sheets'),
                                          ('goals', 'PL goals')]},
 'Ashley Cole-inspired': {'player': 'Ashley Cole',
                          'club': 'Chelsea',
                          'season': '2009/10',
                          'appearances': 27,
                          'goals': 4,
                          'assists': 3,
                          'selection': 'Selected Chelsea-era scoring peak in a title-winning season; not a '
                                       'universal defensive peak.',
                          'sources': [{'title': 'StatMuse · Cole Chelsea season totals',
                                       'url': 'https://www.statmuse.com/fc/ask/chelsea-ashley'}],
                          'coverage_note': 'Goals and assists do not measure defensive positioning or '
                                           'recovery runs. No compatible historical wheel rates are loaded.'},
 'Kyle Walker-inspired': {'player': 'Kyle Walker',
                          'club': 'Manchester City',
                          'season': '2017/18',
                          'appearances': 32,
                          'goals': 0,
                          'assists': 6,
                          'selection': 'Selected for his six-assist contribution to Manchester City’s '
                                       '100-point title season.',
                          'sources': [{'title': 'StatMuse · Walker Manchester City seasons',
                                       'url': 'https://www.statmuse.com/fc/ask/kyle-walker-stats-with-man-city?l=fc'}],
                          'coverage_note': 'Zero goals is a recorded value, not missing data. Assist totals '
                                           'do not measure recovery speed or defensive coverage. No '
                                           'compatible historical wheel rates are loaded.'},
 'Alexander-Arnold-inspired': {'player': 'Trent Alexander-Arnold',
                               'club': 'Liverpool',
                               'season': '2019/20',
                               'appearances': 38,
                               'goals': 4,
                               'assists': 13,
                               'selection': 'Selected for his 13-assist title-winning season and Premier '
                                            'League Young Player award.',
                               'sources': [{'title': 'Premier League · Alexander-Arnold 2019/20 totals',
                                            'url': 'https://www.premierleague.com/en/news/1747985'},
                                           {'title': 'Premier League · Young Player of the Season',
                                            'url': 'https://www.premierleague.com/en/news/1750635'}],
                               'coverage_note': 'Assists are not equivalent to crosses, chances created or '
                                                'progressive passes. No compatible historical wheel rates '
                                                'are loaded.'},
 'Kante-inspired': {'player': 'N’Golo Kanté',
                    'club': 'Chelsea',
                    'season': '2016/17',
                    'appearances': 35,
                    'goals': 1,
                    'assists': 1,
                    'selection': 'Selected for his Chelsea Premier League Player of the Season campaign.',
                    'sources': [{'title': 'Premier League · Kante season award',
                                 'url': 'https://www.premierleague.com/en/news/397433'},
                                {'title': 'StatMuse · Kante 2016/17 appearances',
                                 'url': 'https://www.statmuse.com/fc/ask?q=kante+16%2F17'},
                                {'title': 'StatMuse · 2016/17 tackles',
                                 'url': 'https://www.statmuse.com/fc/ask?q=most+tackles+premier+league+2016%2F17'},
                                {'title': 'StatMuse · Kante season interceptions',
                                 'url': 'https://www.statmuse.com/fc/ask/kante-interception'}],
                    'coverage_note': 'Tackles are total tackles, not successful tackles. Interceptions and '
                                     'tackles are separate provider-defined counts; they are not converted '
                                     'to the wheel’s action-sequence units. No compatible historical wheel '
                                     'rates are loaded.',
                    'tackles': 127,
                    'interceptions': 82,
                    'display_fields': [('appearances', 'PL appearances'),
                                       ('tackles', 'Total tackles'),
                                       ('interceptions', 'Interceptions')]},
 'Makelele-inspired': {'player': 'Claude Makélélé',
                       'club': 'Chelsea',
                       'season': '2004/05',
                       'appearances': 36,
                       'goals': 1,
                       'assists': 2,
                       'selection': 'Selected for his holding-midfield role in Chelsea’s 2004/05 title team, '
                                    'not for an attacking-statistical peak.',
                       'sources': [{'title': 'Premier League · Makelele’s role',
                                    'url': 'https://www.premierleague.com/en/news/2287373'},
                                   {'title': 'StatMuse · Makelele Chelsea seasons',
                                    'url': 'https://www.statmuse.com/fc/ask/makelele-stats-with-chelsea?l=pl'}],
                       'coverage_note': 'Appearances, goals and assists follow StatMuse. These totals do not '
                                        'validate his defensive shielding or positioning; those metrics are '
                                        'unavailable. No compatible historical wheel rates are loaded.'},
 'Rodri-inspired': {'player': 'Rodri',
                    'club': 'Manchester City',
                    'season': '2023/24',
                    'appearances': 34,
                    'goals': 8,
                    'assists': 9,
                    'selection': 'Selected for his title-winning all-round season, included in Opta’s team '
                                 'of the season.',
                    'sources': [{'title': 'Opta Analyst · 2023/24 team of the season',
                                 'url': 'https://theanalyst.com/articles/premier-league-team-of-the-season-2023-24'}],
                    'coverage_note': 'All displayed totals follow Opta. Completed passes are not progressive '
                                     'passes; season totals cannot be compared directly to a selected match '
                                     'window. No compatible historical wheel rates are loaded.',
                    'completed_passes': 3359,
                    'display_fields': [('appearances', 'PL appearances'),
                                       ('completed_passes', 'Completed passes'),
                                       ('assists', 'PL assists')]},
 'Ozil-inspired': {'player': 'Mesut Özil',
                   'club': 'Arsenal',
                   'season': '2015/16',
                   'appearances': 35,
                   'goals': 6,
                   'assists': 19,
                   'selection': 'Selected for his 19-assist Premier League creative peak.',
                   'sources': [{'title': 'Opta Analyst · Most assists in a PL season',
                                'url': 'https://theanalyst.com/articles/most-assists-in-a-premier-league-season'},
                               {'title': 'Premier League · Ozil 2015/16 goals and assists',
                                'url': 'https://www.premierleague.com/ar/news/79521/kind-run-and-big-guns-return-favour-arsenal'},
                               {'title': 'StatMuse · Ozil 2015/16 appearances',
                                'url': 'https://www.statmuse.com/fc/ask?l=eu5&q=ozil+all+matches+15%2F16'}],
                   'coverage_note': 'Assists use the official PL/Opta total of 19 rather than StatMuse’s '
                                    'conflicting 18; StatMuse is used only for appearances. Assists are not '
                                    'chances created. No compatible historical wheel rates are loaded.'},
 'De Bruyne-inspired': {'player': 'Kevin De Bruyne',
                        'club': 'Manchester City',
                        'season': '2019/20',
                        'appearances': 35,
                        'goals': 13,
                        'assists': 20,
                        'selection': 'Selected for his 20-assist Premier League season and Player of the '
                                     'Season award.',
                        'sources': [{'title': 'Manchester City · De Bruyne 2019/20 season',
                                     'url': 'https://www.mancity.com/news/mens/kevin-de-bruyne-pfa-player-of-the-year-201920-63735180'},
                                    {'title': 'StatMuse · De Bruyne 2019/20 appearances',
                                     'url': 'https://www.statmuse.com/fc/ask?q=kevin+de+bruyne+2019%2F20'}],
                        'coverage_note': 'Goals and assists are confirmed by Manchester City; appearances '
                                         'follow StatMuse. This is a creative peak, not his highest-scoring '
                                         'season. No compatible historical wheel rates are loaded.'},
 'Ronaldo-inspired': {'player': 'Cristiano Ronaldo',
                      'club': 'Manchester United',
                      'season': '2007/08',
                      'appearances': 34,
                      'goals': 31,
                      'assists': 6,
                      'selection': 'Selected for his 31-goal Premier League Golden Boot season.',
                      'sources': [{'title': 'Premier League · Record season goal contributions',
                                   'url': 'https://www.premierleague.com/es/news/4261107/x'}],
                      'coverage_note': 'Scoring totals do not measure dribbling, acceleration or the full '
                                       'range of wing play. No compatible historical wheel rates are '
                                       'loaded.'},
 'Salah-inspired': {'player': 'Mohamed Salah',
                    'club': 'Liverpool',
                    'season': '2017/18',
                    'appearances': 36,
                    'goals': 32,
                    'assists': 10,
                    'selection': 'Selected for his 32-goal Premier League scoring peak, not his highest '
                                 'combined goals-and-assists season.',
                    'sources': [{'title': 'Premier League · Salah season records',
                                 'url': 'https://www.premierleague.com/en/news/4299108'}],
                    'coverage_note': 'A scoring-peak season is not necessarily the best season on every '
                                     'dimension of performance. No compatible historical wheel rates are '
                                     'loaded.'},
 'Shearer-inspired': {'player': 'Alan Shearer',
                      'club': 'Blackburn Rovers',
                      'season': '1994/95',
                      'appearances': 42,
                      'goals': 34,
                      'assists': 13,
                      'selection': 'Selected for his 34-goal Blackburn title-winning campaign. The club '
                                   'shown is the club for this season.',
                      'sources': [{'title': 'Premier League · Golden Boot winners',
                                   'url': 'https://www.premierleague.com/en/news/1206108'},
                                  {'title': 'StatMuse · Shearer season totals',
                                   'url': 'https://www.statmuse.com/fc/player/alan-shearer-179/career-stats'}],
                      'coverage_note': 'This was a 42-fixture league season. Raw totals are not adjusted to '
                                       'a 38-fixture season; appearances and assists follow StatMuse. No '
                                       'compatible historical wheel rates are loaded.'},
 'Henry-inspired': {'player': 'Thierry Henry',
                    'club': 'Arsenal',
                    'season': '2003/04',
                    'appearances': 37,
                    'goals': 30,
                    'assists': 6,
                    'selection': 'Selected for his 30-goal scoring peak during Arsenal’s unbeaten title '
                                 'season; not his 2002/03 assist peak.',
                    'sources': [{'title': 'Premier League · 2003/04 review',
                                 'url': 'https://www.premierleague.com/en/news/59016'},
                                {'title': 'StatMuse · Henry 2003/04 season',
                                 'url': 'https://www.statmuse.com/fc/ask/henry-03-04'}],
                    'coverage_note': 'Appearances and assists follow StatMuse. All values belong to 2003/04; '
                                     'his 20-assist 2002/03 season is not mixed into this card. No '
                                     'compatible historical wheel rates are loaded.'},
 'Rooney-inspired': {'player': 'Wayne Rooney',
                     'club': 'Manchester United',
                     'season': '2011/12',
                     'appearances': 34,
                     'goals': 27,
                     'assists': 4,
                     'selection': 'Selected for his highest-scoring Premier League season, with 27 goals.',
                     'sources': [{'title': 'StatMuse · Rooney 2011/12 season',
                                  'url': 'https://www.statmuse.com/fc/ask?q=wayne+rooney+11-12'}],
                     'coverage_note': 'Scoring totals do not establish a measured link-up or all-round '
                                      'playing-style benchmark. No compatible historical wheel rates are '
                                      'loaded.'}})

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
    accent, tint = ({"Blackburn Rovers": ("#4c8dff", "#142b52")}.get(club)
                    or CLUB_COLOURS.get(club, ("#b69aff", "#221c36")))
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
                    record.get("display_fields", (("appearances", "PL appearances"), ("goals", "PL goals"), ("assists", "PL assists"))))
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
