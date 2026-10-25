"""Independent SQL recount of the same source files, separate from profile code.

Usage: python tools/audit_recorded_study.py /tmp/pl-dna-events
This checks arithmetic, not the accuracy of the provider's event annotation.
"""
import json
from pathlib import Path
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[1]
cache=Path(sys.argv[1])
study=json.loads((ROOT/'pl_dna/data/recorded_study.json').read_text())
c=sqlite3.connect(':memory:')
c.execute('CREATE TABLE events(match_id INTEGER, value TEXT)')
for remote in study['source_sha256']:
    mid=int(Path(remote).stem)
    c.execute('INSERT INTO events SELECT ?,value FROM json_each(?)',(mid,(cache/f'{mid}.json').read_text()))
SQL='''WITH player AS (SELECT value FROM events WHERE json_extract(value,'$.player.name')=? AND json_extract(value,'$.period') IN (1,2))
SELECT
sum(json_extract(value,'$.type.name') IN ('Pass','Shot','Dribble')),
sum(CASE WHEN json_extract(value,'$.type.name')='Shot' AND coalesce(json_extract(value,'$.shot.type.name'),'')<>'Penalty' THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Dribble' AND json_extract(value,'$.dribble.outcome.name')='Complete' THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Pass' AND json_extract(value,'$.pass.assisted_shot_id') IS NOT NULL THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Pass' AND json_type(value,'$.pass.outcome') IS NULL AND json_extract(value,'$.pass.end_location[0]')>=102 AND json_extract(value,'$.pass.end_location[1]') BETWEEN 18 AND 62 AND NOT (json_extract(value,'$.location[0]')>=102 AND json_extract(value,'$.location[1]') BETWEEN 18 AND 62) THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Pass' AND json_type(value,'$.pass.outcome') IS NULL AND json_extract(value,'$.pass.end_location[0]')-json_extract(value,'$.location[0]')>=10 THEN 1 ELSE 0 END)
FROM player'''
for name in ('Thierry Henry','Jamie Vardy'):
    actual=c.execute(SQL,(name,)).fetchone()
    profile=study['reference'] if name=='Thierry Henry' else next(t for t in study['targets'].values() if t['player']==name)
    expected=(profile['actions'],*profile['counts'].values())
    assert actual==expected,(name,actual,expected)
    print('PASS',name,dict(zip(['actions',*profile['counts']],actual)))
