"""Independent SQL event recount of the three small CDM match samples."""
import json,hashlib,sqlite3,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];cache=Path(sys.argv[1]);db=sqlite3.connect(':memory:')
study=json.loads((root/'pl_dna/data/cdm_match_samples.json').read_text())
def raw(meta):
 relative=meta['url'].split('/'+study['source_commit']+'/')[1]
 p=cache/relative.replace('/','_');data=p.read_bytes()
 assert hashlib.sha256(data).hexdigest()==meta['sha256'];return data.decode()
for r in study['references']:
 totals={k:0 for k in study['definitions']};minutes=0
 for m in r['matches']:
  events=raw(m['event_source']);lineups=raw(m['lineup_source']);pid=m['player_id']
  players=db.execute('''select p.value from json_each(?) t,
   json_each(json_extract(t.value,'$.lineup')) p where json_extract(p.value,'$.player_id')=?''',(lineups,pid)).fetchall()
  assert len(players)==1
  player=json.loads(players[0][0]);intervals=[]
  for pos in player['positions']:
   def clock(value,period,default):
    if value is None:return default
    a,b=map(float,value.split(':'));v=a+b/60
    if period==2 and v<45:v+=45
    return min(v,45 if period==1 else 90)
   intervals.append((clock(pos['from'],pos['from_period'],0),clock(pos['to'],pos['to_period'],90)))
  # Independently count exposure by the union of interval breakpoints.
  points=sorted({x for a,b in intervals for x in (a,b)})
  duration=sum(b-a for a,b in zip(points,points[1:]) if any(l<=a and b<=u for l,u in intervals))
  assert abs(duration-m['minutes'])<1e-8
  minutes+=duration
  where={
   'passes':"json_extract(value,'$.type.name')='Pass'",
   'tackles':"json_extract(value,'$.type.name')='Duel' and json_extract(value,'$.duel.type.name')='Tackle'",
   'interceptions':"json_extract(value,'$.type.name')='Interception'",
   'recoveries':"json_extract(value,'$.type.name')='Ball Recovery' and coalesce(json_extract(value,'$.ball_recovery.recovery_failure'),0)=0"}
  for k,predicate in where.items():
   count=db.execute("select count(*) from json_each(?) where json_extract(value,'$.player.id')=? and json_extract(value,'$.period') in (1,2) and "+predicate,(events,pid)).fetchone()[0]
   assert count==m['counts'][k],(r['player'],m['id'],k,count,m['counts'][k]);totals[k]+=count
 assert abs(minutes-r['minutes'])<1e-8
 assert all(v==r['counts'][k] for k,v in totals.items())
 print('PASS',r['player'],len(r['matches']),'recorded PL matches;',minutes,'minutes;',totals)
print('PASS: source hashes, player identity, lineup exposure and independent SQL counts. Small match samples and cross-provider equivalence remain limitations; this does not validate style similarity.')
