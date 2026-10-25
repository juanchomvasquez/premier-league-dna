"""Read-only public match/player snapshots. No credentials or invented events.

These are undocumented website data surfaces, not a contracted live-data API.
Errors are surfaced; no alternate hosts, access-control workarounds or retries.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from urllib.request import urlopen

SITE = 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1'
CORE = 'https://sports.core.api.espn.com/v2/sports/soccer/leagues/eng.1'
PL = 'https://sdp-prem-prod.premier-league-prod.pulselive.com/api'

FIELDS = {
    'passes': ('Passes attempted', 'totalPasses', 'totalPasses'),
    'shots': ('Shots', 'totalShots', 'totalShots'),
    'takeons': ('Successful take-ons', 'wonContest', 'successfulDribbles'),
    'tackles': ('Tackles attempted', 'totalTackles', 'totalTackles'),
    'interceptions': ('Interceptions', 'interceptions', 'interceptions'),
    'long_passes': ('Completed long passes', 'accurateLongBalls', 'successfulLongPasses'),
    'clearances': ('Clearances', 'totalClearance', 'totalClearances'),
    'aerials': ('Aerial duels won', 'aerialsWon', 'aerialDuelsWon'),
    'shot_assists': ('Shot-assisting passes', 'shotAssists', 'keyPassesAttemptAssists'),
    'goals': ('Goals', 'totalGoals', 'goals'),
    'assists': ('Goal assists', 'goalAssists', 'goalAssists'),
    'box_touches': ('Touches in the opposition box', 'touchesInOppBox', 'totalTouchesInOppositionBox'),
    'recoveries': ('Ball recoveries', 'ballRecovery', 'recoveries'),
    'saves': ('Saves', 'saves', 'savesMade'),
    'conceded': ('Goals conceded', 'goalsConceded', 'goalsConceded'),
    'punches': ('Goalkeeper punches', 'punches', 'punches'),
}
ROLE_METRICS = {
    'GK': ['saves', 'conceded', 'punches', 'passes', 'long_passes'],
    'CB': ['clearances', 'tackles', 'interceptions', 'aerials', 'long_passes'],
    'FB': ['passes', 'long_passes', 'tackles', 'interceptions', 'takeons'],
    'CDM': ['passes', 'tackles', 'interceptions', 'recoveries', 'long_passes'],
    'CM': ['passes', 'box_touches', 'tackles', 'interceptions', 'long_passes'],
    'CAM': ['box_touches', 'takeons', 'passes', 'assists', 'long_passes'],
    'WING': ['goals', 'assists', 'takeons', 'passes', 'box_touches'],
    'ST': ['goals', 'assists', 'takeons', 'passes', 'box_touches'],
}
ROLE_LABELS = {'GK': 'Goalkeeper', 'CB': 'Centre-back', 'FB': 'Full-back',
    'CDM': 'Defensive midfield', 'CM': 'Central midfield', 'CAM': 'Attacking midfield',
    'WING': 'Wing', 'ST': 'Striker'}


def numeric_id(value):
    text = str(value)
    if not text.isascii() or not text.isdecimal() or not 1 <= len(text) <= 12:
        raise ValueError('Invalid source identifier.')
    return text


def fetch_json(url, transport=None):
    if not url.startswith((SITE+'/', CORE+'/', PL+'/')):
        raise ValueError('Unsupported source URL.')
    send = urlopen if transport is None else transport
    with send(url, timeout=20) as response:
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Source response exceeds the permitted size.')
        metadata = {'url': url, 'checked_at': datetime.now(timezone.utc).isoformat(),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'http_age_seconds': response.headers.get('Age'),
            'http_last_modified': response.headers.get('Last-Modified')}
    return json.loads(raw), metadata


def fetch_scoreboard(date, transport=None):
    if len(date) != 8 or not date.isdecimal():
        raise ValueError('Choose a YYYYMMDD date.')
    datetime.strptime(date, '%Y%m%d')
    return fetch_json(SITE+'/scoreboard?dates='+date, transport)


def fetch_summary(match_id, transport=None):
    return fetch_json(SITE+'/summary?event='+numeric_id(match_id), transport)


def fetch_player_stats(match_id, team_id, player_id, transport=None):
    match_id, team_id, player_id = map(numeric_id, (match_id, team_id, player_id))
    return fetch_json(f'{CORE}/events/{match_id}/competitions/{match_id}/competitors/{team_id}/roster/{player_id}/statistics/0?lang=en&region=us', transport)


def count(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and value >= 0 else None


def normalize_player(raw, metadata):
    stats = {}
    for group in raw.get('splits', {}).get('categories', []):
        for field in group.get('stats', []):
            name = field.get('name')
            if name in stats:
                raise ValueError('Duplicate player-stat field.')
            stats[name] = field.get('value')
    values = {key: count(stats.get(source_key)) for key, (_, source_key, _) in FIELDS.items()}
    warnings = []
    excluded = []
    # Source consistency checks. Do not silently fix or merge disputed fields.
    if all(count(stats.get(k)) is not None for k in ('totalPasses', 'accuratePasses', 'inaccuratePasses')):
        if abs(stats['totalPasses']-stats['accuratePasses']-stats['inaccuratePasses']) > .01:
            warnings.append('Source pass attempts do not reconcile to completed + incomplete passes; passing is excluded from the fit.')
            excluded.append('passes')
    if all(count(stats.get(k)) is not None for k in ('totalShots', 'attemptsInBox', 'attemptsOutBox')):
        if abs(stats['totalShots']-stats['attemptsInBox']-stats['attemptsOutBox']) > .01:
            warnings.append('Source shot totals do not reconcile to inside-box + outside-box attempts; shots are excluded from the fit.')
            excluded.append('shots')
    execution = {}
    for label, numerator, denominator in [('Pass completion','accuratePasses','totalPasses'),
            ('Tackles won','effectiveTackles','totalTackles'), ('Duels won','duelsWon','duels')]:
        won, attempted = count(stats.get(numerator)), count(stats.get(denominator))
        if won is not None and attempted is not None and attempted > 0 and won <= attempted:
            if label=='Pass completion' and 'passes' in excluded:
                continue
            execution[label] = {'successful': won, 'attempted': attempted, 'percentage':100*won/attempted}
    return {'minutes': count(stats.get('minutes')), 'counts': values, 'execution': execution,
        'goals': count(stats.get('totalGoals')), 'assists': count(stats.get('goalAssists')),
        'source': metadata, 'warnings': warnings, 'excluded_metrics': excluded}


def normalize_reference(raw, metadata, season, role, inspiration):
    if season < 2006:
        raise ValueError('Comparable detailed fields are not consistently covered before 2006/07; no historical rates are inferred.')
    stats = raw.get('stats', {})
    minutes = count(stats.get('timePlayed'))
    if not minutes:
        raise ValueError('Historical reference has no positive playing-time denominator.')
    return {'player': raw['player']['name'], 'id': str(raw['player']['id']),
        'role': role, 'inspiration': inspiration, 'season': f'{season}/{str(season+1)[-2:]}',
        'minutes': minutes, 'appearances': count(stats.get('appearances')),
        'counts': {key: count(stats.get(pl_key)) for key, (_, _, pl_key) in FIELDS.items()},
        'source': metadata}


def match_info(summary):
    header = summary['header']
    if header.get('league', {}).get('slug', 'eng.1') != 'eng.1':
        raise ValueError('This source is not a Premier League fixture.')
    if int(header.get('season', {}).get('year', 0)) != 2026:
        raise ValueError('This view accepts only the 2026/27 season.')
    competition = header['competitions'][0]
    status = competition['status']
    state = status['type']['state']
    if state not in ('pre', 'in', 'post'):
        raise ValueError('Unknown match state.')
    teams = sorted(competition['competitors'], key=lambda t: t['homeAway'] != 'home')
    return {'id': str(header['id']), 'name': teams[0]['team']['displayName']+' vs '+teams[1]['team']['displayName'], 'date': competition['date'],
        'state': state, 'status': status['type']['description'],
        'clock': status.get('displayClock', ''), 'period': status.get('period'),
        'home': teams[0]['team']['displayName'], 'away': teams[1]['team']['displayName'],
        'score': f"{teams[0].get('score', '—')}–{teams[1].get('score', '—')}",
        'source_page': f'https://www.espn.com/soccer/matchstats/_/gameId/{header["id"]}'}


def roster_players(summary):
    rows = []
    for team in summary.get('rosters', []):
        for entry in team.get('roster', []):
            if not entry.get('starter') and not entry.get('subbedIn'):
                continue
            athlete = entry['athlete']
            rows.append({'id': str(athlete['id']), 'name': athlete['displayName'],
                'team_id': str(team['team']['id']), 'team': team['team']['displayName'],
                'source_position': entry.get('position', {}).get('displayName', '')})
    return rows
