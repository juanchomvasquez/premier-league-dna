"""Independent cached-source recount of new retired-player card headlines."""
import hashlib,json,sqlite3,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];cache=Path(sys.argv[1])
records=json.loads((root/'pl_dna/data/retired_roster.json').read_text())
db=sqlite3.connect(':memory:')
def source(m):
 p=cache/(hashlib.sha256(m['url'].encode()).hexdigest()+'.json')
 raw=json.loads(p.read_text())
 assert hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()==m['canonical_sha256']
 return json.dumps(raw)
mapping={'appearances':'appearances','goals':'goals','assists':'goalAssists','clean_sheets':'cleanSheets','goals_conceded':'goalsConceded'}
for name,r in records.items():
 for section in ('career','season'):
  record=r[section];meta=record.get('provenance')
  if not meta:
   assert all(record.get(k) is None for k in mapping);continue
  raw=source(meta)
  assert str(db.execute('select json_extract(?,?)',(raw,'$.player.id')).fetchone()[0])==r['id']
  for k,field in mapping.items():
   if k in record:assert record[k]==db.execute('select json_extract(?,?)',(raw,'$.stats.'+field)).fetchone()[0],(name,section,k)
 assert sum(v for _,v in r['career']['clubs'])==r['career']['appearances']
 print('PASS',name,'career and available season fields')
print('PASS nine retired additions: canonical source digests, identity, numerical headlines and club-sum arithmetic. Club attribution uses the linked public club records; arithmetic alone does not independently establish those attributions.')
