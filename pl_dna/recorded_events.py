"""One provider and one counting policy for an archived-match research comparison.

This module never consumes synthetic sequences or produces a resemblance score.
"""
from collections import Counter
from html import escape
import json
import math
from pathlib import Path

METRICS = {
    'non_penalty_shots': 'Non-penalty shots',
    'completed_takeons': 'Completed take-ons',
    'shot_assists': 'Shot-assisting passes',
    'passes_into_box': 'Completed passes into box',
    'forward_passes': 'Completed passes ≥10 units forward',
}
DEFINITIONS = {
    'denominator': 'All player Pass, Shot and Dribble events in periods 1–2, including added time. Carries and receptions are excluded to avoid counting consecutive representations of the same action.',
    'non_penalty_shots': 'Shot events whose shot.type is not Penalty. Includes free-kick shots.',
    'completed_takeons': 'Dribble events with dribble.outcome = Complete. Not carries.',
    'shot_assists': 'Pass events with an assisted_shot_id linking to an actual Shot in the same match. Includes passes assisting goals; no inferred assists.',
    'passes_into_box': 'Pass events without a pass.outcome (StatsBomb completion convention), starting outside and ending inside x≥102, 18≤y≤62 on the StatsBomb 120×80 pitch. Includes set plays.',
    'forward_passes': 'Completed passes ending at least 10 StatsBomb x-units farther toward the opposition goal. This custom definition is NOT the synthetic wheel’s 25% distance-reduction rule.',
    'rates': '100 × summed qualifying events / summed Pass+Shot+Dribble events. Pool counts first, never average match percentages.',
}


def in_box(point):
    return bool(point and len(point) >= 2 and point[0] >= 102 and 18 <= point[1] <= 62)


def player_profile(events, player_id):
    """Fail on duplicate IDs or dangling shot links rather than silently count them."""
    ids = [e['id'] for e in events]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate event IDs')
    shots = {e['id'] for e in events if e['period'] in (1, 2) and e['type']['name'] == 'Shot'}
    own = [e for e in events if e['period'] in (1, 2) and e.get('player', {}).get('id') == player_id]
    counts = Counter({key: 0 for key in METRICS})
    actions = 0
    goals = 0
    for event in own:
        kind = event['type']['name']
        if kind in ('Pass', 'Shot', 'Dribble'):
            actions += 1
        if kind == 'Shot':
            counts['non_penalty_shots'] += event['shot'].get('type', {}).get('name') != 'Penalty'
            goals += event['shot']['outcome']['name'] == 'Goal'
        elif kind == 'Dribble':
            counts['completed_takeons'] += event['dribble']['outcome']['name'] == 'Complete'
        elif kind == 'Pass':
            details = event['pass']
            assisted = details.get('assisted_shot_id')
            if assisted and assisted not in shots:
                raise ValueError(f'Dangling assisted-shot link: {assisted}')
            counts['shot_assists'] += bool(assisted)
            if 'outcome' not in details:
                start, end = event.get('location'), details.get('end_location')
                counts['passes_into_box'] += bool(start and end and not in_box(start) and in_box(end))
                counts['forward_passes'] += bool(start and end and end[0] - start[0] >= 10)
    return dict(counts= dict(counts), actions=actions, goals=goals, appearance=bool(own))


def pooled_profile(profiles):
    counts = {k: sum(p['counts'][k] for p in profiles) for k in METRICS}
    actions = sum(p['actions'] for p in profiles)
    return dict(counts=counts, actions=actions, goals=sum(p['goals'] for p in profiles),
                appearances=sum(p['appearance'] for p in profiles),
                rates={k: 100*v/actions if actions else None for k, v in counts.items()})


def load_study():
    return json.loads((Path(__file__).parent / 'data' / 'recorded_study.json').read_text())


def comparison_wheel(target, reference):
    """Same absolute rate scale for every axis; no min-max fit or similarity score."""
    keys = list(METRICS)
    ceiling = max(10, math.ceil(max(*target['rates'].values(), *reference['rates'].values()) / 10) * 10)
    cx, cy, radius = 330, 235, 132
    angles = [-math.pi/2 + 2*math.pi*i/len(keys) for i in range(len(keys))]
    def points(values):
        return ' '.join(f'{cx+radius*v/ceiling*math.cos(a):.2f},{cy+radius*v/ceiling*math.sin(a):.2f}' for v,a in zip(values,angles))
    pieces=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 475" role="img" aria-label="Recorded-event profile comparison, rates per 100 passes shots and dribbles">',
            '<rect width="660" height="475" rx="20" fill="#101d30"/>',
            '<text x="24" y="30" fill="#dce8fb" font-size="14">RECORDED EVENTS · SHARED DEFINITIONS</text>']
    for fraction in (.25,.5,.75,1):
        pieces.append(f'<polygon points="{points([ceiling*fraction]*len(keys))}" fill="none" stroke="#35465d"/>')
        pieces.append(f'<text x="335" y="{cy-radius*fraction+12}" fill="#9caec5" font-size="11">{ceiling*fraction:g}</text>')
    short=['Non-penalty shots','Completed take-ons','Shot-assisting passes','Passes into box','Forward passes ≥10 units']
    for a,label in zip(angles,short):
        x,y=cx+radius*1.35*math.cos(a),cy+radius*1.35*math.sin(a)
        anchor='middle' if abs(math.cos(a))<.1 else ('start' if math.cos(a)>0 else 'end')
        pieces.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="#dce8fb" font-size="11">{escape(label)}</text>')
    for profile,colour,opacity in ((reference,'#b69aff','.12'),(target,'#39dfbc','.18')):
        pieces.append(f'<polygon points="{points([profile["rates"][k] for k in keys])}" fill="{colour}" fill-opacity="{opacity}" stroke="{colour}" stroke-width="2.5"/>')
    pieces.extend(['<text x="24" y="420" fill="#39dfbc" font-size="13">Teal: selected recorded match</text>',
                   '<text x="24" y="443" fill="#b69aff" font-size="13">Purple: Henry 2003/04 pooled event rates</text>',
                   '<text x="24" y="462" fill="#aabbd0" font-size="11">Per 100 recorded passes + shots + dribbles · frequency, not ability</text></svg>'])
    return ''.join(pieces)


def render_study(st):
    import pandas as pd
    study = load_study()
    st.subheader('Can we compare the recorded actions?')
    st.caption('Historical event study · real matches · separate from the synthetic demo')
    choices = list(study['targets'])
    default = next(i for i, label in enumerate(choices) if study['targets'][label]['player'] == 'Thierry Henry')
    choice=st.selectbox('Recorded performance', choices, index=default, key='recorded_target')
    target=study['targets'][choice]
    # A match must not contribute to its own reference baseline.
    reference=study['reference_without_liverpool'] if target['match_id']==3749448 else study['reference']
    st.write(f"**{choice}** versus **Thierry Henry · Arsenal 2003/04 · {reference['appearances']} other-match appearances**" if target['match_id']==3749448 else f"**{choice}** versus **Thierry Henry · Arsenal 2003/04 · {reference['appearances']} appearances**")
    st.image(comparison_wheel(target,reference),width='stretch')
    frame=pd.DataFrame([{'Measurement':label,'Match count':target['counts'][key], 'Match /100 actions':round(target['rates'][key],2), 'Henry count':reference['counts'][key], 'Henry /100 actions':round(reference['rates'][key],2)} for key,label in METRICS.items()])
    st.dataframe(frame,hide_index=True,width='stretch')
    st.caption(f"Denominators: {target['actions']} selected-match actions; {reference['actions']} Henry reference actions. Rates pool event totals, not match averages.")
    st.caption(f"One additional counted action changes the selected-match rate by {100/target['actions']:.2f} points per 100 actions at the current denominator. This is a sensitivity check, not a confidence interval.")
    st.info('These are comparable recorded-action frequencies. One match does not establish lasting style or ability. No overall similarity percentage is claimed. The reference covers 2003/04, not Henry’s career.')
    with st.expander('Accuracy checks and discrepancies'):
        for check in study['checks']:
            st.write(f"**{check['status']}** · {check['description']}")
            if check.get('source'): st.markdown(f"[Check source]({check['source']})")
        st.write('Validated here means count reconciliation and identical calculation rules. It does not mean an independently validated style-matching model.')
        st.json(study['limitations'])
    with st.expander('Metric definitions and reproducibility'):
        st.json(DEFINITIONS)
        st.write(f"Source snapshot: `{study['source_commit']}`. Source-file SHA-256 digests are included in the research report; no raw event files are bundled.")
    st.image(str(Path(__file__).parent/'data'/'statsbomb-logo.png'),width=170)
    st.markdown('Data: **StatsBomb Open Data**. Analysis by Premier League DNA. [Source repository and terms](https://github.com/hudl/open-data). [Selected match events](https://github.com/hudl/open-data/blob/'+study['source_commit']+'/data/events/'+str(target['match_id'])+'.json).')
