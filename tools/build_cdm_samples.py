"""Transparent CDM event references from identified StatsBomb Open Data matches.

These are small match samples, never complete-season or career averages.
"""
import hashlib,json,sys,unicodedata
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
COMMIT='4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
BASE=f'https://raw.githubusercontent.com/hudl/open-data/{COMMIT}/'
PLAYERS={'Roy Keane':('Keane-inspired','Manchester United'),
         'Patrick Vieira':('Vieira-inspired','Arsenal'),
         'Claude Makelele':('Makelele-inspired','Chelsea')}
def plain(s):return ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
def exposure(positions):
 intervals=[]
 def minute(value,period,default):
  if value is None:return default
  a,b=map(float,value.split(':'));n=a+b/60
  if period==2 and n<45:n+=45
  return min(45 if period==1 else 90,n)
 for pos in positions:
  a=minute(pos['from'],pos['from_period'],0);b=minute(pos['to'],pos['to_period'],90)
  if not 0<=a<=b<=90:raise ValueError('Invalid playing interval')
  intervals.append((a,b))
 merged=[]
 for a,b in sorted(intervals):
  if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
  else:merged.append((a,b))
 return sum(b-a for a,b in merged)

def build(cache):
 cache.mkdir(parents=True,exist_ok=True)
 def get(path):
  p=cache/path.replace('/','_')
  if not p.exists():
   with urlopen(BASE+path,timeout=30) as response:raw=response.read(16_000_001)
   if len(raw)>16_000_000:raise ValueError('Oversized event file')
   p.write_bytes(raw)
  return json.loads(p.read_bytes()),{'url':BASE+path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 matches,_=get('data/matches/2/44.json')
 fixtures=[m for m in matches if {m['home_team']['home_team_name'],m['away_team']['away_team_name']} in
     [{'Arsenal','Manchester United'},{'Arsenal','Chelsea'}]]
 assert len(fixtures)==4
 def match(m):
  mid=m['match_id'];events,es=get(f'data/events/{mid}.json');lineups,ls=get(f'data/lineups/{mid}.json')
  return m,events,lineups,es,ls
 references={n:dict(player=n,inspiration=ins,role='CDM',club=club,minutes=0,counts={
  k:(0 if k in ('passes','tackles','interceptions','recoveries') else None) for k in
  ['passes','shots','takeons','tackles','interceptions','long_passes','clearances','aerials','shot_assists','goals','assists','box_touches','recoveries','saves','conceded','punches']},matches=[]) for n,(ins,club) in PLAYERS.items()}
 with ThreadPoolExecutor(max_workers=3) as ex:
  for m,events,lineups,es,ls in ex.map(match,fixtures):
   for team in lineups:
    for player in team['lineup']:
     name=plain(player['player_name'])
     if name not in references:continue
     minutes=exposure(player['positions'])
     if minutes<=0:continue
     r=references[name];pid=player['player_id'];selected=[e for e in events if e.get('player',{}).get('id')==pid and e['period'] in (1,2)]
     counts={
      'passes':sum(e['type']['name']=='Pass' for e in selected),
      'tackles':sum(e['type']['name']=='Duel' and e.get('duel',{}).get('type',{}).get('name')=='Tackle' for e in selected),
      'interceptions':sum(e['type']['name']=='Interception' for e in selected),
      'recoveries':sum(e['type']['name']=='Ball Recovery' and not e.get('ball_recovery',{}).get('recovery_failure',False) for e in selected)}
     r['minutes']+=minutes
     for k,v in counts.items():r['counts'][k]+=v
     r['matches'].append(dict(id=m['match_id'],date=m['match_date'],player_id=pid,
      name=f"{m['home_team']['home_team_name']} {m['home_score']}–{m['away_score']} {m['away_team']['away_team_name']}",
      minutes=minutes,counts=counts,event_source=es,lineup_source=ls))
 for r in references.values():
  assert r['minutes']>0 and r['matches']
  r.update(id='statsbomb:'+str(r['matches'][0]['player_id']),reference_kind='match_sample',provider='StatsBomb Open Data',
   season=f"2003/04 · {len(r['matches'])} recorded PL matches",source={'url':BASE+'data/matches/2/44.json','checked_at':'2026-10-25','sha256':hashlib.sha256((cache/'data_matches_2_44.json').read_bytes()).hexdigest()},
   limitations=['Selected matches involving Arsenal, not complete-season or career rates. Different sample sizes and opponents are not adjusted for.',
    'Minutes are the union of source lineup position intervals on a regulation-minute clock, capped at ninety; counts include first/second-half added time.',
    'Pass events, tackle duels, interception events and successful ball recoveries are explicit StatsBomb definitions. Complete equivalence to ESPN/Opta summary fields is not established. Long-pass counts are withheld.'])
 out={'provider':'StatsBomb Open Data','source_commit':COMMIT,'definitions':{
  'passes':'All Pass events','tackles':'Duel events whose duel type is Tackle',
  'interceptions':'All Interception events','recoveries':'Ball Recovery events without recovery_failure'},'references':list(references.values())}
 (ROOT/'pl_dna/data/cdm_match_samples.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
 for r in references.values():print(r['player'],r['minutes'],r['counts'],[m['name'] for m in r['matches']],flush=True)
if __name__=='__main__':build(Path(sys.argv[1] if len(sys.argv)>1 else '../cdm-source-cache'))
