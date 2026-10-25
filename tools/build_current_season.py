"""Fetch a fixed, documented current-season sample and historical PL references.

python tools/build_current_season.py --cache-dir /tmp/pl-dna-current
Only selected numerical facts and provenance enter the bundle. Raw responses stay
in the local cache for audit. No match is selected by a computed blend score.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unicodedata
from zoneinfo import ZoneInfo
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pl_dna.season_feed import (PL, fetch_json, SITE, CORE, normalize_player,
    normalize_reference, match_info, roster_players, ROLE_METRICS)
from pl_dna.historical import season_facts

REFERENCES = [
    ('CM', 'Lampard-inspired', 2051, 2009),
    ('CM', 'Gerrard-inspired', 1814, 2008),
    ('CM', 'Scholes-inspired', 363, 2010),
    ('CAM', 'Fabregas-inspired', 17878, 2014),
    ('CAM', 'Ozil-inspired', 37605, 2015),
    ('CAM', 'Bergkamp-inspired', 1608, 1997),
    ('CB', 'Terry-inspired', 1718, 2014),
    ('CB', 'Vidic-inspired', 14965, 2010),
    ('CB', 'Rio Ferdinand-inspired', 2034, 2012),
    ('GK', 'Cech-inspired', 11334, 2013),
    ('GK', 'Van der Sar-inspired', 4058, 2008),
    ('GK', 'Schmeichel-inspired', 3952, 1995),
    ('FB', 'Ashley Cole-inspired', 3785, 2009),
    ('FB', 'Gary Neville-inspired', 1807, 2008),
    ('FB', 'Baines-inspired', 12745, 2012),
    ('CDM', 'Vieira-inspired', 1593, 2004),
    ('CDM', 'Makelele-inspired', 6083, 2006),
    ('CDM', 'Keane-inspired', 361, 1999),
    ('WING', 'Hazard-inspired', 42786, 2018),
    ('WING', 'Giggs-inspired', 3, 2008),
    ('WING', 'Bale-inspired', 36903, 2012),
    ('ST', 'Drogba-inspired', 12303, 2009),
    ('ST', 'Rooney-inspired', 13017, 2011),
    ('ST', 'Henry-inspired', 1619, 2006),
    ('ST', 'Shearer-inspired', 1, 1994),
]
TARGETS = [(401879256, 'Zion Suzuki', 'GK'),
           (401879262, 'Virgil van Dijk', 'CB'),
           (401879255, 'Antonee Robinson', 'FB'),
           (401878767, 'Moisés Caicedo', 'CDM'),
           (401879256, 'Enzo Fernández', 'CM'),
           (401879260, 'Bruno Fernandes', 'CAM'),
           (401879261, 'Diego Gómez', 'WING'),
           (401879262, 'Igor Thiago', 'ST')]


def plain(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name.casefold()) if unicodedata.category(c) != 'Mn').replace('ß', 'ss')


def build(cache):
    cache.mkdir(parents=True, exist_ok=True)
    def get(url):
        key = hashlib.sha256(url.encode()).hexdigest()
        path = cache/(key+'.json')
        meta = cache/(key+'.meta.json')
        if not path.exists():
            value, source = fetch_json(url)
            path.write_text(json.dumps(value))
            meta.write_text(json.dumps(source))
        value, source = json.loads(path.read_text()), json.loads(meta.read_text())
        source['canonical_sha256'] = hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        meta.write_text(json.dumps(source))
        return value, source
    def reference(spec):
        role, inspiration, pid, year = spec
        url=f'{PL}/v2/competitions/8/seasons/{year}/players/{pid}/stats'
        try:
            if year < 2006:
                raise ValueError('Detailed comparable fields are not consistently covered before 2006/07; no rates are inferred.')
            raw, source = get(url)
            r=normalize_reference(raw, source, year, role, inspiration)
            if r['minutes'] < 900 or sum(r['counts'][k] is not None for k in ROLE_METRICS[role]) < 3:
                raise ValueError('Too little playing time or too few shared fields for a usable season reference.')
            return r
        except (HTTPError,ValueError) as exc:
            if isinstance(exc,HTTPError) and exc.code!=404:
                raise
            facts=season_facts(inspiration) or {}
            return dict(unavailable=True,player=facts.get('player',inspiration.removesuffix('-inspired')),
                inspiration=inspiration,role=role,season=f'{year}/{str(year+1)[-2:]}',
                source_url=url,reason='Source returned HTTP 404 for this season.' if isinstance(exc,HTTPError) else str(exc))
    with ThreadPoolExecutor(max_workers=3) as ex:
        all_references = list(ex.map(reference, REFERENCES))
    references=[r for r in all_references if not r.get('unavailable')]
    unavailable=[r for r in all_references if r.get('unavailable')]
    sample_path=ROOT/'pl_dna/data/cdm_match_samples.json'
    if sample_path.exists():
        samples=json.loads(sample_path.read_text())['references']
        replacements={r['inspiration'] for r in samples}
        references=[r for r in references if r['inspiration'] not in replacements]+samples
        unavailable=[r for r in unavailable if r['inspiration'] not in replacements]
    def match(mid):
        raw, source = get(f'{SITE}/summary?event={mid}')
        return mid, (raw, source)
    with ThreadPoolExecutor(max_workers=3) as ex:
        summaries = dict(ex.map(match, sorted({t[0] for t in TARGETS})))
    targets = {}
    for mid, name, role in TARGETS:
        summary, summary_source = summaries[mid]
        candidates = [p for p in roster_players(summary) if plain(p['name']) == plain(name)]
        if len(candidates) != 1:
            raise ValueError(f'Missing or ambiguous selected player: {name}, {mid}')
        player = candidates[0]
        url = f'{CORE}/events/{mid}/competitions/{mid}/competitors/{player["team_id"]}/roster/{player["id"]}/statistics/0?lang=en&region=us'
        raw, source = get(url)
        targets[f'{mid}:{player["id"]}'] = dict(player=player, role=role,
            fixture=match_info(summary), summary_source=summary_source,
            snapshot=normalize_player(raw, source))
    official, official_source = get(PL+'/v2/matches?competition=8&season=2026&period=FullTime&_limit=100&_sort=kickoff:desc&kickoff%3C2026-10-25')
    def club(name):
        return plain(name.replace('&','and').replace('AFC ',''))
    for entry in targets.values():
        f = entry['fixture']
        candidates = [m for m in official['data'] if club(m['homeTeam']['name'])==club(f['home']) and
            club(m['awayTeam']['name'])==club(f['away']) and
            datetime.strptime(m['kickoff'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('Europe/London')).astimezone(timezone.utc).date().isoformat()==f['date'][:10]]
        if len(candidates)!=1:
            raise ValueError('Selected fixture does not match the official Premier League results list.')
        m=candidates[0]
        if f"{m['homeTeam']['score']}–{m['awayTeam']['score']}" != f['score']:
            raise ValueError('Fixture score differs between the Premier League and ESPN sources.')
        entry['official_fixture_id']=m['matchId']
        entry['fixture_check']='Date, home/away teams and final score match the Premier League results feed.'
    assert len(targets)==8 and len({t['role'] for t in targets.values()})==8
    assert len({t['player']['team_id'] for t in targets.values()})==8
    result = dict(version=2, season='2026/27', checked_at=datetime.now(timezone.utc).isoformat(),
        selection='One sourced performance for each of eight position groups, from eight different clubs, across fixtures completed by 24 Oct 2026. The named examples were fixed before calculating their legend blends. This is a varied convenience sample, not a representative random league sample or a claim that every example is a standout.',
        references=references, unavailable_references=unavailable, targets=targets, official_fixture_source=official_source)
    out = ROOT/'pl_dna/data/current_season.json'
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'references': [(r['player'],r['season'],r['minutes']) for r in references],
        'targets': [(t['role'],t['player']['name'],t['player']['team'],t['fixture']['name'],t['snapshot']['minutes']) for t in targets.values()],
        'unavailable_references':unavailable}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache-dir', type=Path, required=True)
    build(parser.parse_args().cache_dir)
