"""Audience-aware, evidence-first football dashboard."""
import json
import math

import pandas as pd
import streamlit as st

from pl_dna.roles import (
    ROLE_DEFINITIONS, PLAYERS, METRIC_DEFINITIONS, analyze_role_player,
    build_role_story_input, generate_role_events, score_role_profiles,
)
from pl_dna.narrative import generate_narrative, SPANISH_METRICS
from pl_dna.presentation import AUDIENCES, player_header, profile_cards, insight_card
from pl_dna.dna_wheel import wheel_data, radar_svg, reference_card
from pl_dna.historical import season_facts, sourced_season_card, observed_wheel_svg

MIN_SEQUENCES = 10
STYLE = """<style>
.block-container {max-width:1180px;padding-top:2rem;padding-bottom:3rem;}
.brand-line {font-size:.74rem;font-weight:700;letter-spacing:.18em;color:#39dfbc;margin-bottom:.5rem;}
.demo-badge {display:inline-block;border:1px solid #37506d;border-radius:24px;padding:5px 13px;
 font-size:.76rem;color:#b8c8de;margin:0 0 1rem;}
.player-hero {display:flex;align-items:center;justify-content:space-between;gap:24px;
 border:1px solid #2b425e;border-radius:20px;padding:26px 30px;margin:14px 0 20px;
 background:linear-gradient(115deg,#14253f,#102b31);}
.player-hero h2 {font-size:2.05rem;line-height:1.2;padding:.4rem 0 .6rem;margin:0;color:#f3f6fc;}
.player-hero p {color:#d1deed;margin:0;}
.eyebrow {font-size:.67rem;letter-spacing:.13em;font-weight:700;color:#9eabc5;}
.hero-tag {font-size:.61rem;letter-spacing:.08em;color:#76c7b4;margin-top:18px;}
.position-pitch {flex:0 0 175px;margin:0;}.position-pitch svg {width:100%;display:block;}
.position-pitch figcaption {font-size:.63rem;text-align:center;color:#aec5c9;margin-top:6px;}
[data-testid="stMetric"] {border:1px solid #2b425e;border-radius:14px;padding:14px 18px;background:#101d30;}
[data-testid="stMetricLabel"] {color:#b4c3d8;}
.insight-card {border:1px solid #2e5d59;border-left:4px solid #39dfbc;border-radius:14px;
 padding:20px 24px;background:#10232d;margin:12px 0;}
.insight-card .eyebrow {color:#66e4cb;}.insight-card p {font-size:1.13rem;line-height:1.65;margin:10px 0 0;color:#f3f6fc;}
.profile-grid {display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:14px;margin:14px 0;}
.profile-card {padding:19px;border:1px solid #473969;border-radius:15px;background:linear-gradient(145deg,#1b223b,#221c36);}
.profile-card h4 {font-size:1.05rem;margin:12px 0 5px;padding:0;color:#f3f6fc;}
.profile-card p {font-size:.84rem;color:#bdc5dc;min-height:2.6em;margin:0 0 12px;}
.profile-score {font-size:1.8rem;font-weight:700;color:#d6c5ff;}.profile-score small {font-size:.8rem;color:#a5adc7;font-weight:400;}
.profile-score.muted {font-size:.85rem;min-height:43px;padding-top:12px;}
.score-track {height:6px;border-radius:8px;background:#35334d;margin-top:10px;overflow:hidden;}
.score-fill {height:100%;background:#b69aff;border-radius:8px;}
.dna-reference {border:1px solid #37506d;border-radius:18px;padding:24px;min-height:360px;}
.dna-reference h3 {font-size:1.8rem;color:#f3f6fc;padding:12px 0 8px;margin:0;}
.dna-reference p {color:#d1deed;font-size:.93rem;line-height:1.65;}
.dna-status {display:inline-block;margin:12px 0;padding:6px 10px;border:1px solid #5b527d;border-radius:20px;color:#d6c5ff;font-size:.65rem;letter-spacing:.07em;}
.dna-reference dl {margin:20px 0;}.dna-reference dt {font-size:.72rem;color:#9eabc5;margin-top:14px;}
.dna-reference dd {font-size:.86rem;color:#f3f6fc;margin:4px 0 0;}
.dna-reference .dna-note {font-size:.78rem;color:#b8c8de;}
.season-facts {display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0;}
.season-fact {background:#09111f66;border:1px solid #52617a;border-radius:12px;padding:12px 8px;text-align:center;}
.season-fact strong {display:block;color:#f3f6fc;font-size:1.65rem;}.season-fact span {display:block;color:#d1deed;font-size:.65rem;}
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
    st.subheader({"Fan": "What did they contribute?", "Broadcaster": "Broadcast desk", "Expert": "Claim selection & checks"}[audience])
    language_col, source_col = st.columns([1, 2])
    language = language_col.selectbox("Insight language", ["English", "Spanish"], key="insight_language")
    mode = source_col.radio("Insight source", ["Local calculated summary", "Microsoft AI"], horizontal=True, key="insight_source")
    context_key = (player, start, end, language, mode, audience)
    package["audience"] = audience.lower()
    package["language"] = language
    if st.button("Generate insight", type="primary", key="generate_insight"):
        provider = None
        if mode == "Microsoft AI":
            try:
                from pl_dna.microsoft_provider import create_provider_from_env
                provider = create_provider_from_env()
            except Exception:
                st.warning("Microsoft AI is not configured. Showing a local calculated summary.")
        with st.spinner("Checking evidence and preparing insight…"):
            result = generate_narrative(package, provider=provider, language=language)
        st.session_state["insight_result"] = {"context": context_key, "result": result}
    saved = st.session_state.get("insight_result")
    # Automatic previews stay local; only the explicit button can call a model.
    result = saved["result"] if saved and saved["context"] == context_key else generate_narrative(package, language=language)
    st.html(insight_card(result["text"], audience))
    if result["status"] == "verified":
        st.caption("Microsoft-selected claims passed evidence checks · controlled wording.")
    else:
        st.caption("Local calculated summary · no model-generated wording.")
        if saved and saved["context"] == context_key and mode == "Microsoft AI":
            st.info("Live Microsoft AI was unavailable or its claims failed validation. The summary above uses the local fallback.")
    if mode == "Microsoft AI":
        st.caption("Generate insight sends this window’s synthetic evidence to your configured Azure model and may incur usage charges. A fresh preview stays local until a model result is accepted.")
    if audience == "Broadcaster":
        st.markdown("#### Supporting facts")
        for claim in result["claims"]:
            label = SPANISH_METRICS.get(claim["measurement"], claim["measurement"]) if language == "Spanish" else claim["measurement"]
            if claim["count"]:
                fact = f"{claim['count']} · {label}"
            else:
                fact = f"Sin eventos registrados · {label}" if language == "Spanish" else f"No recorded events · {label}"
            st.write(f"**{fact}**")
            st.caption("Evidence: " + (", ".join(claim["event_ids"]) or "No recorded events"))
            if claim["supporting_event_ids"]:
                st.caption("Supporting events: " + ", ".join(claim["supporting_event_ids"]))
        with st.expander("Copy talking point"):
            st.code(result["text"], language=None, wrap_lines=True)
        st.caption("Editorial note: synthetic demonstration; one window does not establish a change in tactics or form.")
    with st.expander("Insight evidence checks", expanded=audience == "Expert"):
        st.json({key: result[key] for key in ("status", "source", "reason", "claims")})


def render_profiles(events, player, start, end, role_config, sequences, expert=False):
    st.subheader("Player DNA")
    profile = st.selectbox("Compare with a legend-inspired reference", list(role_config["profiles"]),
                           format_func=lambda key: role_config.get("legend_inspirations", {}).get(key, key),
                           key="dna_reference")
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
        st.html(reference_card(role_config, profile, rows, show_observed=enough) if illustrative else sourced_season_card(name))
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
        st.bar_chart(counts.set_index("measurement"), horizontal=True, color="#39dfbc", x_label="Recorded count")
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
    st.html('<div class="demo-badge">Synthetic demo · Fictional players · Invented profiles</div>')
    audience = st.radio("Audience view", list(AUDIENCES), horizontal=True, key="audience")
    st.caption(AUDIENCES[audience])
    events = st.cache_data(generate_role_events)(seed=42)
    controls = st.columns([2, 2, 2, 3])
    role = controls[0].selectbox("Position", list(ROLE_DEFINITIONS), index=2,
                                format_func=lambda key: ROLE_DEFINITIONS[key]["label"], key="position")
    definition = ROLE_DEFINITIONS[role]
    player = controls[1].selectbox("Player", sorted(name for name, code in PLAYERS.items() if code == role))
    view = controls[2].radio("View", ["Match so far", "Last 15 minutes"], horizontal=True, key="window_view")
    end = controls[3].slider("Match minute", 1, 90, 43, key="minute")
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
    overview, evidence, method = st.tabs(["Analysis & rates" if audience == "Expert" else "Player overview", "Evidence explorer", "How it works"])
    with overview:
        if audience == "Expert":
            render_contributions(report, expert=True)
            render_profiles(events, player, start, end, definition, report["action_sequences"], expert=True)
            render_insight(package, audience, player, start, end)
        else:
            render_insight(package, audience, player, start, end)
            if audience == "Fan":
                render_profiles(events, player, start, end, definition, report["action_sequences"])
                render_contributions(report)
            else:
                render_contributions(report)
                with st.expander("Explore invented style profiles"):
                    render_profiles(events, player, start, end, definition, report["action_sequences"])
    with evidence:
        render_evidence(events, selected, report, package, player, start, end, definition, audience == "Expert")
    with method:
        st.subheader("The model, explained")
        st.markdown("""
        **One evidence base, three views.** Fan leads with a simple summary and profile cards.
        Broadcaster adds a copy-ready talking point and the supporting facts. Expert leads
        with counts, rates, distances and definitions. Audience selection changes presentation;
        it does not change calculated measurements or scores. Insight wording supports English and Spanish.

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

        **Historical season facts.** Selected PL seasons are loaded for Lampard, Gerrard, Scholes,
        Drogba, Hazard and Fabregas, with source links and selection criteria. These full-season
        totals are shown separately and never passed to the wheel or similarity formula: the
        definitions and denominators do not match. Missing or unresolved fields remain unavailable.
        Scoring peaks are not claims of best overall playing style; Fabregas uses a Chelsea-era
        creative peak. A historical polygon and numerical index remain unavailable until comparable
        event metrics are sourced. No combination of career-high statistics is used.

        **Insight provenance.** Local previews use fixed templates and calculated evidence.
        Microsoft mode requires a deployed model and server configuration. Only Generate insight
        triggers a potentially billable request. Accepted model selections must copy counts and
        event IDs exactly; wording uses controlled templates. Invalid or unavailable output falls
        back to the local summary. Evidence consistency does not establish historical truth.
        """)
        with st.expander("Selected position: model configuration"):
            st.json(definition)


if __name__ == "__main__":
    main()
