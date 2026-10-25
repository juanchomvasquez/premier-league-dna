"""Current-season recorded examples and an opt-in, automatically polled match feed."""
from datetime import date as calendar_date, datetime, timezone
from html import escape
import hashlib
import json
import math
from pathlib import Path
import time
from textwrap import wrap
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

from pl_dna.season_feed import (fetch_scoreboard, fetch_summary, fetch_player_stats,
    normalize_player, match_info, roster_players, FIELDS, ROLE_LABELS)
from pl_dna.season_comparison import compare_season_player
from pl_dna.analyst_brief import generate_analyst_brief

now_seconds = time.time


def load_current():
    return json.loads((Path(__file__).parent/'data/current_season.json').read_text())


@st.cache_data(ttl=60, show_spinner=False)
def cached_scoreboard(date):
    return fetch_scoreboard(date)


@st.cache_data(ttl=60, show_spinner=False)
def cached_summary(match_id):
    return fetch_summary(match_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_player(match_id, team_id, player_id):
    return fetch_player_stats(match_id, team_id, player_id)


def fingerprint(payload):
    # Retrieval times alone are not a football development and must not call AI.
    source = {k: payload[k] for k in ('player_id', 'role')}
    source['brief_version'] = 2  # Never reuse the former fixed-template story.
    source['fixture_id'] = payload['fixture']['id']
    source['counts'] = payload['target']['counts']
    source['minutes'] = payload['target']['minutes']
    source['execution'] = payload['target'].get('execution', {})
    source['references'] = [(n, r['season'], r['counts'], r['minutes']) for n, r in payload['references'].items()]
    source['omitted_metrics'] = payload.get('omitted_metrics', [])
    return hashlib.sha256(json.dumps(source, sort_keys=True, allow_nan=False).encode()).hexdigest()


def auto_story_due(enabled, state, changed, now, last_attempt, stale=False):
    return enabled and state == 'in' and changed and not stale and now-last_attempt >= 300


def wheel(payload):
    keys = payload['metric_keys']
    comparable = 'fit' in payload
    scales = payload.get('scales', {k:1 for k in keys})
    rates = payload.get('target_rates', {k:90*payload['target']['counts'][k]/payload['minute'] for k in keys})
    selected = [100*rates[k]/scales[k] for k in keys]
    fitted = [100*payload['fitted_rates'][k]/scales[k] for k in keys] if comparable else []
    show_mix = comparable and payload.get('fit_status') != 'no_clear_match'
    ceiling = max(100, math.ceil(max(selected+(fitted if show_mix else []))/25)*25)
    cx, cy, radius = 330, 235, 135
    angles = [-math.pi/2+2*math.pi*i/len(keys) for i in range(len(keys))]
    def points(values):
        return ' '.join(f'{cx+radius*v/ceiling*math.cos(a):.2f},{cy+radius*v/ceiling*math.sin(a):.2f}' for v, a in zip(values, angles))
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 455" role="img" aria-label="Recorded match and fitted reference-season mix">',
        '<rect width="660" height="455" rx="20" fill="#321044"/>',
        '<text x="24" y="30" fill="#dce8fb" font-size="14">RECORDED MATCH / IDENTIFIED REFERENCES</text>']
    for f in (.25,.5,.75,1):
        svg += [f'<polygon points="{points([ceiling*f]*len(keys))}" fill="none" stroke="#694077"/>',
            f'<text x="335" y="{cy-radius*f+12}" fill="#9caec5" font-size="11">{ceiling*f/100:g}{"×" if comparable else ""}</text>']
    for a, key in zip(angles, keys):
        x, y = cx+radius*1.4*math.cos(a), cy+radius*1.4*math.sin(a)
        anchor = 'middle' if abs(math.cos(a)) < .1 else 'start' if math.cos(a) > 0 else 'end'
        lines = wrap(FIELDS[key][0], width=22)
        spans = ''.join(f'<tspan x="{x:.1f}" dy="{0 if i==0 else 13}">{escape(line)}</tspan>' for i,line in enumerate(lines))
        svg.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="#dce8fb" font-size="11">{spans}</text>')
    series = ([(fitted,'#b69aff','7 5')] if show_mix else []) + [(selected,'#00ff85','none')]
    for values, color, dash in series:
        svg.append(f'<polygon points="{points(values)}" fill="{color}" fill-opacity=".13" stroke="{color}" stroke-width="2.5" stroke-dasharray="{dash}"/>')
    legend = 'Teal: selected match rates · Purple: fitted reference mix' if show_mix else 'Teal: selected match rates · No composite reference shown'
    scale_note = '1× = highest selected reference rate on that axis · not an ability rating' if comparable else 'Recorded counts per 90 played minutes · shared count scale · no historical fit'
    svg += [f'<text x="24" y="420" fill="#00ff85" font-size="13">{legend}</text>',
        f'<text x="24" y="443" fill="#aabbd0" font-size="11">{scale_note}</text></svg>']
    return ''.join(svg)


def render_story(payload, live, stale):
    st.markdown('#### Microsoft analyst brief')
    key = fingerprint(payload)
    from pl_dna.presentation import insight_card
    with st.expander('Calculated snapshot · no AI call'):
        for metric in payload['metric_keys'][:3]:
            st.write(f"{FIELDS[metric][0]}: {payload['target']['counts'][metric]:g} in {payload['minute']:g} played minutes.")
        st.caption('Observed counts only. The analyst brief below interprets the pattern across measurements.')
    clicked = st.button('Generate Microsoft interpretation', type='primary', key='season_generate_story')
    enabled = st.checkbox('Update Microsoft interpretation automatically during live play', value=False, key='season_auto_ai') if live else False
    if live:
        st.caption('Optional automatic AI: potentially billable, at most one request every five minutes in this browser session, only when the comparison changes. It is off by default. Data and calculated comparisons update without AI calls.')
    now = now_seconds()
    changed = st.session_state.get('season_last_ai_fingerprint') != key
    due = auto_story_due(enabled, payload['fixture']['state'], changed, now,
        st.session_state.get('season_ai_last_attempt', 0), stale)
    if (clicked and not stale) or due:
        # Save attempt time before the request, including failures, to avoid retries.
        st.session_state['season_ai_last_attempt'] = now
        st.session_state['season_last_ai_fingerprint'] = key
        try:
            from pl_dna.microsoft_provider import create_provider_from_env
            provider = create_provider_from_env()
        except Exception:
            result = {'status': 'fallback', 'reason': 'Microsoft AI is not configured. The calculated comparison remains available.'}
        else:
            with st.spinner('Interpreting the performance and citing the supporting facts…'):
                result = generate_analyst_brief(payload, provider)
        st.session_state['season_ai_story'] = {'fingerprint': key, 'result': result}
    saved = st.session_state.get('season_ai_story')
    if saved and saved['fingerprint'] == key and not stale:
        result = saved['result']
        if result['status'] == 'evidence_checked':
            st.subheader(result['headline'])
            st.html(insight_card(result['text'], 'Fan'))
            st.caption('AI-written interpretation · cited facts checked · interpretation is not independently verified')
            with st.expander('Supporting facts & copy brief'):
                for fact in result['facts']: st.write(fact)
                st.code(result['headline']+'\n\n'+result['text']+'\n\n'+'\n'.join(result['facts']), language=None, wrap_lines=True)
        else:
            st.info(result['reason'])
    elif not stale:
        st.caption('Generate a short reading of the pattern across these stats, with the exact supporting facts attached. No AI request is made until you click or enable live updates.')
    if clicked and stale:
        st.info('The feed is stale. A new Microsoft story is paused until a successful refresh.')


def render_performance(entry, references, live=False, stale=False, unavailable_references=()):
    player, snapshot, fixture, role = (entry[k] for k in ('player','snapshot','fixture','role'))
    st.html(f'<section class="player-hero"><div><div class="eyebrow">2026/27 PREMIER LEAGUE / RECORDED PERFORMANCE</div><h2>{escape(player["name"])}</h2><p>{escape(player["team"])} · {escape(ROLE_LABELS[role])} reference group</p><p>{escape(fixture["home"])} {escape(fixture["score"])} {escape(fixture["away"])}</p></div></section>')
    st.caption(f"{fixture['date'][:10]} · {fixture['status']} · source clock {fixture['clock']} · player minutes are source-reported, not inferred from the match clock")
    st.caption('Source position: '+player['source_position']+'. Reference-group selection is not an independently verified tactical-role classification.')
    for col, label, value in zip(st.columns(3), ('Minutes played','Goals','Assists'), (snapshot['minutes'],snapshot['goals'],snapshot['assists'])):
        col.metric(label, '—' if value is None else f'{value:g}')
    for warning in snapshot['warnings']:
        st.warning(warning)
    if snapshot.get('execution'):
        with st.expander('Execution facts — separate from the style comparison'):
            for label, fact in snapshot['execution'].items():
                st.write(f"**{label}: {fact['successful']:g}/{fact['attempted']:g} ({fact['percentage']:.1f}%)**")
            st.caption('Recorded action outcomes, not an overall match grade. A familiar style can coexist with poor execution; a different style can be effective.')
    payload = compare_season_player(player, snapshot, fixture, references, role)
    payload['unavailable_references'] = [r for r in unavailable_references if r['role']==role]
    if payload.get('reference_kind')=='match_sample':
        st.info('CDM reference coverage: selected 2003/04 Premier League matches — Keane 2, Vieira 3, Makélélé 2. These are small match samples, not season or career averages.')
        st.caption('Historical pass, tackle-duel, interception and ball-recovery events come from StatsBomb Open Data. Exact equivalence to the current ESPN summary definitions is unverified; long-pass rates are omitted.')
    if payload['availability']:
        st.info(payload['availability'])
        if payload.get('interpretation_available'):
            render_story(payload,live,stale)
            st.image(wheel(payload),width='stretch')
            st.caption('Recorded performance only. No legend mixture or historical scale is inferred from missing references.')
        choices=dict(payload['references'])
        choices.update({r['player']:r for r in payload['unavailable_references']})
        if choices:
            from pl_dna.historical import sourced_season_card
            selected=st.selectbox('Explore a retired legend card',list(choices),key='season_reference')
            st.html(sourced_season_card(choices[selected]['inspiration']))
    else:
        if payload['fit_status']=='no_clear_match':
            st.info('No clear match to the loaded legend profiles for this performance.')
            st.caption('The candidate mix leaves large differences under the current display checks, so blend percentages are hidden. This does not mean the player performed poorly.')
        else:
            st.markdown('#### Closest reference mix — exploratory estimate')
            for col, (name, pct) in zip(st.columns(len(payload['references'])), payload['fit']['percentages'].items()):
                col.metric(name, f'{pct}%')
                r = payload['references'][name]
                col.caption(f"{r['season']} · {r['minutes']:g} PL minutes")
            st.caption('Reference-scaled fit weights, not probabilities, career resemblance scores or ability ratings. Passing provisional display checks does not validate a style match. A 100% weight is not a perfect match.')
        render_story(payload, live, stale)
        left, right = st.columns([1.5,1], gap='large')
        with left:
            st.image(wheel(payload), width='stretch')
            st.caption(f"Scaled fit residual: {payload['fit']['rmse']:.3f}. Per-90 rates appear in the evidence table; the wheel uses a separate reference scale on each axis.")
        with right:
            choices = dict(payload['references'])
            choices.update({r['player']:r for r in payload['unavailable_references']})
            selected = st.selectbox('Explore a historical reference', list(choices), key='season_reference')
            r = choices[selected]
            st.markdown(f"**Reference: {r['player']} · {r['season']}**")
            from pl_dna.historical import sourced_season_card
            st.html(sourced_season_card(r['inspiration']))
            if r.get('unavailable'):
                st.info('Career facts only; this legend is not included in the fit. '+r['reason'])
            st.caption('Career card is context only. Its career totals and separately displayed peak-season facts do not enter the calculation.')
    with st.expander('Recorded counts, source checks & comparison method'):
        rows = []
        for k in ROLE_METRIC_ORDER(role):
            row = {'Measurement': FIELDS[k][0], 'Match count': snapshot['counts'].get(k),
                'Used in fit': 'fit' in payload and k in payload.get('metric_keys', [])}
            if k in payload.get('target_rates', {}):
                row['Match /90'] = payload['target_rates'][k]
                row.update({n+' /90': payload['reference_rates'][n][k] for n in payload['references']})
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')
        st.markdown(f"[Selected match statistics]({fixture['source_page']}) · [Selected player-stat response]({snapshot['source']['url']})")
        st.caption('Current match data: ESPN public website feed. Historical sources: Premier League website season data or explicitly identified StatsBomb Open Data match samples. Website feeds may change; this is not an official data-service partnership.')
        if payload.get('reference_kind')=='match_sample':
            st.image(str(Path(__file__).parent/'data/statsbomb-logo.png'),width=140)
            st.markdown('[StatsBomb Open Data — source, attribution and licence](https://github.com/statsbomb/open-data)')
        st.caption('Some fields may use different provider conventions. Missing/disputed fields are omitted, never filled with zero. Cross-provider equivalence and the style-fit model have not been independently validated.')
        st.write('Method: per-90 counts, divided on each axis by the maximum rate among the selected reference seasons; nonnegative least-squares weights sum to one. Minutes and all included counts must be present. At least three shared metrics and 30 played minutes are required; these are display rules, not reliability guarantees.')
        for n, r in payload['references'].items():
            st.markdown(f"[{n} · {r['season']} · {r['minutes']:g} minutes]({r['source']['url']})")
            if r.get('reference_kind')=='match_sample':
                for match in r['matches']:
                    st.markdown(f"- [{match['date']} · {match['name']}]({match['event_source']['url']}) · {match['minutes']:g} played minutes")
        st.json({'match_source': entry['summary_source'], 'player_source': snapshot['source'],
                 'omitted_metrics': payload.get('omitted_metrics', []), 'fit_status':payload.get('fit_status'),
                 'fit_checks':payload.get('fit_checks'), 'unavailable_references':payload['unavailable_references'],
                 'limitations': payload['limitations']})
    st.download_button('Download this performance evidence', json.dumps(payload, indent=2, allow_nan=False),
        file_name='current_season_comparison.json', mime='application/json', key='current_evidence')


def ROLE_METRIC_ORDER(role):
    from pl_dna.season_feed import ROLE_METRICS
    return ROLE_METRICS[role]


def suggested_role(player, presets):
    if player['id'] in presets:
        return presets[player['id']]
    position = player.get('source_position','')
    if position=='Goalkeeper': return 'GK'
    if 'Back' in position: return 'FB'
    if 'Defender' in position: return 'CB'
    if 'Forward' in position:
        return 'WING' if 'Left' in position or 'Right' in position else 'ST'
    if 'Defensive' in position and 'Midfielder' in position: return 'CDM'
    if 'Attacking Midfielder' in position:
        return 'WING' if 'Left' in position or 'Right' in position else 'CAM'
    if 'Midfielder' in position: return 'CM'
    return None


@st.fragment(run_every=60)
def follow_live():
    today = datetime.now(ZoneInfo('Europe/London')).date()
    selected_day = st.date_input('Match date (UK)', today, min_value=calendar_date(2026,8,1), max_value=today, key='feed_match_date')
    date = selected_day.strftime('%Y%m%d')
    if selected_day != today:
        st.caption('Browsing an earlier 2026/27 matchday. Completed-match data is labelled full time; no live match is being simulated.')
    study = load_current()
    try:
        board, metadata = cached_scoreboard(date)
    except Exception:
        st.error('The match list could not be refreshed. No live status is claimed. Try reconnecting later.')
        return
    events = board.get('events', [])
    if not events:
        st.info('No Premier League fixtures are listed for this UK date. The connection will check again in 60 seconds while this view is open. The bundled recorded 2026/27 performances remain available in the other view.')
        st.caption('Last checked: '+metadata['checked_at'])
        return
    ids = [str(e['id']) for e in events]
    labels = {str(e['id']): f"{e['name']} · {e['status']['type']['description']}" for e in events}
    mid = st.selectbox('Premier League fixtures on the selected date', ids, format_func=labels.get, key='current_live_match')
    st.caption('Automatic feed check every 60 seconds while this view is open. The provider may lag; this is polling, not a guaranteed instant event feed.')
    try:
        summary, summary_source = cached_summary(mid)
        fixture = match_info(summary)
    except Exception:
        st.error('The selected fixture could not be refreshed. No current player analysis is shown.')
        return
    st.info(f"{fixture['status']} · {fixture['home']} {fixture['score']} {fixture['away']} · {fixture['clock']}")
    st.caption('Last fixture check: '+summary_source['checked_at'])
    players = roster_players(summary)
    if not players or fixture['state'] == 'pre':
        st.write('Waiting for kickoff and player statistics. No performance values are inferred.')
        return
    presets = {e['player']['id']: e['role'] for e in study['targets'].values()}
    by_id = {p['id']: p for p in players}
    pid = st.selectbox('Follow a player', list(by_id), format_func=lambda k: by_id[k]['name']+' · '+by_id[k]['team'], key='current_live_player')
    player = by_id[pid]
    default = suggested_role(player,presets)
    if st.session_state.get('role_player_context') != (mid, pid):
        st.session_state['current_live_role'] = default
        st.session_state['role_player_context'] = (mid, pid)
    role = st.selectbox('Reference position group', list(ROLE_LABELS), index=list(ROLE_LABELS).index(default) if default else None, format_func=ROLE_LABELS.get, key='current_live_role')
    st.caption(f"Source position: {player['source_position'] or 'unavailable'}. The suggested group is a broad mapping; choose the group that fits this match role.")
    if role is None:
        st.info('Select a reference position group to inspect this player.')
        return
    state_key = f'{mid}:{pid}'
    stale = False
    try:
        raw, source = cached_player(mid, player['team_id'], pid)
        snapshot = normalize_player(raw, source)
        age = source.get('http_age_seconds')
        stale = age is not None and float(age) > 120
        st.session_state['last_player_snapshot_'+state_key] = snapshot
    except Exception:
        stale = True
        snapshot = st.session_state.get('last_player_snapshot_'+state_key)
    if snapshot is None:
        st.warning('Player statistics are unavailable. No counts, wheel or comparison are fabricated.')
        return
    if stale:
        st.warning('Stale or unavailable player feed: showing the last retrieved snapshot, not a confirmed current performance. Automatic Microsoft stories are paused.')
    st.caption('Last player-stat check: '+snapshot['source']['checked_at'])
    if fixture['state'] == 'post':
        st.success('Full time — showing the source’s completed-match performance. Automatic AI generation has stopped; source corrections may still arrive.')
    render_performance(dict(player=player, snapshot=snapshot, fixture=fixture, role=role,
        summary_source=summary_source), study['references'], live=True, stale=stale,
        unavailable_references=study.get('unavailable_references',[]))


def render_current_dashboard():
    study = load_current()
    st.html('<div class="demo-badge">2026/27 Premier League · Recorded match statistics · Automatic live-feed option</div>')
    mode = st.radio('Match source', ['This season: recorded performances', 'Follow a live match'], horizontal=True, key='current_match_mode')
    if mode == 'This season: recorded performances':
        targets = study['targets']
        key = st.selectbox('Choose a position example from 2026/27', list(targets),
            format_func=lambda k: f"{ROLE_LABELS[targets[k]['role']]} — {targets[k]['player']['name']} · {targets[k]['player']['team']} · {targets[k]['fixture']['date'][:10]}", key='current_target')
        st.caption('Fixed source snapshots, not live or interpolated replays. '+study['selection'])
        render_performance(targets[key], study['references'], unavailable_references=study.get('unavailable_references',[]))
    else:
        connected = st.toggle('Connect to the match feed', value=False, key='connect_live_feed')
        if connected:
            follow_live()
        else:
            st.write('Connect to fetch today’s fixtures and follow a player, or browse another date from this season. Match data and calculated comparisons refresh automatically every 60 seconds while this view is open. This uses public data reads; Microsoft AI calls remain separate and opt-in.')
