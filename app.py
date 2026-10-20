"""Premier League DNA: a local, evidence-first position-aware demonstration."""
import json

import pandas as pd
import streamlit as st

from pl_dna.roles import (
    ROLE_DEFINITIONS,
    PLAYERS,
    analyze_role_player,
    build_role_story_input,
    generate_role_events,
    score_role_profiles,
)

from pl_dna.narrative import generate_narrative

MIN_SEQUENCES = 10


def main():
    st.set_page_config(page_title="Premier League DNA", page_icon="⚽", layout="wide")
    st.markdown("""<style>
    .block-container {max-width:1180px;padding-top:2rem;}
    [data-testid="stMetric"] {border:1px solid #d9e2ed;border-radius:12px;padding:16px;}
    </style>""", unsafe_allow_html=True)
    st.caption("PREMIER LEAGUE DNA · WORKING PROTOTYPE")
    st.title("Every player has a blend.")
    st.write("Explore recorded contributions, compare invented role profiles, and follow the evidence.")
    st.info("Synthetic demonstration · Fictional players · Invented reference profiles. Scores are model outputs, not probabilities or verified historical comparisons. Legend names are design inspirations attached to invented role profiles.")

    events = st.cache_data(generate_role_events)(seed=42)
    controls = st.columns([2, 2, 2, 3])
    role = controls[0].selectbox("Position", list(ROLE_DEFINITIONS),
                                format_func=lambda key: ROLE_DEFINITIONS[key]["label"])
    role_config = ROLE_DEFINITIONS[role]
    inspirations = role_config.get("legend_inspirations", {})
    if inspirations:
        st.markdown("**Design inspirations for this position**")
        inspiration_columns = st.columns(len(inspirations))
        for column, (archetype, legend) in zip(inspiration_columns, inspirations.items()):
            column.markdown(f"**{legend}**  \n{archetype}")
        st.caption("Invented profiles inspired by familiar football stories. Reference values are not historical player statistics.")
    player = controls[1].selectbox("Player", sorted(name for name, code in PLAYERS.items() if code == role))
    view = controls[2].radio("View", ["Match so far", "Last 15 minutes"], horizontal=True)
    end = controls[3].slider("Match minute", min_value=1, max_value=90, value=43)
    start = 0 if view == "Match so far" else max(0, end - 15)
    selected = events.loc[events["player"].eq(player) & events["sequence_minute"].gt(start) & events["sequence_minute"].le(end) & events["minute"].le(end)]
    report = analyze_role_player(events, player, start, end)
    sequences = int(report["action_sequences"])
    st.subheader(f"{player} · {role_config['label']} · minutes ({start}, {end}]")
    st.caption("Windows use sequence start and include only events observed by the selected minute. The start minute is excluded; the end minute is included.")
    metrics = st.columns(3)
    metrics[0].metric("Recorded action sequences", sequences)
    metrics[1].metric("Recorded events", report["recorded_events"])
    metrics[2].metric("Window length", f"{end - start} min")

    package = build_role_story_input(events, player, start, end, view=view, min_sequences=MIN_SEQUENCES)
    blend_tab, evidence_tab, model_tab = st.tabs(["Style & activity", "Evidence explorer", "How it works"])
    with blend_tab:
        left, right = st.columns(2)
        with left:
            st.markdown("#### Experimental style scores")
            if sequences < MIN_SEQUENCES:
                st.warning(f"Scores hidden: {sequences} recorded sequences. The provisional display threshold is {MIN_SEQUENCES}; it is not a validated reliability cutoff.")
            else:
                scores = score_role_profiles(events, player, start, end, min_sequences=MIN_SEQUENCES)["experimental_resemblance_score"]
                st.bar_chart(scores.rename("Model score"), horizontal=True, x_label="Model score (0–100)", color="#7255dc")
                st.dataframe(scores.round(1).rename("Model score").to_frame(), width="stretch")
                st.caption("Each profile is scored independently. These values do not add to 100 and are not a percentage of a legend.")
        with right:
            st.markdown("#### Recorded contributions")
            counts_frame = pd.DataFrame(report["measurements"])[["measurement", "count"]]
            if sequences:
                st.bar_chart(counts_frame.set_index("measurement"), horizontal=True,
                             color="#208a83", x_label="Recorded events supporting measurement")
            else:
                st.write("No recorded events in this window. Move the timeline forward or select another player.")
            st.caption("Measurements can overlap and are not separate event totals. Position profiles use distinct measurement sets.")
        st.markdown("#### Match insight")
        narrative_controls = st.columns([1, 2])
        language = narrative_controls[0].selectbox("Insight language", ["English", "Spanish"])
        mode = narrative_controls[1].radio("Insight source", ["Local calculated summary", "Microsoft AI"], horizontal=True)
        st.caption("Local mode uses verified measurements and fixed text templates. Microsoft mode sends this window's synthetic evidence only when you press Generate insight, and may incur Azure usage charges.")
        context_key = (player, start, end, language, mode)
        if st.button("Generate insight", type="primary"):
            provider = None
            configuration_error = False
            if mode == "Microsoft AI":
                try:
                    from pl_dna.microsoft_provider import create_provider_from_env
                    provider = create_provider_from_env()
                    if provider is None:
                        configuration_error = True
                except Exception:
                    configuration_error = True
            if configuration_error:
                st.warning("Microsoft AI is not configured. Showing a local calculated summary.")
            with st.spinner("Checking the evidence and preparing insight…"):
                result = generate_narrative(package, provider=provider, language=language)
            st.session_state["insight_result"] = {"context": context_key, "result": result}
        saved = st.session_state.get("insight_result")
        if saved and saved["context"] == context_key:
            result = saved["result"]
            st.write(result["text"])
            if result["status"] == "verified":
                st.success("Microsoft-selected claims passed evidence checks. The wording uses controlled templates.")
            else:
                st.info("Local calculated summary · no model-generated wording.")
            with st.expander("Insight evidence checks"):
                st.json({key: result[key] for key in ("status", "source", "reason", "claims") if key in result})
        else:
            st.write("Generate an insight for the current player and match window.")

    with evidence_tab:
        st.write("Every measurement links to the events used to calculate it.")
        evidence = pd.DataFrame(report["measurements"])
        evidence["event_ids"] = evidence["event_ids"].apply(lambda ids: ", ".join(ids) or "No recorded events")
        evidence["supporting_event_ids"] = evidence["supporting_event_ids"].apply(lambda ids: ", ".join(ids) or "None")
        st.caption("Event IDs credit the selected player's action. Supporting IDs show another player's shot for chance creation or goalkeeper saves; those shots are not credited to the selected player.")
        st.dataframe(evidence, hide_index=True, width="stretch")
        metric_names = [row["measurement"] for row in report["measurements"]]
        measurement = st.selectbox("Inspect supporting events", ["All recorded events", *metric_names])
        inspected = selected
        if measurement != "All recorded events":
            evidence_row = next(row for row in report["measurements"] if row["measurement"] == measurement)
            primary_ids = evidence_row["event_ids"]
            secondary_ids = evidence_row.get("supporting_event_ids", [])
            inspected = events.loc[events["event_id"].isin(primary_ids + secondary_ids) & events["minute"].le(end)].copy()
            inspected["evidence_role"] = inspected["event_id"].map(
                lambda event_id: "Selected player's action" if event_id in primary_ids else "Supporting shot (not credited to selected player)"
            )
        if inspected.empty:
            st.write("No recorded events for this selection.")
        else:
            st.dataframe(inspected, hide_index=True, width="stretch")
            event_id = st.selectbox("Inspect an individual event", inspected["event_id"].tolist())
            event = inspected.loc[inspected["event_id"].eq(event_id)].iloc[0]
            st.json(json.loads(event.to_json()))
        st.download_button("Download evidence package", json.dumps(package, indent=2, allow_nan=False),
                           file_name=f"{player.lower().replace(' ', '_')}_{start}_{end}_evidence.json", mime="application/json")

    with model_tab:
        st.markdown("""
        **Current scope:** eight fictional players across goalkeeper, centre-back, full-back, defensive midfield, central midfield, attacking midfield, winger and striker roles. Each position has distinct measurements and invented reference profiles with legend-inspired design labels.

        **Measurement rules:** coordinates run from 0 to 100 in each direction. A completed pass or carry is progressive when it reduces distance to the goal centre by at least 25%. Other measurements use explicit event types and completion flags in the synthetic dataset. These are prototype definitions, not an official data provider's metrics.

        **Style model:** measurements per 100 recorded action sequences are compared with fixed, invented role reference rates using a weighted distance. Profiles and weights are design assumptions. Scores are not comparable across positions, do not sum to 100, and do not establish similarity to historical players.

        **Limits:** this is not a coherent full-match simulation, calibrated scouting tool, or validated historical comparison. Sequences are assigned by their start minute. Only events observed by the selected end minute are included; a created chance requires an observed follow-up shot. No tactical causes or meaningful change over time can be inferred from a single window.
        """)
        with st.expander("Selected position: model configuration"):
            st.json(role_config)
        st.caption("Microsoft mode requires a configured endpoint. Generated claims must match calculated evidence; invalid output falls back to a local summary.")


if __name__ == "__main__":
    main()
