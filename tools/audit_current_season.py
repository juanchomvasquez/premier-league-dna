"""Independently recount bundled numerical facts from cached source JSON using SQL.

python tools/audit_current_season.py ../source-audit-cache
Does not import the production normalization or comparison functions.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

root=Path(__file__).resolve().parents[1]
cache=Path(sys.argv[1])
study=json.loads((root/'pl_dna/data/current_season.json').read_text())
db=sqlite3.connect(':memory:')
fields={
 'passes':('totalPasses','totalPasses'), 'shots':('totalShots','totalShots'),
 'takeons':('wonContest','successfulDribbles'), 'tackles':('totalTackles','totalTackles'),
 'interceptions':('interceptions','interceptions'),
 'long_passes':('accurateLongBalls','successfulLongPasses'),
 'clearances':('totalClearance','totalClearances'), 'aerials':('aerialsWon','aerialDuelsWon'),
 'shot_assists':('shotAssists','keyPassesAttemptAssists'),
 'goals':('totalGoals','goals'), 'assists':('goalAssists','goalAssists'),
 'box_touches':('touchesInOppBox','totalTouchesInOppositionBox'),
 'recoveries':('ballRecovery','recoveries'), 'saves':('saves','savesMade'),
 'conceded':('goalsConceded','goalsConceded'), 'punches':('punches','punches')}

def source(metadata):
    key=hashlib.sha256(metadata['url'].encode()).hexdigest()
    data=json.loads((cache/(key+'.json')).read_text())
    canonical=json.dumps(data,sort_keys=True,separators=(',',':')).encode()
    assert hashlib.sha256(canonical).hexdigest()==metadata['canonical_sha256']
    return data

for r in study['references']:
    if r.get('reference_kind')=='match_sample':continue  # Recounted by audit_cdm_samples.py.
    a=source(r['source'])
    assert a['player']['id']==r['id']
    for key,(_,pl) in fields.items():
        v=db.execute('SELECT json_extract(?,?)',(json.dumps(a),'$.stats.'+pl)).fetchone()[0]
        assert v==r['counts'][key],(r['player'],key,v,r['counts'][key])
    assert a['stats']['timePlayed']==r['minutes']
    print('PASS reference',r['player'],r['season'],r['minutes'],'minutes')

official=source(study['official_fixture_source'])
official_by_id={m['matchId']:m for m in official['data']}
for entry in study['targets'].values():
    a=source(entry['snapshot']['source'])
    values=db.execute('''SELECT json_extract(s.value,'$.name'),json_extract(s.value,'$.value')
    FROM json_each(json_extract(?,'$.splits.categories')) c,
         json_each(json_extract(c.value,'$.stats')) s''',(json.dumps(a),)).fetchall()
    assert len(values)==len({k for k,v in values})
    values=dict(values)
    for key,(espn,_) in fields.items():
        assert values.get(espn)==entry['snapshot']['counts'][key],(entry['player']['name'],key)
    assert values.get('minutes')==entry['snapshot']['minutes']
    for label,(num,den) in {'Pass completion':('accuratePasses','totalPasses'),
                           'Tackles won':('effectiveTackles','totalTackles'),
                           'Duels won':('duelsWon','duels')}.items():
        if label in entry['snapshot'].get('execution',{}):
            fact=entry['snapshot']['execution'][label]
            assert fact['successful']==values[num] and fact['attempted']==values[den]
            assert abs(fact['percentage']-100*values[num]/values[den])<1e-8
    summary=source(entry['summary_source'])
    assert str(summary['header']['id'])==entry['fixture']['id']
    assert summary['header']['season']['year']==2026
    selected=[p for t in summary['rosters'] for p in t['roster'] if str(p['athlete']['id'])==entry['player']['id']]
    assert len(selected)==1 and selected[0]['athlete']['displayName']==entry['player']['name']
    m=official_by_id[entry['official_fixture_id']]
    assert f"{m['homeTeam']['score']}–{m['awayTeam']['score']}"==entry['fixture']['score']
    # Match-boxscore shot totals reconcile across all players, while the selected
    # player's detailed location breakdown may conflict. Preserve that warning.
    for team in summary['rosters']:
        total=sum(s['value'] for p in team['roster'] for s in p.get('stats',[]) if s['name']=='totalShots')
        team_total=next(float(s['displayValue']) for t in summary['boxscore']['teams'] if t['team']['id']==team['team']['id'] for s in t['statistics'] if s['name']=='totalShots')
        assert total==team_total,(entry['fixture']['id'],team['team']['id'],total,team_total)
    print('PASS performance',entry['player']['name'],entry['fixture']['id'],'and official fixture',entry['official_fixture_id'])
assert len({e['role'] for e in study['targets'].values()})==8
assert len({e['player']['team_id'] for e in study['targets'].values()})==8
print(f"PASS: {sum(r.get('reference_kind')!='match_sample' for r in study['references'])} reference seasons, {len(study['targets'])} performances across eight roles and clubs, cached digests, identities, minutes, execution facts and numerical fields; fixture scores agree with PL and team/player shot totals reconcile. CDM match samples are checked separately by audit_cdm_samples.py.")
print('LIMIT: detailed shot-location fields disagree, so shots are excluded from the blend. This audit does not establish full cross-provider definition equivalence or validate style similarity.')
