# Recorded midfield blend — research pilot

This update replaces the Microsoft window-change commentary with a recorded-match
legend-sample comparison. It does **not** establish validated career resemblance.
The Fan / Broadcaster / Expert buttons have been removed. The story is prominent,
copyable text and detailed evidence sit under expanders.

This older study is available under **Archived midfield research**. The default
view is now **This season & live**, documented in CURRENT_SEASON_AND_LIVE.md. The original
eight-position synthetic demo remains available through the Data source control.

## What Azure does

The application calculates all counts, rates and mixture weights first. On an
explicit button click, Azure selects a lead comparison and optional supporting
comparison for the match story in one unified dashboard. Strict JSON schema limits
the output to known evidence IDs and an editorial angle. The application validates
the IDs and renders the story with calculated numbers and controlled wording.
Azure cannot invent a percentage, modify a count or supply unchecked prose.

One potentially billable request is made per **Generate legend story with
Microsoft AI** click. Control changes, viewing cards and calculating the blend do
not call Azure. Earlier stories are hidden after player or minute changes.
Failure produces a safe diagnostic and retains the locally calculated comparison;
there are no automatic retries. Existing private Azure settings remain applicable.
Local tests used simulated responses, not paid Azure inference. The first live
request after upload still needs checking with the user's configured deployment.

## Actual coverage

Source: [StatsBomb Open Data](https://github.com/hudl/open-data), pinned commit
`4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.

| Reference | Recorded PL fixtures | On-ball denominator |
|---|---|---:|
| Frank Lampard | Arsenal–Chelsea, 18 Oct 2003; Chelsea–Arsenal, 21 Feb 2004 | 111 |
| Steven Gerrard | Liverpool–Arsenal, 4 Oct 2003; Arsenal–Liverpool, 9 Apr 2004 | 131 |
| Paul Scholes | Arsenal–Manchester United, 28 Mar 2004 | 56 |

Scholes did not play in the other Manchester United fixture in this archive.
Therefore his reference has **one** appearance, not two. These are selected match
samples against a single opponent. They are **not** career, best-season or full-season
averages, and a zero in these small samples is not evidence of a career weakness.

Selected performances are Patrick Vieira and Gilberto Silva at Newcastle on
11 Apr 2004, plus Gilberto against Newcastle on 26 Sep 2003 and at Leeds on
1 Nov 2003. None of those fixtures contributes to any reference profile. Players
and fixtures are fixed in the build script; there is no search for a flattering fit.
Selection is archival and narrow, not a representative sample of PL midfield styles.

## Five compatible axes

All use the same provider fields and counting function on both sides:

- Non-penalty shots.
- Completed take-ons (Dribble outcome Complete, not carries).
- Passes explicitly linked to a teammate shot already observed.
- Completed passes from outside into the penalty area, including set plays.
- Completed passes at least 10 StatsBomb x-units forward, including set plays.

Denominator: all Pass + Shot + Dribble events in periods 1–2. Rates are pooled
counts divided by pooled on-ball actions, times 100. They are not per 90 minutes,
touches, all events, or the synthetic demo's independent action sequences.
Measurements can overlap. The forward-pass definition is a custom field rule,
not a provider-standard progressive-pass statistic. Box entries are not box arrivals.

At minute 45 all first-half added time is included; at 90 all second-half added
time is included. Other selections use events before that minute boundary.
Future teammate shots cannot establish an earlier shot-assisting pass. Fixture
labels give the archived full-time result, not an in-progress score.

## How the blend is calculated

Solve the constrained least-squares problem over five action-rate coordinates:

`minimize sum((reference_matrix @ weights - selected_rates)^2)`

subject to each weight being nonnegative and the three weights summing to one.
All rate-point errors have equal weight. The solver examines all active faces of
the three-reference simplex; no hand-set resemblance values or softmax are used.
Integer percentages use largest-remainder rounding and total 100.

The purple polygon is the weighted reference mixture, not a career polygon.
The teal polygon is the selected observed performance. The residual is RMS error
in rate points per 100 actions. A 100% weight is a boundary solution, **not** a
perfect match; a fitted mixture can still describe the target poorly. No threshold
has been validated for what constitutes an acceptable fit.

The interface reports the maximum weight change under a one-count annotation
change on any axis, with the denominator held fixed. This is sensitivity, not a
confidence interval or a sampling-error estimate. Thirty actions is only a display
floor; it is not a statistical reliability guarantee.

For example, the bundled Vieira performance at 90 minutes gives **66% Lampard /
0% Gerrard / 34% Scholes** under this specific formula and reference set. It has
66 on-ball actions and an RMS residual of approximately 2.65 rate points. Changing
one metric count can move a weight by up to about 11.0 percentage points at that
denominator. This example is a reproducible descriptive fit, not an assessment of
Vieira's identity, ability or career similarity.

## Validation and reproduction

Run from the repository root:

```bash
python tools/build_midfield_study.py --cache-dir /tmp/pl-dna-cm
python tools/audit_midfield_study.py /tmp/pl-dna-cm
python -m unittest discover -s tests -q
```

The build retrieves the publisher's pinned event files only when missing from the
chosen cache directory. The bundled JSON contains derived counts, minute snapshots,
source links and SHA-256 digests; raw event files are not redistributed.

The separate SQLite recount agrees on all five counts and denominators for all
seven reference/target profiles. Tests cover known mixtures, boundary fits,
degenerate references, rate reconciliation, target/reference separation, future-shot
leakage, response rejection, provider mutation, explicit-call boundaries and stale
story hiding. Full local suite: **102 tests passed**. This checks arithmetic and
implementation consistency, not independent accuracy of source annotations or
validity of a historical style-matching model.

## What is still needed

A release claiming career or representative season resemblance requires broader,
representative compatible event coverage for each legend and evaluation on held-out
matches. A recent match also requires an event feed with compatible fields and
definitions. This pilot does not fill those gaps with estimated career event counts.
All 25 existing career cards remain separate context, and their facts never enter
the mixture calculation. Current Azure storytelling is English only.

Data attribution and the StatsBomb logo are displayed. Reuse remains subject to
the publisher's [terms](https://github.com/hudl/open-data).
