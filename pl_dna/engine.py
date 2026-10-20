"""Deterministic synthetic midfield analysis extracted from the research notebook.

Coordinates use normalized 0–100 units, attacking toward (100, 50).
Progression is a >=25% reduction in normalized distance to that point.
References are invented design hypotheses, never historical calibration.
Windows select event timestamps in (start, end]; sequences spanning boundaries
may therefore appear in both windows. Coverage dimensions can overlap.
"""
import numpy as np
import pandas as pd


profile_groups = {
    "Lampard-inspired\nAttacking involvement": [
        "Box arrivals",
        "Shots",
        "Recorded box touches"
    ],
    "Gerrard-inspired\nProgression": [
        "Progressive passes",
        "Progressive carries",
        "Passes entering final third"
    ],
    "Scholes-inspired\nDistribution": [
        "Completed passes",
        "Completed switches",
        "Completed long passes"
    ]
}

def analyze_player(data, player, start_minute=0, end_minute=45):
    """Return measurements and evidence for (start_minute, end_minute]."""
    if start_minute >= end_minute:
        raise ValueError("Start minute must be before end minute.")
    if player not in data["player"].values:
        raise ValueError(f"Unknown player: {player}")

    d = data.loc[
        data["player"].eq(player)
        & data["minute"].gt(start_minute)
        & data["minute"].le(end_minute)
    ].copy()

    completed_pass = d["event_type"].eq("pass") & d["completed"]
    completed_carry = d["event_type"].eq("carry") & d["completed"]

    start_distance = np.hypot(100 - d["start_x"], 50 - d["start_y"])
    end_distance = np.hypot(100 - d["end_x"], 50 - d["end_y"])
    reduction = (
        (start_distance - end_distance)
        / start_distance.replace(0, np.nan)
    )

    start_box = d["start_x"].ge(84) & d["start_y"].between(21, 79)
    end_box = d["end_x"].ge(84) & d["end_y"].between(21, 79)

    lateral = abs(d["end_y"] - d["start_y"])
    distance = np.hypot(
        d["end_x"] - d["start_x"],
        d["end_y"] - d["start_y"]
    )
    crosses_center = (
        (d["start_y"].lt(50) & d["end_y"].gt(50))
        | (d["start_y"].gt(50) & d["end_y"].lt(50))
    )

    conditions = {
        "Box arrivals": (
            d["event_type"].eq("box_arrival")
            & d["completed"] & ~start_box & end_box
        ),
        "Shots": d["event_type"].eq("shot"),
        "Recorded box touches": d["event_type"].eq("touch") & start_box,
        "Progressive passes": completed_pass & reduction.ge(0.25),
        "Progressive carries": completed_carry & reduction.ge(0.25),
        "Passes entering final third": (
            completed_pass
            & d["start_x"].lt(100 * 2 / 3)
            & d["end_x"].ge(100 * 2 / 3)
        ),
        "Completed passes": completed_pass,
        "Completed switches": (
            completed_pass & crosses_center & lateral.ge(50)
        ),
        "Completed long passes": completed_pass & distance.ge(30)
    }

    return {
        "player": player,
        "start_minute_exclusive": start_minute,
        "end_minute_inclusive": end_minute,
        "recorded_events": len(d),
        "data_type": "synthetic demonstration",
        "measurements": [
            {
                "measurement": name,
                "count": int(condition.sum()),
                "event_ids": d.loc[condition, "event_id"].tolist()
            }
            for name, condition in conditions.items()
        ]
    }

def generate_midfield_events(seed=42):
    rng = np.random.default_rng(seed)
    rows = []

    # Probabilities: pass, carry, attacking sequence.
    player_settings = {
        "Alex Morganfield": [
            [0.80, 0.15, 0.05],  # Minutes 0–30: distribution emphasis
            [0.65, 0.25, 0.10],  # Minutes 30–60: more carrying
            [0.55, 0.25, 0.20],  # Minutes 60–90: more attacking
        ],
        "Ben Calder": [
            [0.85, 0.10, 0.05],
            [0.85, 0.10, 0.05],
            [0.85, 0.10, 0.05],
        ],
        "Diego Mercer": [
            [0.60, 0.30, 0.10],
            [0.60, 0.30, 0.10],
            [0.60, 0.30, 0.10],
        ],
    }

    def add_event(player, minute, kind, sx, sy, ex, ey,
                  completed, sequence_id, shot_outcome=None):
        rows.append({
            "minute": minute,
            "event_type": kind,
            "start_x": sx, "start_y": sy,
            "end_x": ex, "end_y": ey,
            "completed": completed,
            "shot_outcome": shot_outcome,
            "sequence_id": sequence_id,
            "player": player,
            "team": "Northbridge FC",
            "synthetic": True
        })

    for player, phases in player_settings.items():
        # Same number of action opportunities for each player.
        times = np.sort(rng.uniform(0.1, 89.8, size=60))

        for number, minute in enumerate(times, start=1):
            phase = min(int(minute // 30), 2)
            action = rng.choice(
                ["pass", "carry", "attack"],
                p=phases[phase]
            )
            sequence_id = f"{player.split()[0]}_SEQ_{number:03d}"

            sx = float(rng.uniform(25, 75))
            sy = float(rng.uniform(10, 90))

            if action == "pass":
                # Include occasional wide switches.
                if rng.random() < 0.20:
                    sy = float(rng.uniform(10, 20))
                    ey = float(rng.uniform(80, 90))
                    if rng.random() < 0.5:
                        sy, ey = ey, sy
                    ex = float(np.clip(sx + rng.uniform(-5, 20), 0, 100))
                else:
                    ex = float(np.clip(sx + rng.uniform(-15, 35), 0, 100))
                    ey = float(np.clip(sy + rng.uniform(-25, 25), 0, 100))

                add_event(
                    player, minute, "pass", sx, sy, ex, ey,
                    bool(rng.random() < 0.85), sequence_id
                )

            elif action == "carry":
                ex = float(np.clip(sx + rng.uniform(5, 30), 0, 100))
                ey = float(np.clip(sy + rng.uniform(-10, 10), 0, 100))

                add_event(
                    player, minute, "carry", sx, sy, ex, ey,
                    bool(rng.random() < 0.90), sequence_id
                )

            else:
                # Related events share a sequence ID.
                bx = float(rng.uniform(85, 95))
                by = float(rng.uniform(30, 70))

                add_event(
                    player, minute, "box_arrival",
                    78, by, bx, by, True, sequence_id
                )
                add_event(
                    player, minute + 0.02, "touch",
                    bx, by, bx, by, True, sequence_id
                )

                if rng.random() < 0.55:
                    outcome = rng.choice(
                        ["goal", "saved", "off_target", "blocked"],
                        p=[0.12, 0.35, 0.33, 0.20]
                    )
                    add_event(
                        player, minute + 0.04, "shot",
                        bx, by, 100, 50,
                        bool(outcome == "goal"),
                        sequence_id,
                        shot_outcome=str(outcome)
                    )

    result = pd.DataFrame(rows).sort_values(
        ["minute", "player"], kind="stable"
    ).reset_index(drop=True)

    result.insert(
        0, "event_id",
        [f"SYN_{i:04d}" for i in range(1, len(result) + 1)]
    )

    return result

def calculate_sequence_blend(data, player, start=0, end=90):
    report = analyze_player(data, player, start, end)

    selected = data.loc[
        data["player"].eq(player)
        & data["minute"].gt(start)
        & data["minute"].le(end)
    ]

    total_sequences = selected["sequence_id"].nunique()

    evidence_by_metric = {
        item["measurement"]: set(item["event_ids"])
        for item in report["measurements"]
    }

    rows = []

    for profile, measurements in profile_groups.items():
        supporting_ids = set().union(*[
            evidence_by_metric[measurement]
            for measurement in measurements
        ])

        supporting_sequences = selected.loc[
            selected["event_id"].isin(supporting_ids),
            "sequence_id"
        ].unique()

        rows.append({
            "player": player,
            "profile": profile.replace("\n", " — "),
            "supporting_sequences": len(supporting_sequences),
            "total_sequences": total_sequences,
            "sequence_coverage_pct": (
                round(100 * len(supporting_sequences)
                      / total_sequences, 1)
                if total_sequences else np.nan
            )
        })

    return pd.DataFrame(rows)

def build_change_evidence(data, player):
    periods = {
        "opening": (0, 30),
        "closing": (60, 90)
    }

    period_evidence = {}

    for label, (start, end) in periods.items():
        measurements = analyze_player(data, player, start, end)
        coverage = calculate_sequence_blend(data, player, start, end)

        period_evidence[label] = {
            "start_minute_exclusive": start,
            "end_minute_inclusive": end,
            "measurements": measurements["measurements"],
            "activity_dimensions": coverage[[
                "profile",
                "supporting_sequences",
                "total_sequences",
                "sequence_coverage_pct"
            ]].to_dict(orient="records")
        }

    opening = {
        row["profile"]: row["sequence_coverage_pct"]
        for row in period_evidence["opening"]["activity_dimensions"]
    }
    closing = {
        row["profile"]: row["sequence_coverage_pct"]
        for row in period_evidence["closing"]["activity_dimensions"]
    }

    changes = [
        {
            "profile": profile,
            "change_percentage_points": round(
                closing[profile] - opening[profile], 1
            )
        }
        for profile in opening
    ]

    return {
        "player": player,
        "data_type": "synthetic demonstration",
        "comparison": "Opening 30 minutes versus closing 30 minutes",
        "periods": period_evidence,
        "changes": changes,
        "interpretation_limits": [
            "Coverage measures activity, not historical similarity.",
            "Dimensions can overlap.",
            "Changes are descriptive, not statistically validated.",
            "Do not infer tactical causes from these events alone.",
            "Compare supporting counts as well as percentages."
        ]
    }

def validate_change_evidence(data, package):
    assert data["event_id"].is_unique, "Duplicate event IDs found."

    for period_name, period in package["periods"].items():
        valid_events = data.loc[
            data["player"].eq(package["player"])
            & data["minute"].gt(period["start_minute_exclusive"])
            & data["minute"].le(period["end_minute_inclusive"])
        ]

        valid_ids = set(valid_events["event_id"])
        total_sequences = valid_events["sequence_id"].nunique()

        for measurement in period["measurements"]:
            ids = measurement["event_ids"]

            assert len(ids) == len(set(ids)), (
                f"Duplicate evidence in {measurement['measurement']}"
            )
            assert measurement["count"] == len(ids), (
                f"Count mismatch in {measurement['measurement']}"
            )
            assert set(ids).issubset(valid_ids), (
                f"Invalid evidence in {period_name}"
            )

        for dimension in period["activity_dimensions"]:
            assert dimension["total_sequences"] == total_sequences
            assert 0 <= dimension["supporting_sequences"] <= total_sequences

            expected = (
                round(
                    100 * dimension["supporting_sequences"]
                    / total_sequences, 1
                )
                if total_sequences else np.nan
            )

            assert (
                pd.isna(expected)
                and pd.isna(dimension["sequence_coverage_pct"])
            ) or expected == dimension["sequence_coverage_pct"]

    return True

def build_style_features(data, player, start=0, end=90):
    report = analyze_player(data, player, start, end)

    selected = data.loc[
        data["player"].eq(player)
        & data["minute"].gt(start)
        & data["minute"].le(end)
    ]

    total_sequences = selected["sequence_id"].nunique()

    return {
        "player": player,
        "action_sequences": total_sequences,
        **{
            item["measurement"]: (
                100 * item["count"] / total_sequences
                if total_sequences else np.nan
            )
            for item in report["measurements"]
        }
    }

feature_names = [name for names in profile_groups.values() for name in names]

reference_profiles = pd.DataFrame({
    "Lampard-inspired": {
        "Box arrivals": 20,
        "Shots": 10,
        "Recorded box touches": 20,
        "Progressive passes": 10,
        "Progressive carries": 5,
        "Passes entering final third": 10,
        "Completed passes": 45,
        "Completed switches": 3,
        "Completed long passes": 8
    },
    "Gerrard-inspired": {
        "Box arrivals": 10,
        "Shots": 5,
        "Recorded box touches": 10,
        "Progressive passes": 20,
        "Progressive carries": 15,
        "Passes entering final third": 20,
        "Completed passes": 55,
        "Completed switches": 8,
        "Completed long passes": 15
    },
    "Scholes-inspired": {
        "Box arrivals": 3,
        "Shots": 2,
        "Recorded box touches": 3,
        "Progressive passes": 15,
        "Progressive carries": 3,
        "Passes entering final third": 15,
        "Completed passes": 75,
        "Completed switches": 15,
        "Completed long passes": 25
    }
}).T.reindex(columns=feature_names)

feature_weights = pd.Series({
    "Box arrivals": 1 / 6,
    "Shots": 1 / 6,
    "Recorded box touches": 0,
    "Progressive passes": 1 / 9,
    "Progressive carries": 1 / 9,
    "Passes entering final third": 1 / 9,
    "Completed passes": 1 / 9,
    "Completed switches": 1 / 9,
    "Completed long passes": 1 / 9
}).reindex(feature_names)

feature_scales = reference_profiles.abs().max(axis=0).replace(0, 1)

def score_style_profiles(features):
    """Compare one player's feature rates with each reference."""
    player_vector = pd.Series(features).reindex(feature_names).astype(float)

    if not np.isfinite(player_vector.to_numpy()).all():
        raise ValueError("All feature values must be finite.")

    scaled_difference = (
        reference_profiles.subtract(player_vector, axis="columns")
        .divide(feature_scales, axis="columns")
    )

    distances = np.sqrt(
        scaled_difference.pow(2)
        .multiply(feature_weights, axis="columns")
        .sum(axis=1)
    )

    return pd.DataFrame({
        "weighted_distance": distances,
        "experimental_resemblance_score": 100 / (1 + distances)
    }).sort_values(
        "experimental_resemblance_score", ascending=False
    )

dimension_features = {
    "Attacking": ["Box arrivals", "Shots", "Recorded box touches"],
    "Progression": [
        "Progressive passes",
        "Progressive carries",
        "Passes entering final third"
    ],
    "Distribution": [
        "Completed passes",
        "Completed switches",
        "Completed long passes"
    ]
}


def build_story_input(data, player, start=0, end=90, view="Match so far",
                      min_sequences=10):
    """Build an evidence-only model payload; threshold is provisional.

    No model calls occur here. Sequence counts use distinct sequences with at
    least one selected event. Scores are independent, never blend percentages.
    """
    if min_sequences < 1:
        raise ValueError("min_sequences must be at least one.")
    features = build_style_features(data, player, start, end)
    scores = []
    if features["action_sequences"] >= min_sequences:
        result = score_style_profiles(features)
        scores = [
            {"reference": profile,
             "experimental_score": round(float(row["experimental_resemblance_score"]), 1)}
            for profile, row in result.iterrows()
        ]
    return {
        "player": player,
        "view": view,
        "window": {"start_exclusive": start, "end_inclusive": end},
        "action_sequences": int(features["action_sequences"]),
        "evidence": analyze_player(data, player, start, end),
        "experimental_reference_scores": scores,
        "audience": "casual fan",
        "language": "English",
        "instructions": [
            "Write a match insight in no more than 80 words.",
            "Use only the supplied measurements and scores.",
            "Describe references as invented legend-inspired profiles.",
            "Never describe scores as percentages of a legend.",
            "Explain the observed actions before mentioning resemblance.",
            "Do not claim a change over time without comparison evidence.",
            "Do not invent tactical causes or historical facts.",
            "Mention that this is a synthetic demonstration.",
            "If scores are absent, describe recorded actions only."
        ]
    }


def explain_profile_distance(features, profile):
    """Return each weighted feature's contribution to reference distance."""
    if profile not in reference_profiles.index:
        raise ValueError(f"Unknown reference: {profile}")
    observed = pd.Series(features).reindex(feature_names).astype(float)
    if not np.isfinite(observed.to_numpy()).all():
        raise ValueError("All feature values must be finite.")
    reference = reference_profiles.loc[profile, feature_names]
    contributions = ((observed - reference) / feature_scales).pow(2) * feature_weights
    return pd.DataFrame({
        "player_rate": observed,
        "reference_rate": reference,
        "difference": observed - reference,
        "weighted_squared_difference": contributions,
    }).loc[feature_weights.gt(0)].sort_values(
        "weighted_squared_difference", ascending=False
    )
