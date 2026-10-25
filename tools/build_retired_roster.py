"""Build attributed card facts for the approved retired-player replacements."""
import hashlib
import json
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pl_dna.season_feed import PL,fetch_json

# Club subtotals are PL appearances only, not all league/all-competition games.
# Public records below identify the club splits; totals are cross-checked with PL.
SPECS=[
 ('Van der Sar-inspired',4058,2008,'Manchester United',[('Manchester United',186),('Fulham',127)],'https://www.myfootballfacts.com/premier-league/all-time-premier-league/appearances/all-time-300-or-more-players-premier-league-appearances/'),
 ('Rio Ferdinand-inspired',2034,2012,'Manchester United',[('Manchester United',312),('West Ham United',127),('Leeds United',54),('Queens Park Rangers',11)],'https://www.statmuse.com/fc/ask/rio-ferdinand-appearances-by-club'),
 ('Gary Neville-inspired',1807,2008,'Manchester United',[('Manchester United',400)],'https://www.premierleague.com/en/events/hall-of-fame/inductees/gary-neville'),
 ('Baines-inspired',12745,2012,'Everton',[('Everton',348),('Wigan Athletic',72)],'https://www.statmuse.com/fc/ask/leighton-baines-stats-with-wigan-athletic'),
 ('Vieira-inspired',1593,2004,'Arsenal',[('Arsenal',279),('Manchester City',28)],'https://fbref.com/en/players/f90f1086/Patrick-Vieira'),
 ('Keane-inspired',361,1999,'Manchester United',[('Manchester United',326),('Nottingham Forest',40)],'https://www.statmuse.com/fc/ask/how-many-premier-league-appearances-did-roy-keane-make'),
 ('Bergkamp-inspired',1608,1997,'Arsenal',[('Arsenal',315)],'https://www.premierleague.com/es/news/2147141'),
 ('Giggs-inspired',3,2008,'Manchester United',[('Manchester United',632)],'https://www.premierleague.com/en/news/1251148'),
 ('Bale-inspired',36903,2012,'Tottenham Hotspur',[('Tottenham Hotspur',166)],'https://www.premierleague.com/en/news/3014385'),
]

def build(cache):
 cache.mkdir(exist_ok=True,parents=True)
 def get(url):
  key=hashlib.sha256(url.encode()).hexdigest();p=cache/(key+'.json');m=cache/(key+'.meta.json')
  if not p.exists():
   a,s=fetch_json(url);p.write_text(json.dumps(a));m.write_text(json.dumps(s))
  a=json.loads(p.read_text());s=json.loads(m.read_text())
  s['canonical_sha256']=hashlib.sha256(json.dumps(a,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  m.write_text(json.dumps(s));return a,s
 def one(spec):
  name,pid,year,club,clubs,club_source=spec
  raw,meta=get(f'{PL}/v2/competitions/8/players/{pid}/stats')
  stats=raw['stats'];player=raw['player']['name']
  assert str(raw['player']['id'])==str(pid)
  assert sum(v for _,v in clubs)==stats['appearances'],(name,clubs,stats['appearances'])
  career={'appearances':stats['appearances'],'clubs':clubs,'checked_on':'25 Oct 2026',
   'sources':[['Premier League · complete PL career',meta['url']],['PL club appearance records',club_source]],
   'provenance':meta,'coverage':'Complete recorded PL career',
   'note':'Club colour widths use Premier League appearances only. Career totals do not enter the comparison.'}
  if name=='Van der Sar-inspired':career.update(clean_sheets=stats.get('cleanSheets'),titles=None)
  else:career.update(goals=stats.get('goals'),assists=stats.get('goalAssists'))
  url=f'{PL}/v2/competitions/8/seasons/{year}/players/{pid}/stats'
  try:
   season,sm=get(url);values=season['stats']
  except HTTPError as exc:
   if exc.code!=404:raise
   values={};sm=None
  facts={'player':player,'club':club,'season':f'{year}/{str(year+1)[-2:]}',
   'appearances':values.get('appearances'),'goals':values.get('goals'),'assists':values.get('goalAssists'),
   'selection':'Selected identified PL season. Chosen for a relevant career period and source availability, not claimed to be the best overall season.',
   'coverage_note':'Season facts and career totals are separate from fitted rates. Missing source fields remain unavailable.',
   'sources':[{'title':'Premier League · selected season','url':url}], 'provenance':sm}
  if year<2006:facts['coverage_note']+=' Detailed pre-2006/07 metrics are not used to infer a style profile.'
  if sm is None:facts['coverage_note']+=' This season endpoint returned HTTP 404; no season totals or rates are invented.'
  if name=='Van der Sar-inspired':
   facts.update(clean_sheets=values.get('cleanSheets'),goals_conceded=values.get('goalsConceded'),
     display_fields=[['appearances','PL appearances'],['clean_sheets','PL clean sheets'],['goals_conceded','Goals conceded']])
  return name,{'career':career,'season':facts,'id':str(pid),'club':club}
 with ThreadPoolExecutor(max_workers=3) as ex:records=dict(ex.map(one,SPECS))
 for r in records.values():
  for section in ('career','season'):
   for key,value in r[section].items():
    if isinstance(value,float) and value.is_integer():r[section][key]=int(value)
 (ROOT/'pl_dna/data/retired_roster.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
 for name,r in records.items():print(name,r['career']['appearances'],r['season']['appearances'],r['season']['goals'],r['season']['assists'])

if __name__=='__main__':build(Path(sys.argv[1] if len(sys.argv)>1 else '../source-audit-cache'))
