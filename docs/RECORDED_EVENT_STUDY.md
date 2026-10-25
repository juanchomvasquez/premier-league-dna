# Recorded-event comparison: what is actually supported

23 October 2026 · research preview · no live deployment performed.

The default example is Thierry Henry's Arsenal 4–2 Liverpool performance on
9 April 2004 against his OTHER 36 Premier League appearances in 2003/04.
The selected match is excluded from its reference. A separate Jamie Vardy match
(Newcastle 0–3 Leicester, 21 November 2015) is a cross-player pipeline test;
Vardy is not added to the legend roster.

## Reproducible source

- Publisher: [StatsBomb Open Data](https://github.com/hudl/open-data).
- Pinned source commit: `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.
- 38 Arsenal 2003/04 fixtures, including 37 Henry appearances; one Leicester fixture.
- Source-file SHA-256 hashes: `pl_dna/data/recorded_study.json`.
- Original event files are downloaded only to a local cache, not bundled or redistributed.
- Analysis uses an identical event function on both sides. Published results are
  derived counts and rates with StatsBomb attribution and its supplied logo.
- The publisher's user agreement restricts raw-data redistribution and commercial
  exploitation. This is an analysis/research preview, not a declaration that all
  competition or future commercial uses are cleared.

```
python tools/build_recorded_study.py --cache-dir /tmp/pl-dna-events --download
python tools/audit_recorded_study.py /tmp/pl-dna-events
python -m unittest discover -s tests -q
```

## What passed

- Henry's goal-event total is 30, matching the PL's 2003/04 season review.
- Henry appears in 37 fixtures, matching the published season appearance total.
- Goal events match all 39 fixture scorelines in the publisher's match metadata;
  own goals count once for the opposition.
- Henry's three-goal Liverpool performance and Vardy's one-goal Newcastle
  performance match separately published club/league match accounts.
- Event IDs are unique within each input; shot-assist links resolve to real shots.
- A separate SQLite JSON query reproduces all five Henry-season and Vardy-match
  counts and denominators independently of the Python counting function.
- The selected Henry match is excluded from its own reference.
- 82 tests passed, including source-snapshot, denominator, data isolation, club-share
  and rendered-app checks. No Azure model calls or network requests occur on app use.

## Exact comparison units

Five frequencies per 100 recorded **passes + shots + dribbles**. This is a custom,
explicit on-ball action denominator, not possession sequences, touches or minutes.
All events use regulation periods 1 and 2, including added time. Rates pool total
counts and exposure; they do not average match percentages.

| Axis | Counting rule |
| --- | --- |
| Non-penalty shots | Shot event not tagged Penalty; free-kick shots included |
| Completed take-ons | Dribble outcome Complete; not carries |
| Shot-assisting passes | Pass linked by assisted_shot_id to an actual shot; goal assists included |
| Completed passes into box | Completed pass from outside to inside x≥102, 18≤y≤62 on a 120×80 pitch |
| Completed forward passes | Completed pass advances at least 10 x-units toward the opposing goal |

Missing pass outcome denotes completion in StatsBomb. A pass into the box must
cross its boundary; passes starting inside are excluded. Axes can overlap and
therefore need not sum to 100. These definitions do NOT silently replace or map
to the synthetic dashboard's 25%-distance-reduction progressions.

| Sample | Actions | Non-penalty shots | Completed take-ons | Shot-assisting passes | Passes into box | Forward passes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Henry, all 37 appearances | 1720 | 187 | 148 | 76 | 77 | 165 |
| Henry vs Liverpool | 40 | 9 | 3 | 1 | 0 | 2 |
| Henry, other 36 appearances | 1680 | 178 | 145 | 75 | 77 | 163 |
| Vardy vs Newcastle | 24 | 6 | 2 | 0 | 1 | 0 |

## What has NOT been validated

Matching goals/appearances does not validate every dribble or pass annotation.
No independent second-provider recount of all advanced events has been completed.
The SQL audit checks calculations against the same input, not independent reality.
There is no trained, externally validated style-matching score, calibrated percentage,
or claim of equal ability. Different roles, teammates and eras remain confounders.

One additional numerator event at the current denominator shifts Henry's selected
match rate by 2.50 points per 100 actions, and Vardy's by 4.17. That sensitivity is
not a confidence interval. One match cannot establish a stable long-term profile.

**This is a Henry 2003/04 reference, NOT a Henry career average.** The dataset does
not cover his full PL career. A real career rate would pool same-definition events
and exposure across all verified covered seasons. No season or career headline
(goals, assists, appearances) is used to invent advanced event averages.

## Career card and colour prototype

Seven sourced retired-player career records are available as an optional card:
Lampard, Cech, Henry, Gerrard, Scholes, Drogba and Fabregas. The 25 selected-season
cards remain available. Remaining career records are not silently filled in.

Colour strip widths are shares of Premier League appearances, not minutes or
all-competition games. All verified PL clubs are listed, and multiple spells at
one club are combined. The chosen-season club remains separately named.

- Lampard: Chelsea 429/609 (70.4%), West Ham 148/609 (24.3%), Man City 32/609 (5.3%).
- Cech: Chelsea 333/443 (75.2%), Arsenal 110/443 (24.8%).
- Fabregas: Arsenal 212/350 (60.6%), Chelsea 138/350 (39.4%). His selected 2014/15
  season remains Chelsea, with that distinction explicit.
- Career assists use the official PL figures. Drogba's PL total 55 differs from
  StatMuse's 54; Fabregas's club assist totals also vary by provider. Club colour
  weights use appearances only and do not blend assist definitions.

Each card links its sources in `pl_dna/career.py`. These verified career headlines
are achievements, not the advanced-event reference. Displaying more impressive
career totals does not make the wheel a career comparison.

## Review/install

Open `recorded-event-review.html` for a self-contained preview, with no account,
Azure connection or installation. The live app is unchanged until upload.

Optional app update ZIP: drag its extracted `app.py` and `pl_dna` folder into the
existing GitHub repository root; merge/replace matching files, never delete the
folder. Then commit. Reboot Streamlit if imports remain cached.

In the app, choose **Show PL career achievements & club colours** on a supported
legend card. The separate bottom expander **Recorded-match evidence study · real
events** contains the opt-in real-event comparison. It does not alter synthetic
inputs, narrative evidence, legend selection or the Microsoft integration.
