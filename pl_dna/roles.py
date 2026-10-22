"""Position-aware synthetic action scenarios, with invented style references.

This generates independent player action sequences, not a complete simulation
of possession, opposition movement, or match score. All coordinates are
normalized 0–100 with Northbridge attacking toward x=100. Goalkeeper defensive
actions occur near the own goal atx=0; opposing linked shots attack towardx=0. Each sequence is assigned wholly to
its initiating timestamp for window selection, avoiding split sequence counts.
Only events observed by the replay end are included; future follow-ups never
justify a chance-created measurement.
Reference values are illustrative counts per100 sequences, not historical data.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ROLE_DEFINITIONS = {
    "CB": {
        "label": "Centre-back",
        "metrics": {"Successful tackles": "tackle", "Interceptions": "interception", "Aerial duels won": "aerial_duel", "Blocks": "block", "Completed progressive passes": "progressive_pass"},
        "profiles": {"Defensive stopper": [25, 20, 15, 20, 8], "Aerial defender": [15, 12, 35, 15, 8], "Ball-playing defender": [12, 15, 15, 10, 30]},
        "legend_inspirations": {},
    },
    "FB": {
        "label": "Full-back",
        "metrics": {"Successful tackles": "tackle", "Interceptions": "interception", "Completed crosses": "cross", "Completed progressive carries": "progressive_carry", "Chances created": "chance_created"},
        "profiles": {"Defensive full-back": [30, 25, 8, 10, 5], "Defensive carrier": [22, 18, 10, 30, 8], "Creative full-back": [10, 10, 20, 18, 30]},
        "legend_inspirations": {},
    },
    "CM": {
        "label": "Central midfield",
        "metrics": {"Box arrivals": "box_arrival", "Shots": "shot", "Completed progressive passes": "progressive_pass", "Completed progressive carries": "progressive_carry", "Completed switches": "switch"},
        "profiles": {"Box-to-box attacker": [25, 20, 15, 20, 5], "Driving midfielder": [10, 8, 30, 30, 10], "Deep distributor": [3, 3, 25, 8, 35]},
        "legend_inspirations": {"Box-to-box attacker": "Lampard-inspired", "Driving midfielder": "Gerrard-inspired", "Deep distributor": "Scholes-inspired"},
    },
    "CAM": {
        "label": "Attacking midfielder",
        "metrics": {"Chances created": "chance_created", "Completed through balls": "through_ball", "Passes entering final third": "final_third_pass", "Box arrivals": "box_arrival", "Shots": "shot"},
        "profiles": {"Chance creator": [35, 25, 30, 5, 8], "Attacking playmaker": [25, 20, 25, 15, 20], "Advanced distributor": [20, 20, 40, 5, 8]},
        "legend_inspirations": {},
    },
    "ST": {
        "label": "Striker",
        "metrics": {"Shots": "shot", "Box arrivals": "box_arrival", "Aerial duels won": "aerial_duel", "Completed link-up passes": "link_up_pass", "Ball recoveries": "recovery"},
        "profiles": {"Penalty-area finisher": [35, 30, 8, 10, 5], "Target forward": [20, 15, 30, 25, 5], "Scoring and link-up forward": [32, 25, 5, 25, 8], "Link-up forward": [18, 15, 10, 35, 15]},
        "legend_inspirations": {},
    },
}
ROLE_DEFINITIONS["CB"]["legend_inspirations"] = {"Defensive stopper": "Terry-inspired", "Aerial defender": "Vidic-inspired", "Ball-playing defender": "Van Dijk-inspired"}
ROLE_DEFINITIONS["FB"]["legend_inspirations"] = {"Defensive full-back": "Ashley Cole-inspired", "Defensive carrier": "Kyle Walker-inspired", "Creative full-back": "Alexander-Arnold-inspired"}
ROLE_DEFINITIONS["CAM"]["legend_inspirations"] = {"Chance creator": "Ozil-inspired", "Attacking playmaker": "De Bruyne-inspired", "Advanced distributor": "Fabregas-inspired"}
ROLE_DEFINITIONS["ST"]["legend_inspirations"] = {"Penalty-area finisher": "Shearer-inspired", "Target forward": "Drogba-inspired", "Scoring and link-up forward": "Henry-inspired", "Link-up forward": "Rooney-inspired"}
ROLE_DEFINITIONS["GK"] = {
    "label": "Goalkeeper",
    "metrics": {"Saves": "save", "Successful claims": "claim", "Sweeper interventions": "sweeper_intervention", "Completed progressive passes": "progressive_pass", "Completed long distribution": "long_distribution"},
    "profiles": {"Shot stopper": [35, 20, 8, 10, 15], "Area-command keeper": [30, 30, 10, 12, 18], "Sweeper keeper": [20, 12, 30, 25, 15]},
    "legend_inspirations": {"Shot stopper": "Schmeichel-inspired", "Area-command keeper": "Cech-inspired", "Sweeper keeper": "Alisson-inspired"},
}
ROLE_DEFINITIONS["WING"] = {
    "label": "Winger",
    "metrics": {"Successful take-ons": "take_on", "Completed crosses": "cross", "Completed progressive carries": "progressive_carry", "Shots": "shot", "Chances created": "chance_created"},
    "profiles": {"Direct goalscorer": [20, 10, 20, 35, 10], "Dribbling creator": [35, 15, 30, 15, 20], "Inside forward": [20, 8, 25, 30, 20]},
    "legend_inspirations": {"Direct goalscorer": "Ronaldo-inspired", "Dribbling creator": "Hazard-inspired", "Inside forward": "Salah-inspired"},
}
ROLE_DEFINITIONS["CDM"] = {
    "label": "Defensive midfield",
    "metrics": {"Successful tackles": "tackle", "Interceptions": "interception", "Ball recoveries": "recovery", "Completed progressive passes": "progressive_pass", "Completed switches": "switch"},
    "profiles": {"Ball winner": [30, 30, 25, 10, 5], "Holding anchor": [25, 30, 30, 15, 5], "Deep controller": [10, 18, 18, 30, 30]},
    "legend_inspirations": {"Ball winner": "Kante-inspired", "Holding anchor": "Makelele-inspired", "Deep controller": "Rodri-inspired"},
}
# Names are optional design inspirations only; no historical data calibrates them.
PLAYERS = {"Noah Bennett": "CB", "Leo Serrano": "FB", "Alex Morganfield": "CM", "Diego Mercer": "CAM", "Sam Okafor": "ST", "Ethan Vale": "GK", "Mateo Silva": "WING", "Owen Reed": "CDM"}
METRIC_DEFINITIONS = {
    "tackle": "Explicit tackle event with outcome won.",
    "interception": "Explicit interception event with outcome retained.",
    "aerial_duel": "Explicit aerial duel event with outcome won.",
    "block": "Explicit block event with outcome blocked.",
    "cross": "Explicit cross event with outcome completed.",
    "chance_created": "Explicit completed key pass followed by a synthetic teammate shot in the same sequence.",
    "take_on": "Explicit take-on event with outcome won.",
    "shot": "Any explicit shot event, regardless of outcome.",
    "box_arrival": "Explicit off-ball arrival from outside to inside x>=84 and21<=y<=79.",
    "progressive_pass": "Completed pass reducing normalized distance to (100,50) by at least25%.",
    "progressive_carry": "Completed carry reducing normalized distance to (100,50) by at least25%.",
    "switch": "Completed pass across y=50 with lateral displacement>=50 normalized units.",
    "link_up_pass": "Completed pass explicitly tagged link_up in the synthetic scenario.",
    "recovery": "Explicit loose-ball recovery event with outcome retained.",
    "through_ball": "Completed forward pass (end_x>start_x) explicitly tagged through_ball in the synthetic scenario; the tag is scenario annotation, not an inference about real defenders.",
    "final_third_pass": "Completed pass from start_x<66.6667 to end_x>=66.6667.",
    "save": "Explicit successful goalkeeper save with outcome saved, supported by an earlier opposing shot with outcome saved in the same sequence. No save percentage is inferred.",
    "claim": "Explicit goalkeeper aerial claim with outcome claimed.",
    "sweeper_intervention": "Explicit goalkeeper intervention with start_x>16 (outside the own penalty area) and outcome retained.",
    "long_distribution": "Completed goalkeeper pass tagged distribution traveling at least30 normalized coordinate units.",
}


def generate_role_events(seed=42):
    """Generate60 independent action sequences per player with explicit outcomes."""
    rng = np.random.default_rng(seed)
    rows = []
    def add(player, role, sequence, sequence_minute, minute, kind, coords, completed, outcome, tag=None, team="Northbridge FC"):
        rows.append(dict(player=player, role=role, team=team, sequence_id=sequence,
                         sequence_minute=float(sequence_minute), minute=float(minute), event_type=kind,
                         start_x=float(coords[0]), start_y=float(coords[1]), end_x=float(coords[2]),
                         end_y=float(coords[3]), completed=bool(completed), outcome=outcome,
                         shot_outcome=outcome if kind=="shot" else None, action_tag=tag, synthetic=True))
    for player, role in PLAYERS.items():
        metrics=list(ROLE_DEFINITIONS[role]["metrics"].values())
        if role=="CAM":
            # Retain the previous combined-role RNG draw schedule, then map its
            # scenarios into explicit central-creation actions below. This keeps
            # every other existing player's generated raw action values stable.
            metrics=["chance_created","cross","take_on","shot","progressive_carry"]
        times=np.sort(rng.uniform(.1,89.8,60))
        for number,t in enumerate(times,1):
            seq=f"{role}_SEQ_{number:03d}"
            # Deliberate scripted mixture evolves by phase; not an inferred tactic.
            weights=np.array([3,2,1,1,1] if t<30 else ([1,2,3,2,1] if t<60 else [1,1,2,2,3]),dtype=float)
            kind=str(rng.choice(metrics,p=weights/weights.sum()))
            sy=float(rng.uniform(25,75)); sx=float(rng.uniform(20,60))
            coords=(sx,sy,sx+5,sy); completed=bool(rng.random()<.78)
            outcome="won" if completed else "lost"; tag=None; event=kind
            if kind in ("interception","recovery"):
                outcome="retained" if completed else "not_retained"
            elif kind=="block":
                outcome="blocked" if completed else "missed"
            elif kind in ("progressive_pass","progressive_carry"):
                event="pass" if kind=="progressive_pass" else "carry"
                coords=(5,50,40,sy) if role=="GK" else (sx,sy,min(95,sx+30),50)
                outcome="completed" if completed else "incomplete"
            elif kind=="save":
                coords=(5,50,5,50); outcome="saved" if completed else "conceded"
                add("Opposition synthetic shooter", "ST", seq, t, t-.01,
                    "shot", (15,50,0,50), not completed,
                    "saved" if completed else "goal", "opponent_shot", "Southbank FC")
            elif kind=="claim":
                coords=(8,sy,8,sy); outcome="claimed" if completed else "missed"
            elif kind=="sweeper_intervention":
                coords=(20,sy,25,sy); outcome="retained" if completed else "missed"
            elif kind=="long_distribution":
                event="pass"; coords=(5,50,55,sy); tag="distribution"
                outcome="completed" if completed else "incomplete"
            elif kind=="switch":
                event="pass"; coords=(sx,15,sx+8,85); tag="switch"
                outcome="completed" if completed else "incomplete"
            elif kind=="link_up_pass":
                event="pass";coords=(80,sy,72,50);tag="link_up"
                outcome="completed" if completed else "incomplete"
            elif kind=="cross":
                coords=(78,8,91,50);outcome="completed" if completed else "incomplete"
            elif kind=="chance_created":
                event="pass";coords=(70,sy,90,50);tag="key_pass"
                outcome="completed" if completed else "incomplete"
            elif kind=="box_arrival":
                coords=(78,sy,90,sy); completed=True;outcome="arrived"
            elif kind=="shot":
                coords=(90,sy,100,50)
                outcome=str(rng.choice(["goal","saved","off_target","blocked"],p=[.12,.35,.33,.2]))
                completed=outcome=="goal"
            if role=="CAM":
                if kind=="cross":
                    event="pass"; coords=(60,sy,90,50); tag="through_ball"
                    outcome="completed" if completed else "incomplete"
                elif kind=="take_on":
                    event="pass"; coords=(55,sy,75,sy); tag="final_third"
                    outcome="completed" if completed else "incomplete"
                elif kind=="progressive_carry":
                    event="box_arrival"; coords=(78,sy,90,sy)
                    completed=True; outcome="arrived"; tag=None
            add(player,role,seq,t,t,event,coords,completed,outcome,tag)
            if kind=="chance_created" and completed:
                # The receiver's shot is evidence that the pass created a chance;
                # do not credit that shot to the creator.
                add(f"{role} synthetic receiver",role,seq,t,t+.02,"shot",(90,50,100,50),False,"saved","teammate_shot")
    result=pd.DataFrame(rows).sort_values(["minute","player"],kind="stable").reset_index(drop=True)
    result.insert(0,"event_id",[f"ROLE_{i:04d}" for i in range(1,len(result)+1)])
    return result


def _selected(data,player,start,end):
    if not np.isfinite([start,end]).all() or start<0 or start>=end:
        raise ValueError("Window must be finite with0<=start<end.")
    if player not in PLAYERS or player not in data.player.values:
        raise ValueError(f"Unknown demo player: {player}")
    player_rows=data.loc[data.player.eq(player)]
    if not player_rows.role.eq(PLAYERS[player]).all():
        raise ValueError("Player events contain an inconsistent role.")
    return player_rows.loc[player_rows.sequence_minute.gt(start)&player_rows.sequence_minute.le(end)&player_rows.minute.le(end)].copy()


def analyze_role_player(data,player,start=0,end=90):
    """Return role-specific counts with traceable event IDs in(start,end]."""
    d=_selected(data,player,start,end); role=PLAYERS[player]
    start_dist=np.hypot(100-d.start_x,50-d.start_y)
    end_dist=np.hypot(100-d.end_x,50-d.end_y)
    progressive=(start_dist-end_dist)/start_dist.replace(0,np.nan)>=.25
    conditions={}
    supporting_evidence={}
    for label,kind in ROLE_DEFINITIONS[role]["metrics"].items():
        if kind=="progressive_pass": mask=d.event_type.eq("pass")&d.completed&progressive
        elif kind=="progressive_carry": mask=d.event_type.eq("carry")&d.completed&progressive
        elif kind=="switch":
            mask=d.event_type.eq("pass")&d.completed&(abs(d.end_y-d.start_y)>=50)&((d.start_y-50)*(d.end_y-50)<0)
        elif kind=="link_up_pass": mask=d.event_type.eq("pass")&d.completed&d.action_tag.eq("link_up")
        elif kind=="through_ball":
            mask=d.event_type.eq("pass")&d.completed&d.outcome.eq("completed")&d.action_tag.eq("through_ball")&d.end_x.gt(d.start_x)
        elif kind=="final_third_pass":
            mask=d.event_type.eq("pass")&d.completed&d.outcome.eq("completed")&d.start_x.lt(100*2/3)&d.end_x.ge(100*2/3)
        elif kind=="chance_created":
            shots=data.loc[data.action_tag.eq("teammate_shot")&data.event_type.eq("shot")&data.minute.le(end)]
            supported=d.apply(lambda row: bool((shots.sequence_id.eq(row.sequence_id)
                &shots.player.ne(row.player)&shots.team.eq(row.team)
                &shots.minute.ge(row.minute)).any()),axis=1) if len(d) else pd.Series(False,index=d.index)
            mask=d.event_type.eq("pass")&d.completed&d.outcome.eq("completed")&d.action_tag.eq("key_pass")&supported
            supporting_evidence[label]=list(dict.fromkeys(
                event_id for _,row in d.loc[mask].iterrows()
                for event_id in shots.loc[shots.sequence_id.eq(row.sequence_id)
                    &shots.player.ne(row.player)&shots.team.eq(row.team)
                    &shots.minute.ge(row.minute),"event_id"].tolist()
            ))
        elif kind=="save":
            shots=data.loc[data.event_type.eq("shot")&data.action_tag.eq("opponent_shot")
                           &data.outcome.eq("saved")&data.minute.le(end)]
            def supporting_shots(row):
                return shots.loc[shots.sequence_id.eq(row.sequence_id)
                    &shots.player.ne(row.player)&shots.team.ne(row.team)
                    &shots.minute.lt(row.minute),"event_id"].tolist()
            linked=d.apply(lambda row: bool(supporting_shots(row)),axis=1) if len(d) else pd.Series(False,index=d.index)
            mask=d.event_type.eq("save")&d.completed&d.outcome.eq("saved")&linked
            supporting_evidence[label]=list(dict.fromkeys(
                event_id for _,row in d.loc[mask].iterrows() for event_id in supporting_shots(row)))
        elif kind=="long_distribution":
            distance=np.hypot(d.end_x-d.start_x,d.end_y-d.start_y)
            mask=d.event_type.eq("pass")&d.completed&d.outcome.eq("completed")&d.action_tag.eq("distribution")&distance.ge(30)
        elif kind=="sweeper_intervention":
            # Own penalty area ends atx16 on the normalized pitch.
            mask=d.event_type.eq(kind)&d.completed&d.outcome.eq("retained")&d.start_x.gt(16)
        elif kind=="shot":mask=d.event_type.eq("shot")
        elif kind=="box_arrival":
            start_box=d.start_x.ge(84)&d.start_y.between(21,79)
            end_box=d.end_x.ge(84)&d.end_y.between(21,79)
            mask=d.event_type.eq(kind)&d.completed&~start_box&end_box
        else:
            expected={"tackle":"won","aerial_duel":"won","take_on":"won",
                      "interception":"retained","recovery":"retained",
                      "block":"blocked","cross":"completed","claim":"claimed"}[kind]
            mask=d.event_type.eq(kind)&d.completed&d.outcome.eq(expected)
        conditions[label]=mask
    return dict(player=player,role=role,start_minute_exclusive=start,end_minute_inclusive=end,
                recorded_events=int(len(d)),action_sequences=int(d.sequence_id.nunique()),
                data_type="synthetic demonstration",window_attribution="sequence start",
                measurements=[dict(measurement=k,count=int(v.sum()),event_ids=d.loc[v,"event_id"].tolist(),
                                   supporting_event_ids=supporting_evidence.get(k,[])) for k,v in conditions.items()])


def score_role_profiles(data,player,start=0,end=90,min_sequences=10):
    """Equal feature weights, fixed reference-max scales; independent0–100 scores."""
    if min_sequences<1:raise ValueError("min_sequences must be positive.")
    report=analyze_role_player(data,player,start,end)
    if report["action_sequences"]<min_sequences:
        return pd.DataFrame(columns=["weighted_distance","experimental_resemblance_score"])
    features={m["measurement"]:100*m["count"]/report["action_sequences"] for m in report["measurements"]}
    return score_role_features(report["role"], features)


def score_role_features(role, features):
    """Score explicit rates per100 sequences against fixed invented references."""
    if role not in ROLE_DEFINITIONS:
        raise ValueError(f"Unknown role: {role}")
    names=list(ROLE_DEFINITIONS[role]["metrics"])
    refs=pd.DataFrame.from_dict(ROLE_DEFINITIONS[role]["profiles"],orient="index",columns=names)
    observed=pd.Series(features).reindex(names).astype(float)
    if not np.isfinite(observed.to_numpy()).all() or observed.lt(0).any():
        raise ValueError("All role feature rates must be finite and nonnegative.")
    distance=np.sqrt(refs.sub(observed,axis=1).div(refs.abs().max().replace(0,1),axis=1).pow(2).mean(axis=1))
    return pd.DataFrame({"weighted_distance":distance,"experimental_resemblance_score":100/(1+distance)}).sort_values("experimental_resemblance_score",ascending=False)


def build_role_story_input(data,player,start=0,end=90,view="Match so far",min_sequences=10):
    report=analyze_role_player(data,player,start,end)
    scores=score_role_profiles(data,player,start,end,min_sequences)
    return dict(player=player,role=report["role"],view=view,window={"start_exclusive":start,"end_inclusive":end},
                action_sequences=report["action_sequences"],evidence=report,
                experimental_reference_scores=[{"reference":p,"experimental_score":round(float(r.experimental_resemblance_score),1)} for p,r in scores.iterrows()],
                audience="casual fan",language="English",instructions=["Write at most80 words using only supplied evidence.","Describe observed actions before invented archetype scores.","Scores are not historical similarity or probabilities.","Do not infer causes or changes without comparison evidence.","Mention synthetic demonstration.","Dimensions may overlap; never sum them as distinct actions."])
