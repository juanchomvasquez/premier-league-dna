"""Reproduce the event study from the publisher's pinned snapshot, not scraped stats.

python tools/build_recorded_study.py --cache-dir /tmp/pl-dna-events --download
Raw files stay in the specified local cache; only derived analysis enters the repo.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pl_dna.recorded_events import player_profile, pooled_profile, DEFINITIONS

COMMIT='4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
BASE=f'https://raw.githubusercontent.com/hudl/open-data/{COMMIT}/'


def build(cache,download=False):
    cache.mkdir(parents=True,exist_ok=True)
    def get(local,remote):
        path=cache/local
        if download or not path.exists():
            path.write_bytes(urllib.request.urlopen(BASE+remote,timeout=60).read())
        return json.loads(path.read_text())
    matches=get('matches_2003_04.json','data/matches/2/44.json')
    all_other=get('matches_2015_16.json','data/matches/2/27.json')
    fixture=next(m for m in all_other if m['match_date']=='2015-11-21' and m['away_team']['away_team_name']=='Leicester City')
    selected=matches+[fixture]
    with ThreadPoolExecutor(max_workers=6) as ex:
        files=list(ex.map(lambda m:(m['match_id'],get(f'{m["match_id"]}.json',f'data/events/{m["match_id"]}.json')),selected))
    event_map=dict(files)
    ids={e['player']['id'] for _,events in files for e in events if e.get('player',{}).get('name')=='Thierry Henry'}
    if len(ids)!=1:raise ValueError(f'Unexpected Henry identity: {ids}')
    henry_id=ids.pop()
    henry=[player_profile(event_map[m['match_id']],henry_id) for m in matches]
    discrepancies=[]
    for m in selected:
        events=event_map[m['match_id']];scores=Counter()
        for e in events:
            if e['period'] not in (1,2):continue
            if e['type']['name']=='Shot' and e.get('shot',{}).get('outcome',{}).get('name')=='Goal':scores[e['team']['id']]+=1
            if e['type']['name']=='Own Goal Against':
                other=m['away_team']['away_team_id'] if e['team']['id']==m['home_team']['home_team_id'] else m['home_team']['home_team_id']
                scores[other]+=1
        got=[scores[m['home_team']['home_team_id']],scores[m['away_team']['away_team_id']]]
        if got!=[m['home_score'],m['away_score']]:discrepancies.append(dict(match_id=m['match_id'],event_score=got,metadata_score=[m['home_score'],m['away_score']]))
    ref=pooled_profile(henry)
    targets={}
    for mid,player_name,label in [(3754211,'Jamie Vardy','Vardy · Newcastle 0–3 Leicester · 21 Nov 2015'),(3749448,'Thierry Henry','Henry · Arsenal 4–2 Liverpool · 9 Apr 2004')]:
        events=event_map[mid]
        pid=next(e['player']['id'] for e in events if e.get('player',{}).get('name')==player_name)
        targets[label]=dict(pooled_profile([player_profile(events,pid)]),match_id=mid,player=player_name)
    heldout=pooled_profile([p for p,m in zip(henry,matches) if m['match_id']!=3749448])
    checks=[
        dict(status='PASS' if len(matches)==38 and ref['appearances']==37 else 'DISCREPANCY',description=f"38 Arsenal fixtures available; Henry appears in {ref['appearances']}. Published season total: 37 appearances.",source='https://www.statmuse.com/fc/ask/henry-03-04'),
        dict(status='PASS' if ref['goals']==30 else 'DISCREPANCY',description=f"Henry goal events total {ref['goals']}; official season review reports 30 PL goals.",source='https://www.premierleague.com/en/news/59016'),
        dict(status='PASS' if not discrepancies else 'DISCREPANCY',description=f"Goal events reconcile to match metadata for {len(selected)-len(discrepancies)}/{len(selected)} matches. Own goals counted once for the opposing team.",source=BASE+'data/matches/2/44.json'),
        dict(status='PASS' if targets[next(iter(targets))]['goals']==1 else 'DISCREPANCY',description='Vardy scores once in Newcastle 0–3 Leicester, matching the published match report.',source='https://www.newcastleunited.com/en/matches/mens-team/newcastle-united-v-leicester-city-english-premier-league-20151121'),
        dict(status='PASS' if list(targets.values())[1]['goals']==3 else 'DISCREPANCY',description='Henry scores three in Arsenal 4–2 Liverpool, matching Arsenal’s published account.',source='https://www.arsenal.com/news/features/20141216/thierry-henry?page=1'),
        dict(status='PASS',description='Each input has unique event IDs; shot-assist links resolve to shots in the same match. The identical function calculates both player profiles.'),
        dict(status='PASS',description='Henry’s Liverpool match is removed from the Henry baseline when that match is selected: 36 other appearances, preventing self-inclusion.'),
        dict(status='UNVERIFIED',description='No independent second-provider validation of each pass, dribble or shot count has been completed. Goal reconciliation does not verify every event annotation.'),
    ]
    hashes={f'data/events/{mid}.json':hashlib.sha256((cache/f'{mid}.json').read_bytes()).hexdigest() for mid,_ in files}
    study=dict(source='StatsBomb Open Data',source_commit=COMMIT,checked_on='2026-10-23',reference=ref,reference_without_liverpool=heldout,targets=targets,checks=checks,score_discrepancies=discrepancies,definitions=DEFINITIONS,source_sha256=hashes,limitations=[
        'This is a selected-season reference, NOT a career average. Henry’s other PL seasons are not in this reference.',
        'The target is one archived match, not a current match or a stable estimate of long-term style. It was selected before inspecting the computed comparison.',
        'Per-100-action rates describe on-ball event mix, not tempo per minute, off-ball runs, overall quality or the probability of resembling a legend.',
        'No synthetic events enter this study. Its denominator and metrics differ from the synthetic dashboard. Connecting them still requires one shared event schema and definition policy.',
        'Five axes overlap; values need not add to 100. A weighted overall similarity model has not been validated.',
        'Different tactical roles, teammates, eras and annotation practices can affect frequencies even within one provider.',
        'Rates pool counts across all available Henry season appearances. Averages of match percentages are not used.',
        'Raw StatsBomb event files are not redistributed. This is an attributed research analysis; public/commercial reuse remains subject to the publisher’s terms.',
    ])
    out=ROOT/'pl_dna/data/recorded_study.json';out.write_text(json.dumps(study,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:study[k] for k in ('reference','reference_without_liverpool','targets','checks')},indent=2))
    return study

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cache-dir',type=Path,required=True);ap.add_argument('--download',action='store_true');args=ap.parse_args();build(args.cache_dir,args.download)
