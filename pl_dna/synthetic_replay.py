"""Clocked release of our own synthetic events into the Microsoft brief pipeline."""
from copy import deepcopy
import hashlib,json,math
from pl_dna.roles import build_role_story_input,analyze_role_player,ROLE_DEFINITIONS,score_role_profiles

def advance_clock(state,now):
    if not state.get('replay_playing'):return
    last=state.get('replay_last_tick',now)
    ticks=max(0,int((now-last)//2))
    if ticks:
        state['minute']=min(90,int(state.get('minute',1))+ticks*int(state.get('replay_step',3)))
        state['replay_last_tick']=last+2*ticks
        if state['minute']==90:state['replay_playing']=False

def illustrative_profile_context(data, player, start, end):
    """Rank invented profiles; never convert independent scores into blend percentages."""
    report=analyze_role_player(data,player,start,end)
    scores=score_role_profiles(data,player,start,end)
    context={'status':'insufficient', 'kind':'invented_legend_inspired_profiles',
        'label':'Illustrative profile comparison · not historical player similarity',
        'policy':'Demo display policy: distance at most 0.75; show a second eligible profile only within five score points of the first. Not calibrated against historical players.',
        'score_meaning':'Independent scores = 100 / (1 + normalized distance), not percentages, probabilities, quality ratings or mixture weights.',
        'candidates':[]}
    if scores.empty:return context
    eligible=scores[scores.weighted_distance.le(0.75)]
    if eligible.empty:
        context['status']='no_clear_profile';return context
    top=float(eligible.iloc[0].experimental_resemblance_score)
    config=ROLE_DEFINITIONS[report['role']]
    counts={m['measurement']:m['count'] for m in report['measurements']}
    for name,row in eligible.iterrows():
        if len(context['candidates'])==2 or top-float(row.experimental_resemblance_score)>5:break
        axes=[]
        for i,metric in enumerate(config['metrics']):
            observed=100*counts[metric]/report['action_sequences']
            reference=config['profiles'][name][i]
            scale=max(v[i] for v in config['profiles'].values()) or 1
            axes.append({'metric':metric,'evidence_id':'observed:'+metric,
                'observed_per_100_sequences':round(observed,3),'invented_reference_per_100_sequences':reference,
                'normalized_difference':round(abs(observed-reference)/scale,4)})
        context['candidates'].append({'profile':name,'legend_label':config['legend_inspirations'][name],
            'score':round(float(row.experimental_resemblance_score),1),
            'axes':axes})
    context['status']='illustrative_candidates'
    return context

def synthetic_brief_payload(data,player,start,end,view='Match so far',language='English',focus='Fan explanation'):
    package=build_role_story_input(data,player,start,end,view=view)
    report=package['evidence'];role=report['role']
    p=dict(task='performance_interpretation',data_kind='synthetic',player=player,role=role,
        role_label=ROLE_DEFINITIONS[role]['label'],minute=end,window=package['window'],
        language=language,focus=focus,view=view,phase='full_time_recap' if end==90 else 'match_in_progress',
        fit_status='synthetic_demonstration',references={},evidence=[],availability='',
        instructions=package['instructions'],limitations=[
            'Our own deterministic fictional action scenarios, not real match observations or a complete possession-consistent simulation.',
            'Invented legend-inspired profiles are design hypotheses, never measured historical similarity.',
            'Action measurements overlap. Do not sum them into distinct events or infer player quality, tactics or causes.'])
    for m in report['measurements']:
        assert m['count']==len(m['event_ids'])
        p['evidence'].append(dict(id='observed:'+m['measurement'],metric=m['measurement'],kind='recorded',
            count=m['count'],event_ids=m['event_ids'],supporting_event_ids=m.get('supporting_event_ids',[]),
            sentence=f"Synthetic demonstration — {player}: {m['count']} {m['measurement'].lower()} in minutes ({start}, {end}]."))
    if report['action_sequences']<10:
        p['availability']='At least ten recorded action sequences are required for the Microsoft brief. The replay and local facts remain available.'
    if end>=30:
        previous=analyze_role_player(data,player,end-30,end-15)
        recent=analyze_role_player(data,player,end-15,end)
        if min(previous['action_sequences'],recent['action_sequences'])>=5:
            for old,new in zip(previous['measurements'],recent['measurements'],strict=True):
                if old['count']+new['count']<3 or old['count']==new['count']:continue
                p['evidence'].append(dict(id='change:'+new['measurement'],kind='window_change',metric=new['measurement'],
                    previous_count=old['count'],recent_count=new['count'],
                    event_ids=list(dict.fromkeys(old['event_ids']+new['event_ids'])),
                    supporting_event_ids=list(dict.fromkeys(old.get('supporting_event_ids',[])+new.get('supporting_event_ids',[]))),
                    sentence=f"Synthetic demonstration — {new['measurement']}: {new['count']} in minutes ({end-15}, {end}], versus {old['count']} in the preceding equal fifteen-minute window ({end-30}, {end-15}]."))
    # Invented comparisons are separate, explicitly labelled context; no future rows.
    p['illustrative_comparison']=illustrative_profile_context(data,player,start,end)
    from pl_dna.presentation import LEGEND_CLUBS
    p['excluded_legend_names']=[n.removesuffix('-inspired') for n in LEGEND_CLUBS]
    return p

def brief_fingerprint(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()

def auto_brief_due(enabled,playing,minute,key,state,now):
    return bool(enabled and (playing or minute==90) and
        state.get('synthetic_last_ai_key')!=key and now-state.get('synthetic_last_ai_attempt',-math.inf)>=30)
