"""Audience-aware, evidence-first football dashboard."""
import json
import math
import os
import time

import pandas as pd
import streamlit as st

from pl_dna.roles import (
    ROLE_DEFINITIONS, PLAYERS, METRIC_DEFINITIONS, analyze_role_player,
    build_role_story_input, generate_role_events, score_role_profiles,
)
from pl_dna.narrative import generate_narrative, SPANISH_METRICS
from pl_dna.presentation import player_header, profile_cards, insight_card
from pl_dna.dna_wheel import wheel_data, radar_svg, reference_card
from pl_dna.historical import season_facts, sourced_season_card, observed_wheel_svg

from pl_dna.synthetic_replay import advance_clock, synthetic_brief_payload, brief_fingerprint, auto_brief_due
from pl_dna.analyst_brief import generate_analyst_brief

MIN_SEQUENCES = 10
STYLE = """<style>
.stApp {background:radial-gradient(ellipse at 85% 0%,#4b145b66,transparent 48%),#21082f;}
[data-testid="stHeader"] {background:#21082ff2;}
[data-testid="stTabs"] [aria-selected="true"] {color:#ff72ad;}
button[kind="primary"] {background:#00ff85;color:#21082f;border-color:#00ff85;font-weight:700;}
button[kind="primary"]:hover {background:#80ffbd;color:#21082f;border-color:#80ffbd;}
.block-container {max-width:1180px;padding-top:2rem;padding-bottom:3rem;}
.brand-line::before {content:"";display:inline-block;width:32px;height:4px;background:linear-gradient(90deg,#00ff85 50%,#ff2882 50%);vertical-align:middle;margin-right:10px;}
.brand-line {font-size:.74rem;font-weight:700;letter-spacing:.18em;color:#00ff85;margin-bottom:.5rem;}
.demo-badge {display:inline-block;border:1px solid #694077;border-radius:24px;padding:5px 13px;
 font-size:.76rem;color:#d7c4df;margin:0 0 1rem;}
.player-hero {display:flex;align-items:center;justify-content:space-between;gap:24px;
 border:1px solid #61336e;border-radius:20px;padding:26px 30px;margin:14px 0 20px;
 background:linear-gradient(115deg,#37003c,#4b145b);}
.player-hero h2 {font-size:2.05rem;line-height:1.2;padding:.4rem 0 .6rem;margin:0;color:#f3f6fc;}
.player-hero p {color:#eee4f2;margin:0;}
.eyebrow {font-size:.67rem;letter-spacing:.13em;font-weight:700;color:#c8afd1;}
.hero-tag {font-size:.61rem;letter-spacing:.08em;color:#80ffbd;margin-top:18px;}
.position-pitch {flex:0 0 175px;margin:0;}.position-pitch svg {width:100%;display:block;}
.position-pitch figcaption {font-size:.63rem;text-align:center;color:#aec5c9;margin-top:6px;}
[data-testid="stMetric"] {border:1px solid #61336e;border-radius:14px;padding:14px 18px;background:#321044;}
[data-testid="stMetricLabel"] {color:#d7c4df;}
.insight-card {border:1px solid #694077;border-left:4px solid #00ff85;border-radius:14px;
 padding:20px 24px;background:#321044;margin:12px 0;}
.insight-card .eyebrow {color:#80ffbd;}.insight-card p {font-size:1.13rem;line-height:1.65;margin:10px 0 0;color:#f3f6fc;}
.profile-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:14px;margin:14px 0;}
.profile-card {padding:19px;border:1px solid #473969;border-radius:15px;background:linear-gradient(145deg,#321044,#3e124b);}
.profile-card h4 {font-size:1.05rem;margin:12px 0 5px;padding:0;color:#f3f6fc;}
.profile-card p {font-size:.84rem;color:#bdc5dc;min-height:2.6em;margin:0 0 12px;}
.profile-score {font-size:1.8rem;font-weight:700;color:#d6c5ff;}.profile-score small {font-size:.8rem;color:#a5adc7;font-weight:400;}
.profile-score.muted {font-size:.85rem;min-height:43px;padding-top:12px;}
.score-track {height:6px;border-radius:8px;background:#573063;margin-top:10px;overflow:hidden;}
.score-fill {height:100%;background:#b69aff;border-radius:8px;}
.dna-reference {border:1px solid #694077;border-radius:18px;padding:24px;min-height:360px;}
.dna-reference h3 {font-size:1.8rem;color:#f3f6fc;padding:12px 0 8px;margin:0;}
.dna-reference p {color:#eee4f2;font-size:.93rem;line-height:1.65;}
.dna-status {display:inline-block;margin:12px 0;padding:6px 10px;border:1px solid #5b527d;border-radius:20px;color:#d6c5ff;font-size:.65rem;letter-spacing:.07em;}
.dna-reference dl {margin:20px 0;}.dna-reference dt {font-size:.72rem;color:#c8afd1;margin-top:14px;}
.dna-reference dd {font-size:.86rem;color:#f3f6fc;margin:4px 0 0;}
.dna-reference .dna-note {font-size:.78rem;color:#d7c4df;}
.season-facts {display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0;}
.season-fact {background:#21082f66;border:1px solid #52617a;border-radius:12px;padding:12px 8px;text-align:center;}
.season-fact strong {display:block;color:#f3f6fc;font-size:1.65rem;}.season-fact span {display:block;color:#eee4f2;font-size:.65rem;}
.season-sources {padding-left:16px;font-size:.75rem;line-height:1.6;}.season-sources a {color:#93c5fd;}
@media(max-width:640px){
 .block-container {padding:1.2rem 1rem 2rem;}.player-hero {padding:20px;gap:12px;align-items:flex-start;}
 .player-hero h2 {font-size:1.55rem;}.player-hero p {font-size:.85rem;}.hero-tag{font-size:.53rem;}
 .position-pitch {flex-basis:92px;}.position-pitch figcaption{font-size:.55rem;}
 .profile-grid {grid-template-columns:1fr;}.profile-card p {min-height:0;}
 .insight-card {padding:17px;}.insight-card p {font-size:1rem;}
}
</style>"""


def render_insight(package, audience, player, start, end):
    st.subheader("What did they contribute?")
    language_col, source_col = st.columns([1, 2])
    language = language_col.selectbox("Insight language", ["English", "Spanish"], key="insight_language")
    mode = source_col.radio("Insight source", ["Local calculated summary", "Microsoft AI"], horizontal=True, key="insight_source")
    if mode == "Microsoft AI":
        focus = st.selectbox("Brief focus", ["Fan explanation", "Broadcast talking point"], key="synthetic_brief_focus")
        payload = synthetic_brief_payload(st.session_state["synthetic_events"],player,start,end,
            view=package["view"],language=language,focus=focus)
        with st.expander("Calculated snapshot · no AI call"):
            st.write(generate_narrative(package,language=language)["text"])
            for fact in payload["evidence"]:
                if fact.get("kind")=="window_change":st.write(fact["sentence"])
        from pl_dna.analyst_brief import calculated_profile_story
        profile_story=calculated_profile_story(payload)
        if profile_story:
            st.markdown("**Calculated style comparison · selected window**")
            st.write(profile_story)
            current_comparison=payload["illustrative_comparison"]
            for candidate in current_comparison["candidates"]:
                st.caption(f"{candidate['legend_label']} · independent illustrative score {candidate['score']}/100")
            with st.expander("Profile calculation and supporting dimensions"):
                st.write(current_comparison["score_meaning"])
                st.write(current_comparison["policy"])
                st.json(current_comparison["candidates"])
        if payload["availability"]:
            st.info(payload["availability"])
            return
        key = brief_fingerprint(payload)
        scope=(player,payload['role'],package['view'],language,focus)
        clicked = st.button("Generate Microsoft recap" if end==90 else "Generate Microsoft interpretation",
                            type="primary",key="synthetic_generate_brief")
        enabled = st.checkbox("Refresh Microsoft brief during replay",value=False,key="synthetic_auto_ai")
        st.caption("Potentially billable: one request per click. Optional replay updates are off by default and limited to one attempt every thirty seconds per browser session when the evidence changes. No calls on ordinary control changes while automatic updates are off.")
        now = time.monotonic()
        due = auto_brief_due(enabled,st.session_state.get("replay_playing",False),end,key,st.session_state,now)
        if clicked or due:
            st.session_state["synthetic_last_ai_attempt"]=now
            st.session_state["synthetic_last_ai_key"]=key
            try:
                from pl_dna.microsoft_provider import create_provider_from_env
                provider=create_provider_from_env()
            except Exception:
                result={"status":"fallback","reason":"Microsoft is not configured or enabled. The synthetic replay and calculated facts remain available."}
            else:
                with st.spinner("Interpreting observed synthetic events…"):
                    result=generate_analyst_brief(payload,provider)
            st.session_state["synthetic_ai_result"]={"key":key,"result":result,"scope":scope,"minute":end,"start":start}
        saved=st.session_state.get("synthetic_ai_result")
        replay_history=bool(saved and st.session_state.get('replay_playing') and saved.get('scope')==scope and saved.get('minute',end)<=end)
        if saved and (saved["key"]==key or replay_history):
            result=saved["result"]
            if result["status"]=="evidence_checked":
                st.subheader(result["headline"])
                st.html(insight_card(result["text"],"Broadcaster" if focus=="Broadcast talking point" else "Fan"))
                st.caption("Synthetic full-time recap · Microsoft AI" if saved.get('minute',end)==90 else "Synthetic match interpretation · Microsoft AI")
                st.caption(f"As of synthetic minute {saved.get('minute',end)} · evidence window ({saved.get('start',start)}, {saved.get('minute',end)}].")
                st.caption("Cited facts and format checked; the AI interpretation is not independently verified. This is fictional match data, not a real legend comparison.")
                if result.get("style_note"):st.caption(result["style_note"])
                with st.expander("Supporting facts & copy brief"):
                    for fact in result["facts"]:st.write(fact)
                    st.code(result["headline"]+"\n\n"+result.get("original_text",result["text"]),language=None,wrap_lines=True)
            else:st.info(result["reason"])
        else:
            st.caption("The brief will use only events observed by the current replay minute. Pause the replay to read a fixed-window interpretation.")
        st.download_button("Download synthetic AI evidence",json.dumps(payload,indent=2,allow_nan=False),
            file_name="synthetic_brief_evidence.json",mime="application/json",key="synthetic_brief_evidence")
        return
    context_key = (player, start, end, language, mode, audience)
    package["audience"] = audience.lower()
    package["language"] = language
    if st.button("Generate insight", type="primary", key="generate_insight"):
        with st.spinner("Preparing the calculated summary…"):
            result = generate_narrative(package, language=language)
        st.session_state["insight_result"] = {"context": context_key, "result": result}
    saved = st.session_state.get("insight_result")
    # Automatic previews stay local; only the explicit button can call a model.
    result = saved["result"] if saved and saved["context"] == context_key else generate_narrative(package, language=language)
    st.html(insight_card(result["text"], audience))
    st.caption("Local calculated summary · no model-generated wording.")
    with st.expander("Copy summary"):
        st.code(result["text"], language=None, wrap_lines=True)
    with st.expander("Insight evidence checks", expanded=audience == "Expert"):
        st.json({key: result[key] for key in ("status", "source", "reason", "claims")})


def render_profiles(events, player, start, end, role_config, sequences, expert=False):
    st.subheader("Player DNA")
    profile = st.selectbox("Compare with a legend-inspired reference", list(role_config["profiles"]),
                           format_func=lambda key: role_config.get("legend_inspirations", {}).get(key, key),
                           key=f"dna_reference_{role_config['label']}")
    report = analyze_role_player(events, player, start, end)
    rows = wheel_data(role_config, report, profile)
    enough = sequences >= MIN_SEQUENCES
    name = role_config.get("legend_inspirations", {}).get(profile, profile)
    illustrative = st.checkbox("Show invented reference overlay (design preview)", value=False, key="illustrative_overlay")
    st.caption("Synthetic performance wheel · Historical season facts shown separately · No validated legend similarity score")
    wheel, reference = st.columns([1.5, 1], gap="large")
    with wheel:
        scale_max = max(20, math.ceil(max(max(values) for values in role_config["profiles"].values()) / 20) * 20)
        svg = radar_svg(rows, player, name, show_observed=enough, scale_max=scale_max) if illustrative else observed_wheel_svg(rows, player, scale_max, enough)
        st.image(svg, width="stretch")
        st.caption("Teal solid: selected synthetic performance · Purple dashed: invented reference" if illustrative else "Teal: selected synthetic performance only. No historical polygon is drawn because comparable reference rates are not loaded.")
    with reference:
        st.html(sourced_season_card(name))
    with st.expander("Exact wheel values & scale", expanded=expert):
        table = pd.DataFrame(rows).rename(columns={"measurement": "Measurement", "count": "Recorded count",
            "observed_rate": "Selected rate / 100 sequences", "reference_rate": "Invented reference / 100 sequences"})
        if not enough:
            table["Selected rate / 100 sequences"] = None
        if not illustrative:
            table = table.drop(columns=["Invented reference / 100 sequences"])
        st.dataframe(table, hide_index=True, width="stretch")
        st.caption("Every axis uses counts per 100 recorded sequences on the same rate scale. Its baseline covers all illustrative profiles for this position; it expands if an observed rate exceeds it. Check the ring labels when changing windows. These are not percentiles, ability ratings or historical statistics. Higher is more frequent, not necessarily better. Measurements may overlap.")
    with st.expander("Historical source coverage", expanded=expert):
        historical = season_facts(name)
        if historical:
            st.write("These are full-season facts. They are not fed into the wheel, narrative provider or resemblance formula.")
            st.json(historical)
        else:
            st.write("Historical season data is not loaded for this legend. Missing values are unavailable, not zero.")
    scores = {}
    if enough:
        frame = score_role_profiles(events, player, start, end, min_sequences=MIN_SEQUENCES)
        scores = frame["experimental_resemblance_score"].to_dict()
    else:
        st.warning(f"Scores hidden: {sequences} recorded sequences. The provisional display threshold is {MIN_SEQUENCES}; it is not a validated reliability cutoff.")
    with st.expander("Other illustrative profiles"):
        st.html(profile_cards(role_config, scores, show_scores=expert or not enough))
        if expert:
            st.caption("Legacy experimental model scores / 100 · invented references · not historical similarity, quality, or percentages of a legend.")
            if scores:
                st.dataframe(frame.rename(columns={"weighted_distance": "Weighted distance", "experimental_resemblance_score": "Model score / 100"}), width="stretch")


def render_contributions(report, expert=False):
    st.subheader("Recorded contributions")
    counts = pd.DataFrame(report["measurements"])[["measurement", "count"]]
    if report["action_sequences"]:
        st.bar_chart(counts.set_index("measurement"), horizontal=True, color="#00ff85", x_label="Recorded count")
    else:
        st.info("No recorded events in this window. Move the timeline forward or select another player.")
    if expert:
        count = report["action_sequences"]
        counts["Per 100 sequences"] = (counts["count"] * 100 / count).round(2) if count else None
        st.dataframe(counts.rename(columns={"measurement": "Measurement", "count": "Count"}), hide_index=True, width="stretch")
        st.caption("Rates use recorded action sequences, not minutes or possession. Rates are unavailable when no sequences are recorded.")
    st.caption("Measurements can overlap within a sequence; do not add them as separate event totals.")


def render_evidence(events, selected, report, package, player, start, end, role_config, expert):
    st.subheader("Follow the evidence")
    st.write("Choose a measurement to inspect the actions behind its count.")
    if expert:
        definitions = [{"Measurement": label, "Rule": METRIC_DEFINITIONS[key]} for label, key in role_config["metrics"].items()]
        st.dataframe(definitions, hide_index=True, width="stretch")
    evidence = pd.DataFrame(report["measurements"])
    for field in ("event_ids", "supporting_event_ids"):
        evidence[field] = evidence[field].apply(lambda ids: ", ".join(ids) or "No recorded events")
    st.dataframe(evidence, hide_index=True, width="stretch")
    st.caption("Primary IDs credit this player’s action. Supporting IDs identify another player’s shot used for chance creation or save evidence.")
    measurement = st.selectbox("Inspect supporting events", ["All recorded events", *role_config["metrics"]], key="evidence_measurement")
    inspected = selected
    if measurement != "All recorded events":
        row = next(item for item in report["measurements"] if item["measurement"] == measurement)
        primary = row["event_ids"]
        secondary = row["supporting_event_ids"]
        inspected = events.loc[events["event_id"].isin(primary + secondary) & events["minute"].le(end)].copy()
        inspected["evidence_role"] = inspected["event_id"].map(lambda eid: "Selected player’s action" if eid in primary else "Supporting shot")
    if inspected.empty:
        st.write("No recorded events for this selection.")
    else:
        st.dataframe(inspected, hide_index=True, width="stretch")
        event_id = st.selectbox("Inspect an individual event", inspected["event_id"].tolist())
        with st.expander("Individual event details", expanded=expert):
            st.json(json.loads(inspected.loc[inspected["event_id"].eq(event_id)].iloc[0].to_json()))
    st.download_button("Download evidence package", json.dumps(package, indent=2, allow_nan=False),
                       file_name=f"{player.lower().replace(' ', '_')}_{start}_{end}_evidence.json", mime="application/json")


def main():
    st.set_page_config(page_title="Premier League DNA", page_icon="⚽", layout="wide")
    st.html(STYLE)
    st.html('<div class="brand-line">PREMIER LEAGUE DNA / MATCH EXPLORER</div>')
    st.title("Every player has a blend.")
    st.write("Explore the contribution. Understand the profile. Follow the evidence.")
    audience = "Fan"  # One public dashboard; this preserves the internal narrative schema.
    options = ["This season & live", "Eight-position synthetic demo"] if os.environ.get("PL_DNA_ENABLE_RESEARCH")=="1" else ["Eight-position synthetic demo"]
    source = st.radio("Data source",options,horizontal=True,key="data_source")
    if source == "This season & live":
        from pl_dna.current_dashboard import render_current_dashboard
        render_current_dashboard()
        return
    render_synthetic_dashboard()


def toggle_replay():
    playing=not st.session_state.get("replay_playing",False)
    if playing and st.session_state.get("minute",43)>=90:st.session_state["minute"]=1
    st.session_state["replay_playing"]=playing
    st.session_state["replay_last_tick"]=time.monotonic()


def reset_replay():
    st.session_state["replay_playing"]=False
    st.session_state["minute"]=1
    st.session_state.pop("synthetic_ai_result",None)


def pause_replay():
    st.session_state["replay_playing"]=False


@st.fragment(run_every=2)
def render_synthetic_dashboard():
    audience = "Fan"
    st.session_state.setdefault("minute",43)
    advance_clock(st.session_state,time.monotonic())
    st.html('<div class="demo-badge">Synthetic demo · Fictional players · Invented profiles</div>')
    events = st.cache_data(generate_role_events)(seed=42)
    st.session_state["synthetic_events"]=events
    replay_controls=st.columns([1,1,2])
    replay_controls[0].button("Pause replay" if st.session_state.get("replay_playing") else "Start replay",on_click=toggle_replay,key="replay_toggle")
    replay_controls[1].button("Reset replay",on_click=reset_replay,key="replay_reset")
    replay_controls[2].selectbox("Accelerated replay speed",[1,3,5],index=1,format_func=lambda n:f"{n} match minutes every two seconds",key="replay_step")
    st.caption("Controlled synthetic replay: events are released by simulated match minute. This is not a live Premier League feed. Pause or drag the timeline to inspect a fixed window.")
    controls = st.columns([2, 2, 2, 3])
    role = controls[0].selectbox("Position", list(ROLE_DEFINITIONS), index=2,
                                format_func=lambda key: ROLE_DEFINITIONS[key]["label"], key="position")
    definition = ROLE_DEFINITIONS[role]
    player = controls[1].selectbox("Player", sorted(name for name, code in PLAYERS.items() if code == role))
    view = controls[2].radio("View", ["Match so far", "Last 15 minutes"], horizontal=True, key="window_view")
    end = controls[3].slider("Match minute", 1, 90, value=None, key="minute",on_change=pause_replay)
    start = 0 if view == "Match so far" else max(0, end - 15)
    report = analyze_role_player(events, player, start, end)
    selected = events.loc[events["player"].eq(player) & events["sequence_minute"].gt(start) & events["sequence_minute"].le(end) & events["minute"].le(end)]
    package = build_role_story_input(events, player, start, end, view=view, min_sequences=MIN_SEQUENCES)
    package["audience"] = audience.lower()
    st.html(player_header(player, role, definition["label"], start, end, view))
    summary = st.columns(3)
    summary[0].metric("Recorded sequences", report["action_sequences"])
    summary[1].metric("Recorded events", report["recorded_events"])
    summary[2].metric("Selected window", f"{end-start} min")
    if end==90:st.success("Synthetic full time — complete performance available. Generate a Microsoft recap or use the calculated summary below.")
    with st.expander("Latest ingested synthetic events"):
        observed=events.loc[events.minute.le(end)].sort_values(["minute","event_id"])
        st.caption(f"{len(observed)} event rows observed across all generated players by minute {end}. Rows from future minutes are withheld.")
        st.dataframe(observed[["event_id","minute","player","event_type","outcome"]].tail(10),hide_index=True,width="stretch")
    overview, evidence, method = st.tabs(["Player overview", "Evidence explorer", "How it works"])
    with overview:
        render_insight(package, audience, player, start, end)
        render_profiles(events, player, start, end, definition, report["action_sequences"])
        with st.expander("Recorded contributions & rates"):
            render_contributions(report, expert=True)
    with evidence:
        render_evidence(events, selected, report, package, player, start, end, definition, audience == "Expert")
    with method:
        st.subheader("The model, explained")
        st.markdown("""
        **One dashboard.** The overview leads with the summary and player profiles. Copyable
        summaries, recorded contributions and detailed evidence are available under expanders
        and the Evidence explorer tab. Local summary wording supports English and Spanish.

        **Synthetic demonstration.** Eight fictional players cover eight position groups.
        These are independent action scenarios, not a possession-consistent full match.
        The pitch marker shows a schematic position, not a measured average position or heatmap.

        **Time windows.** The start minute is excluded and the end minute included. A sequence
        belongs to its start minute. Only events observed by the selected end minute are used;
        future teammate shots cannot support a chance-created measurement.

        **Measurements.** Coordinates run from 0 to 100 on each axis. A completed pass or carry
        is progressive when it reduces distance to the goal centre by at least 25%.
        Other measurements require explicit event types and outcomes. These are prototype definitions.

        **Invented profiles.** Rates per 100 recorded sequences are compared with invented
        references using equally weighted, scaled distances. Scores are independent, do not sum
        to 100, and cannot be compared across positions. Legend labels are design inspirations;
        these values are not historical player statistics or validated similarity estimates.
        The ten-sequence display threshold is provisional, not a statistical reliability guarantee.

        **Player DNA wheel.** Teal shows measured synthetic rates. An invented purple reference
        is available only through the explicit design-preview checkbox, off by default.
        No percentile or ability rating is inferred. Below ten sequences the observed shape is hidden.

        **Historical season facts.** Selected PL seasons are loaded for all 25 legends
        across eight positions, with source links and selection criteria. These full-season
        totals are shown separately and never passed to the wheel or similarity formula: the
        definitions and denominators do not match. Missing or unresolved fields remain unavailable.
        Scoring peaks are not claims of best overall playing style; Fabregas uses a Chelsea-era
        creative peak. A historical polygon and numerical index remain unavailable until comparable
        event metrics are sourced. No combination of career-high statistics is used.

        **Insight provenance.** Local summaries use calculated evidence and fixed wording.
        Select Microsoft AI in the synthetic demo to connect observed events to an analyst brief. It interprets the recorded
        performance using cited measurements. Exact supporting numbers are rendered locally.
        Citation and format checks do not independently verify the prose interpretation or
        establish validated historical similarity. Automatic AI updates are off by default.
        """)
        with st.expander("Selected position: model configuration"):
            st.json(definition)

if __name__ == "__main__":
    main()
