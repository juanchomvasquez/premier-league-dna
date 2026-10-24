"""Recorded-event legend comparison UI. Provider calls occur only on the button."""
import json
import math
from html import escape
import pandas as pd
from pl_dna.legend_blend import load_midfield_study, build_blend_payload, generate_blend_story
from pl_dna.recorded_events import METRICS


def blend_wheel(payload):
    keys = list(METRICS)
    target, fitted = payload['target']['rates'], payload['fit']['reconstructed_rates']
    ceiling = max(10, math.ceil(max(*target.values(), *fitted.values())/10)*10)
    cx, cy, radius = 330, 235, 132
    angles = [-math.pi/2 + 2*math.pi*i/5 for i in range(5)]
    def points(values):
        return ' '.join(f'{cx+radius*v/ceiling*math.cos(a):.2f},{cy+radius*v/ceiling*math.sin(a):.2f}' for v, a in zip(values, angles))
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 465" role="img" aria-label="Observed action rates and fitted reference blend">',
           '<rect width="660" height="465" rx="20" fill="#101d30"/>',
           '<text x="24" y="30" fill="#dce8fb" font-size="14">RECORDED MATCH / FITTED REFERENCE MIX</text>']
    for fraction in (.25, .5, .75, 1):
        svg += [f'<polygon points="{points([ceiling*fraction]*5)}" fill="none" stroke="#35465d"/>',
                f'<text x="335" y="{cy-radius*fraction+12}" fill="#9caec5" font-size="11">{ceiling*fraction:g}</text>']
    for a, label in zip(angles, ['Non-penalty shots', 'Completed take-ons', 'Shot-assisting passes', 'Passes into box', 'Forward passes ≥10 units']):
        x, y = cx+radius*1.35*math.cos(a), cy+radius*1.35*math.sin(a)
        anchor = 'middle' if abs(math.cos(a)) < .1 else 'start' if math.cos(a) > 0 else 'end'
        svg.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="#dce8fb" font-size="11">{escape(label)}</text>')
    for rates, colour, dash in ((fitted, '#b69aff', '7 5'), (target, '#39dfbc', 'none')):
        svg.append(f'<polygon points="{points([rates[k] for k in keys])}" fill="{colour}" fill-opacity=".12" stroke="{colour}" stroke-width="2.5" stroke-dasharray="{dash}"/>')
    svg += ['<text x="24" y="418" fill="#39dfbc" font-size="13">Teal: observed selected player</text>',
            '<text x="24" y="441" fill="#b69aff" font-size="13">Purple: calculated mix of three reference samples</text></svg>']
    return ''.join(svg)


def render_blend_dashboard(st, audience="Fan"):
    study = load_midfield_study()
    st.html('<div class="demo-badge">Real Premier League events · Archived match comparison · Research preview</div>')
    st.caption('Reference coverage: Lampard — 2 matches; Gerrard — 2 matches; Scholes — 1 match. All against Arsenal in 2003/04. These are match samples, not season or career averages.')
    choices = list(study['targets'])
    def label(key):
        t = study['targets'][key]
        f = study['fixtures'][str(t['match_id'])]
        return f"{t['player']} · {f['match']} · {f['date']}"
    controls = st.columns([3, 2])
    target_key = controls[0].selectbox('Recorded midfield performance', choices, format_func=label, key='blend_target')
    minute = controls[1].slider('Match so far', 1, 90, 90, key='blend_minute')
    payload = build_blend_payload(study, target_key, minute, audience)
    target = payload['target']
    st.subheader(f"{payload['player']} · {minute} minutes")
    st.caption('Regular-time clock; 45 and 90 include that half’s added time. Only events observed by the selected point enter the comparison.')
    if payload['availability']:
        st.info(payload['availability'])
        return
    st.markdown('#### Estimated blend within these three recorded samples')
    for column, (name, pct) in zip(st.columns(3), payload['fit']['percentages'].items()):
        column.metric(name, f'{pct}%')
        r = study['references'][name]
        column.caption(f"{r['appearances']} reference match{'es' if r['appearances'] != 1 else ''} · {r['actions']} on-ball actions")
    st.caption('Weights sum to 100% because the calculation fits a mixture of these three samples. They are not probabilities, ability ratings or percentages of a player’s identity. A 100% result means the nearest boundary of this set, not a perfect match.')
    st.markdown('#### The story behind the blend')
    st.write('Microsoft AI selects the most useful supporting comparisons for the match story. The app calculates every count, rate and blend weight, and checks the selected evidence before showing the story.')
    context = (study['source_commit'], target_key, minute, audience, 'legend-blend-v1')
    if st.button('Generate legend story with Microsoft AI', type='primary', key='generate_legend_story'):
        try:
            from pl_dna.microsoft_provider import create_provider_from_env
            provider = create_provider_from_env()
        except Exception:
            result = dict(status='fallback', reason='Microsoft AI is not configured. The calculated blend is available above.')
        else:
            with st.spinner('Choosing the comparisons that explain this blend…'):
                result = generate_blend_story(payload, provider)
        st.session_state['legend_story'] = dict(context=context, result=result)
    saved = st.session_state.get('legend_story')
    if saved and saved['context'] == context:
        result = saved['result']
        if result['status'] == 'verified':
            from pl_dna.presentation import insight_card
            st.html(insight_card(result['text'], audience))
            st.caption('Microsoft-selected story · calculated numbers · checked evidence · controlled wording')
            with st.expander('Copy match story'):
                st.code(result['text'] + ' Exploratory fit to five archived reference appearances, not a career-style score.', language=None, wrap_lines=True)
        else:
            st.info(result['reason'])
    else:
        st.caption('Generate a story for this selection. Changing controls does not call Azure; a story from an earlier selection is hidden.')
    st.caption('One potentially billable Azure request per click. No automatic calls or retries.')
    left, right = st.columns([1.5, 1], gap='large')
    with left:
        st.image(blend_wheel(payload), width='stretch')
        st.caption(f"Shared rate scale: per 100 recorded passes + shots + dribbles. Fit residual: {payload['fit']['rmse']:.2f} rate points RMS; lower is a closer mathematical fit, not higher quality.")
    with right:
        name = st.selectbox('Explore a reference legend', list(study['references']), key='blend_legend')
        from pl_dna.historical import sourced_season_card
        st.html(sourced_season_card(name.split()[-1] + '-inspired'))
        st.caption('Career facts above are context only. The blend uses the specific match samples listed below, never career totals.')
    with st.expander('Recorded counts & fit details'):
        table = pd.DataFrame([dict(Measurement=label, Count=target['counts'][key],
            **{'Selected /100 actions': round(target['rates'][key], 2),
               **{name + ' /100': round(r['rates'][key], 2) for name, r in study['references'].items()},
               'Fitted blend /100': round(payload['fit']['reconstructed_rates'][key], 2)}) for key, label in METRICS.items()])
        st.dataframe(table, hide_index=True, width='stretch')
        st.caption(f"Selected denominator: {target['actions']} on-ball actions. Measurements overlap. A one-event annotation change, holding this denominator fixed, can move a blend weight by up to {payload['one_event_sensitivity_pp']:.1f} percentage points. This is sensitivity, not a confidence interval.")
    with st.expander('Sources, exact definitions & limits', expanded=audience == 'Expert'):
        for legend, r in study['references'].items():
            st.markdown(f'**{legend} — reference fixtures**')
            for mid in r['match_ids']:
                f = study['fixtures'][str(mid)]
                st.markdown(f"[{f['date']} · {f['match']}]({f['source']})")
        for limit in study['limitations']:
            st.write(limit)
        st.json(study['definitions'])
        st.caption('Fit: minimize the unscaled sum of squared differences across five rates, subject to nonnegative weights summing to one. Integer percentages use largest-remainder rounding.')
    st.download_button('Download this comparison evidence', json.dumps(payload, indent=2, allow_nan=False),
        file_name='recorded_midfield_blend_evidence.json', mime='application/json', key='blend_evidence_download')
    st.image(str(__import__('pathlib').Path(__file__).parent/'data/statsbomb-logo.png'), width=170)
    st.markdown('Data: **StatsBomb Open Data** · Analysis: Premier League DNA · [Publisher and usage terms](https://github.com/hudl/open-data). Derived measurements only; raw events are not bundled.')
