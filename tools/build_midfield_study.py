"""Build an explicitly limited PL event comparison from a pinned publisher snapshot.

python tools/build_midfield_study.py --cache-dir /tmp/pl-dna-cm
Raw events are cached outside the project and are not redistributed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pl_dna.recorded_events import player_profile, pooled_profile, DEFINITIONS

COMMIT = '4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
BASE = f'https://raw.githubusercontent.com/hudl/open-data/{COMMIT}/'
LEGENDS = {'Frank Lampard': [3749079, 3749276],
           'Steven Gerrard': [3749253, 3749448], 'Paul Scholes': [3749246]}
TARGETS = {3749431: ['Patrick Vieira', 'Gilberto Aparecido da Silva'],
           3749528: ['Gilberto Aparecido da Silva'],
           3749346: ['Gilberto Aparecido da Silva']}


def observed_by(events, minute):
    """At 45/90 include that half's added time; otherwise use elapsed match minute.

    A pass cannot count as a shot assist until its linked shot has been observed.
    Never remove or reinterpret other recorded pass fields.
    """
    selected = [e for e in events if e['period'] in (1, 2) and
                ((e['period'] == 1 and minute >= 45) or minute >= 90 or e['minute'] < minute)]
    shots = {e['id'] for e in selected if e['type']['name'] == 'Shot'}
    result = []
    for e in selected:
        if e['type']['name'] == 'Pass' and e['pass'].get('assisted_shot_id') not in shots:
            e = dict(e, **{'pass': {k: v for k, v in e['pass'].items() if k != 'assisted_shot_id'}})
        result.append(e)
    return result


def build(cache):
    cache.mkdir(parents=True, exist_ok=True)
    def get(local, remote):
        p = cache / local
        if not p.exists():
            p.write_bytes(urllib.request.urlopen(BASE + remote, timeout=60).read())
        return json.loads(p.read_text())
    metadata = get('matches.json', 'data/matches/2/44.json')
    index = {m['match_id']: m for m in metadata}
    mids = sorted(set(sum(LEGENDS.values(), []) + list(TARGETS)))
    events = {mid: get(f'{mid}.json', f'data/events/{mid}.json') for mid in mids}
    fixtures = {str(mid): dict(date=index[mid]['match_date'],
        match=f"{index[mid]['home_team']['home_team_name']} {index[mid]['home_score']}–{index[mid]['away_score']} {index[mid]['away_team']['away_team_name']}",
        source=BASE + f'data/events/{mid}.json',
        sha256=hashlib.sha256((cache / f'{mid}.json').read_bytes()).hexdigest()) for mid in mids}
    def identity(mid, name):
        ids = {e['player']['id'] for e in events[mid] if e.get('player', {}).get('name') == name}
        if len(ids) != 1:
            raise ValueError(f'Player missing or ambiguous: {name}, {mid}')
        return ids.pop()
    references = {}
    for name, matches in LEGENDS.items():
        profiles = [player_profile(events[mid], identity(mid, name)) for mid in matches]
        references[name] = dict(pooled_profile(profiles), match_ids=matches)
    targets = {}
    for mid, names in TARGETS.items():
        for name in names:
            pid = identity(mid, name)
            key = f'{mid}:{pid}'
            targets[key] = dict(player=name, match_id=mid, snapshots={str(end):
                pooled_profile([player_profile(observed_by(events[mid], end), pid)])
                for end in range(1, 91)})
    assert all(t['match_id'] not in sum(LEGENDS.values(), []) for t in targets.values())
    study = dict(version=1, source='StatsBomb Open Data', source_commit=COMMIT,
        source_license=BASE + 'LICENSE.pdf', metadata_sha256=hashlib.sha256((cache/'matches.json').read_bytes()).hexdigest(),
        references=references, targets=targets, fixtures=fixtures, definitions=DEFINITIONS,
        coverage='Selected 2003/04 Premier League matches against Arsenal: Lampard 2, Gerrard 2, Scholes 1. NOT season or career averages.',
        limitations=['One opponent, very small unequal reference samples; tactical and opponent selection effects are not removed.',
                    'The percentages are a descriptive least-squares fit within these three samples, not probabilities, ability ratings or validated career-style similarity.',
                    'All five axes use counts per 100 Pass+Shot+Dribble events, with equal weight per rate point. Metrics can overlap.',
                    'A poor fit or unstable weights can mean the target is outside this reference set. No claim that these three players span all midfield styles.',
                    'Future events do not enter earlier snapshots. Half-end selections include added time.',
                    'Counts are reproducible from the pinned source; no independent second-provider event audit has been performed.'])
    path = ROOT/'pl_dna/data/midfield_study.json'
    path.write_text(json.dumps(study, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(references=references, targets=list(targets), output=str(path)), indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache-dir', type=Path, required=True)
    build(ap.parse_args().cache_dir)
