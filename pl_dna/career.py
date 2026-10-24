"""Verified retired-player career headlines; never an event-profile input.

A club's share is PL appearances / total PL appearances, not minutes or all games.
Unknown players return no career block rather than an invented complete record.
"""
from html import escape

CAREERS = {
    'Lampard-inspired': dict(appearances=609,goals=177,assists=102,
        clubs=[('Chelsea',429),('West Ham United',148),('Manchester City',32)],
        sources=[('Premier League · career record','https://www.premierleague.com/en/players/2051/frank-lampard/overview?tab=stats'),('Chelsea · 429 PL appearances','https://www.chelseafc.com/en/news/article/chelseas-top-10-premier-league-appearance-makers'),('Premier League · Man City season appearances','https://www.premierleague.com/players/800'),('11v11 · West Ham PL appearances','https://www.11v11.com/teams/west-ham-united/tab/stats/option/appearances/')]),
    'Cech-inspired': dict(appearances=443,clean_sheets=202,titles=4,
        clubs=[('Chelsea',333),('Arsenal',110)],
        sources=[('Premier League · career clean-sheet record','https://www.premierleague.com/en/news/975480'),('Petr Cech · playing history and titles','https://www.petr-cech.net/playing-history/')]),
    'Henry-inspired': dict(appearances=258,goals=175,assists=74,clubs=[('Arsenal',258)],
        sources=[('Premier League · career record','https://www.premierleague.com/en/players/1619/thierry-henry/stats?co=1&se=-1')]),
    'Gerrard-inspired': dict(appearances=504,goals=120,assists=92,clubs=[('Liverpool',504)],
        sources=[('Premier League · Gerrard Hall of Fame','https://www.premierleague.com/en/news/2147433')]),
    'Scholes-inspired': dict(appearances=499,goals=107,assists=55,clubs=[('Manchester United',499)],
        sources=[('Premier League · Scholes Hall of Fame','https://www.premierleague.com/en/events/hall-of-fame/inductees/paul-scholes')]),
    'Drogba-inspired': dict(appearances=254,goals=104,assists=55,clubs=[('Chelsea',254)],
        sources=[('Premier League · Drogba retirement record','https://www.premierleague.com/en/news/916862')]),
    'Fabregas-inspired': dict(appearances=350,goals=50,assists=111,clubs=[('Arsenal',212),('Chelsea',138)],
        sources=[('Premier League · retirement career totals','https://www.premierleague.com/es/news/3563755'),('StatMuse · appearances by club, not assist totals','https://www.statmuse.com/fc/ask/cesc-fabregas-career-appearances-by-club?l=eu5')]),
}


# Additional sourced club records; coverage is explicit for changing careers.
CAREERS.update({'Shearer-inspired': {'appearances': 441,
                      'goals': 260,
                      'assists': 64,
                      'clubs': [('Newcastle United', 303), ('Blackburn Rovers', 138)],
                      'sources': [('Premier League · Shearer Hall of Fame',
                                   'https://www.premierleague.com/en/events/hall-of-fame/inductees/alan-shearer'),
                                  ('Newcastle · 303 PL appearances',
                                   'https://www.newcastleunited.com/en/news/alan-shearer-named-as-one-of-first-two-inductees-into-the-premier-league-hall-of-fame'),
                                  ('FBref · PL club subtotals',
                                   'https://fbref.com/en/players/438b3a51/Alan-Shearer')],
                      'checked_on': '24 Oct 2026',
                      'note': 'Southampton appearances predate the Premier League and are excluded.'},
 'Rooney-inspired': {'appearances': 491,
                     'goals': 208,
                     'assists': 103,
                     'clubs': [('Manchester United', 393), ('Everton', 98)],
                     'sources': [('Premier League · career totals',
                                  'https://www.premierleague.com/en/news/758950'),
                                 ('DC United · 393 Man Utd and 98 Everton league appearances',
                                  'https://www.dcunited.com/news/rooney-makes-500th-career-league-appearance')],
                     'checked_on': '24 Oct 2026',
                     'note': 'Both Everton spells are combined.'},
 'Schmeichel-inspired': {'appearances': 310,
                         'clean_sheets': 128,
                         'titles': 5,
                         'clubs': [('Manchester United', 252), ('Aston Villa', 29), ('Manchester City', 29)],
                         'checked_on': '24 Oct 2026',
                         'sources': [('Premier League · 310 appearances and 128 clean sheets',
                                      'https://www.premierleague.com/en/news/1653036'),
                                     ('Premier League · 252 Man Utd appearances',
                                      'https://www.premierleague.com/en/news/4160542'),
                                     ('Man City · 29 appearances',
                                      'https://www.mancity.com/news/womens/karen-bardsley-my-footballing-icon-63724270'),
                                     ('My Football Facts · PL club totals',
                                      'https://www.myfootballfacts.com/premier-league/all-time-premier-league/appearances/all-time-300-or-more-players-premier-league-appearances/')],
                         'note': 'Man Utd appearances before the Premier League began are excluded.'},
 'Terry-inspired': {'appearances': 492,
                    'goals': 41,
                    'assists': 12,
                    'clubs': [('Chelsea', 492)],
                    'sources': [('Premier League · career numbers',
                                 'https://www.premierleague.com/en/news/3972366')],
                    'checked_on': '24 Oct 2026',
                    'note': 'Aston Villa and Nottingham Forest appearances were outside the Premier League.'},
 'Vidic-inspired': {'appearances': 211,
                    'goals': 15,
                    'assists': 3,
                    'clubs': [('Manchester United', 211)],
                    'sources': [('Premier League · Hall of Fame nominee record',
                                 'https://www.premierleague.com/es/news/1653924')],
                    'checked_on': '24 Oct 2026'},
 'Ashley Cole-inspired': {'appearances': 385,
                          'goals': 15,
                          'assists': 31,
                          'clubs': [('Chelsea', 229), ('Arsenal', 156)],
                          'sources': [('Premier League · career totals',
                                       'https://www.premierleague.com/en/news/3936970'),
                                      ('Arsenal · 156 of 385 PL appearances',
                                       'https://www.arsenal.com/news/cole-inducted-into-premier-league-hall-of-fame-ab0m55H0Jm91')],
                          'checked_on': '24 Oct 2026'},
 'Kante-inspired': {'appearances': 227,
                    'goals': 12,
                    'assists': 17,
                    'clubs': [('Chelsea', 190), ('Leicester City', 37)],
                    'sources': [('Premier League · career totals',
                                 'https://www.premierleague.com/en/news/4061347'),
                                ('Premier League · 190 Chelsea appearances',
                                 'https://www.premierleague.com/en/news/4391327/the-biggest-transfers-between-premier-league-clubs')],
                    'checked_on': '24 Oct 2026'},
 'Makelele-inspired': {'appearances': 144,
                       'goals': 2,
                       'assists': 4,
                       'clubs': [('Chelsea', 144)],
                       'sources': [('Premier League · career totals',
                                    'https://www.premierleague.com/en/news/4061347')],
                       'checked_on': '24 Oct 2026'},
 'Ozil-inspired': {'appearances': 184,
                   'goals': 33,
                   'assists': 54,
                   'clubs': [('Arsenal', 184)],
                   'sources': [('Premier League · retirement career record',
                                'https://www.premierleague.com/en/news/3118777')],
                   'checked_on': '24 Oct 2026'},
 'Ronaldo-inspired': {'appearances': 236,
                      'goals': 103,
                      'assists': 37,
                      'clubs': [('Manchester United', 236)],
                      'sources': [('Premier League · career comparison',
                                   'https://www.premierleague.com/en/news/4282776'),
                                  ('Premier League · departure totals',
                                   'https://www.premierleague.com/es/news/2915108')],
                      'checked_on': '24 Oct 2026',
                      'note': 'Both Manchester United spells are combined.'},
 'Hazard-inspired': {'appearances': 245,
                     'goals': 85,
                     'assists': 54,
                     'clubs': [('Chelsea', 245)],
                     'sources': [('Premier League · retirement record',
                                  'https://www.premierleague.com/en/news/3733199')],
                     'checked_on': '24 Oct 2026'},
 'Alexander-Arnold-inspired': {'appearances': 259,
                               'goals': 18,
                               'assists': 64,
                               'clubs': [('Liverpool', 259)],
                               'sources': [('Opta · PL career',
                                            'https://theanalyst.com/players/4089/trent-alexander-arnold/career')],
                               'checked_on': '24 Oct 2026',
                               'coverage': 'PL career through 2024/25'},
 'De Bruyne-inspired': {'appearances': 288,
                        'goals': 72,
                        'assists': 119,
                        'clubs': [('Manchester City', 285), ('Chelsea', 3)],
                        'sources': [('Opta · PL club totals',
                                     'https://theanalyst.com/players/4141/kevin-de-bruyne/career'),
                                    ('Manchester City · 2025 annual report',
                                     'https://www.mancity.com/meta/media/acait4ww/mcfc_annual_report_2025.pdf')],
                        'checked_on': '24 Oct 2026',
                        'coverage': 'PL career through 2024/25'},
 'Kyle Walker-inspired': {'appearances': 446,
                          'goals': 8,
                          'assists': 38,
                          'clubs': [('Manchester City', 212),
                                    ('Tottenham Hotspur', 183),
                                    ('Burnley', 36),
                                    ('Aston Villa', 15)],
                          'sources': [('Opta · season-by-season competition and club record',
                                       'https://theanalyst.com/players/4145/kyle-walker/career')],
                          'checked_on': '24 Oct 2026',
                          'coverage': 'PL career through 2025/26',
                          'note': 'Includes Burnley 2025/26. Burnley 2026/27, QPR, Sheffield United and '
                                  'Northampton games shown by the source are outside the PL and excluded.'},
 'Van Dijk-inspired': {'appearances': 339,
                       'goals': 31,
                       'assists': 8,
                       'clubs': [('Liverpool', 272), ('Southampton', 67)],
                       'sources': [('Opta · season-by-season competition and club record',
                                    'https://theanalyst.com/players/4113/virgil-van-dijk/career')],
                       'checked_on': '24 Oct 2026',
                       'coverage': 'PL career through 2025/26',
                       'note': 'Excludes 2026/27 and Southampton development-team matches. Assists follow '
                               "this source's PL rows."},
 'Rodri-inspired': {'appearances': 196,
                    'goals': 23,
                    'assists': 21,
                    'clubs': [('Manchester City', 196)],
                    'sources': [('Opta · PL season totals',
                                 'https://theanalyst.com/players/4143/rodri/career')],
                    'checked_on': '24 Oct 2026',
                    'coverage': 'PL career through 2025/26'},
 'Salah-inspired': {'appearances': 328,
                    'goals': 193,
                    'assists': 94,
                    'clubs': [('Liverpool', 315), ('Chelsea', 13)],
                    'sources': [('Opta · Liverpool and Chelsea PL totals',
                                 'https://theanalyst.com/players/4100/mohamed-salah/career')],
                    'checked_on': '24 Oct 2026',
                    'coverage': 'PL career through 2025/26'},
 'Alisson-inspired': {'appearances': 255,
                      'clean_sheets': 103,
                      'titles': None,
                      'clubs': [('Liverpool', 255)],
                      'checked_on': '24 Oct 2026',
                      'coverage': 'PL career through 2025/26',
                      'sources': [('Opta · PL season-by-season appearances',
                                   'https://theanalyst.com/players/4096/alisson-becker/career'),
                                   ('PL · 2025/26 clean sheets', 'https://www.premierleague.com/en/news/4604681/202526-premier-league-golden-glove-which-goalkeeper-has-kept-the-most-clean-sheets'),
                                   ('NewsBytes · 95 through 2024/25', 'https://www.newsbytesapp.com/news/sports/alisson-becker-makes-his-300th-liverpool-appearance/story')],
                      'note': 'Clean sheets: 95 through 2024/25 plus 8 in 2025/26 = 103. Title total remains unavailable.'}})


# Club-inspired primary colours used consistently in the background and legend.
from pl_dna.presentation import CLUB_COLOURS
CAREER_COLOURS = dict(CLUB_COLOURS, **{
    'West Ham United': ('#7a263a', '#302239'),
    'Blackburn Rovers': ('#4c8dff', '#142b52'),
    'Everton': ('#1455d9', '#13274a'),
    'Aston Villa': ('#7a263a', '#302239'),
    'Leicester City': ('#0053a0', '#112a46'),
    'Tottenham Hotspur': ('#f4f5f7', '#1b2443'),
    'Burnley': ('#6c1d45', '#302239'),
    'Southampton': ('#d71920', '#3c202b'),
})


def club_shares(name):
    r=CAREERS.get(name)
    if r is None:return []
    if sum(n for _,n in r['clubs'])!=r['appearances']:
        raise ValueError('Club appearance totals do not reconcile to career total')
    return [(club,n,n/r['appearances']) for club,n in r['clubs']]


def club_background(name):
    """Exact horizontal colour widths, with a dark overlay for readable text."""
    from pl_dna.presentation import CLUB_COLOURS
    shares = club_shares(name)
    if not shares:
        return None
    colours = CAREER_COLOURS
    stops = []
    cumulative = 0.0
    for index, (club, _, share) in enumerate(shares):
        start = cumulative
        cumulative = 100.0 if index == len(shares) - 1 else cumulative + 100 * share
        colour = colours[club][0]
        stops.append(f'{colour} {start:.6f}% {cumulative:.6f}%')
    return ('linear-gradient(rgba(7,15,29,.78),rgba(7,15,29,.90)),'
            + 'linear-gradient(90deg,' + ','.join(stops) + ')')


def career_html(name):
    from pl_dna.presentation import CLUB_COLOURS
    r=CAREERS.get(name)
    if r is None:return ''
    shares=club_shares(name)
    colours = CAREER_COLOURS
    stripe=''.join(f'<span style="display:block;width:{100*share:.6f}%;background:{colours[club][0]};height:9px"></span>' for club,_,share in shares)
    clubs=' · '.join(f'{escape(club)} {n} ({100*share:.1f}%)' for club,n,share in shares)
    fields=(('appearances','PL appearances'),('clean_sheets','PL clean sheets'),('titles','PL titles')) if 'clean_sheets' in r else (('appearances','PL appearances'),('goals','PL goals'),('assists','PL assists'))
    facts=''.join(f'<div class="season-fact"><strong>{r[key] if r.get(key) is not None else "—"}</strong><span>{label}</span></div>' for key,label in fields)
    links=''.join(f'<li><a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{escape(title)}</a></li>' for title,url in r['sources'])
    coverage = r.get('coverage', 'Complete recorded PL career')
    note = r.get('note', '')
    checked = r.get('checked_on', '23 Oct 2026')
    return ('<div class="eyebrow">PREMIER LEAGUE CAREER · SOURCE SNAPSHOT</div>'
            f'<p class="dna-note">{escape(coverage)}</p>'
            f'<div class="season-facts">{facts}</div><div style="display:flex;border-radius:8px;overflow:hidden;margin:14px 0">{stripe}</div>'
            f'<p class="dna-note">{clubs}</p><p class="dna-note">Club colour widths reflect shares of PL appearances, not playing minutes. Only clubs with PL appearances are included. Both spells at the same club are combined.</p>'
            f'<p class="dna-note">{escape(note)}</p><details><summary>Career sources · checked {escape(checked)}</summary><ul>{links}</ul></details>'
            '<p class="dna-note">Career achievements are not career event averages. They do not enter the comparison wheel.</p>')
