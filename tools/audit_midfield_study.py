"""Independent SQL recount of reference and target totals from cached source files.

python tools/audit_midfield_study.py /tmp/pl-dna-cm
This checks implementation consistency, not independent annotation accuracy.
"""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
cache = Path(sys.argv[1])
study = json.loads((ROOT/'pl_dna/data/midfield_study.json').read_text())
c = sqlite3.connect(':memory:')
c.execute('CREATE TABLE events(match_id INTEGER, value TEXT)')
for mid, fixture in study['fixtures'].items():
    raw = (cache/f'{mid}.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == fixture['sha256']
    c.execute('INSERT INTO events SELECT ?,value FROM json_each(?)', (int(mid), raw.decode()))

SQL = '''WITH player AS (SELECT value FROM events
WHERE json_extract(value,'$.player.name')=? AND match_id IN (SELECT value FROM json_each(?))
AND json_extract(value,'$.period') IN (1,2))
SELECT
sum(json_extract(value,'$.type.name') IN ('Pass','Shot','Dribble')),
sum(CASE WHEN json_extract(value,'$.type.name')='Shot' AND coalesce(json_extract(value,'$.shot.type.name'),'')<>'Penalty' THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Dribble' AND json_extract(value,'$.dribble.outcome.name')='Complete' THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Pass' AND json_extract(value,'$.pass.assisted_shot_id') IS NOT NULL THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Pass' AND json_type(value,'$.pass.outcome') IS NULL AND json_extract(value,'$.pass.end_location[0]')>=102 AND json_extract(value,'$.pass.end_location[1]') BETWEEN 18 AND 62 AND NOT (json_extract(value,'$.location[0]')>=102 AND json_extract(value,'$.location[1]') BETWEEN 18 AND 62) THEN 1 ELSE 0 END),
sum(CASE WHEN json_extract(value,'$.type.name')='Pass' AND json_type(value,'$.pass.outcome') IS NULL AND json_extract(value,'$.pass.end_location[0]')-json_extract(value,'$.location[0]')>=10 THEN 1 ELSE 0 END)
FROM player'''
cases = [(n, r['match_ids'], r) for n, r in study['references'].items()]
cases += [(t['player'], [t['match_id']], t['snapshots']['90']) for t in study['targets'].values()]
for name, mids, profile in cases:
    actual = c.execute(SQL, (name, json.dumps(mids))).fetchone()
    expected = (profile['actions'], *profile['counts'].values())
    assert actual == expected, (name, mids, actual, expected)
    print('PASS', name, mids, dict(zip(['actions', *profile['counts']], actual)))
print('PASS: all source digests and seven independently recounted profiles agree.')
