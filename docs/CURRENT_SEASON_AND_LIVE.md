> Research documentation. This view is disabled in the default submission build while third-party data-use permissions remain unresolved. The primary submission route is the synthetic replay connected to Microsoft. See [data review](submission/DATA_RIGHTS_REVIEW.md). An owner flag is not permission to reuse data.

# Current-season performances and automatic match updates

The default **This season & live** view now uses real 2026/27 match snapshots.
The old Vieira study remains in the source tree but is removed from public navigation. The synthetic
eight-position demonstration remains separate and explicitly labelled.
Fan/Broadcaster/Expert buttons have been removed; evidence sits under expanders.

## Included recorded performances

| Position | Player | Club | Match date |
|---|---|---|---|
| GK | Zion Suzuki | Aston Villa | 24 Oct 2026 |
| CB | Virgil van Dijk | Liverpool | 17 Oct 2026 |
| FB | Antonee Robinson | Fulham | 24 Oct 2026 |
| CDM | Moisés Caicedo | Chelsea | 24 Oct 2026 |
| CM | Enzo Fernández | Manchester City | 24 Oct 2026 |
| CAM | Bruno Fernandes | Manchester United | 18 Oct 2026 |
| Wing | Diego Gómez | Brighton | 18 Oct 2026 |
| ST | Igor Thiago | Brentford | 17 Oct 2026 |

Eight positions, eight clubs, with source-reported minutes (90 in each selected
snapshot). Names and clubs come from each fixture roster, not assumptions about
an older squad. The fixed convenience sample spans wins, a draw and losses.
It was selected before calculating fits, not to flatter every player. A team
loss does not establish a poor individual performance. These examples are not
claimed to be the season's best performances or a representative league sample.

Fixture dates, home/away identities and scores were cross-checked against the
Premier League's own 2026/27 results feed. Player minutes and counts come from
ESPN's public match-stat responses. Links and retrieval timestamps are in the UI
and downloadable evidence. Source URLs and SHA-256 fingerprints are bundled.

Completed-match totals are never interpolated into fabricated minute-by-minute
events. The recorded view has no match-minute slider and is not presented as live.

## Historical references

| Group | Available reference coverage |
|---|---|
| GK | Petr Cech 2013/14; Edwin van der Sar 2008/09 |
| CB | John Terry 2014/15; Nemanja Vidic 2010/11; Rio Ferdinand 2012/13 |
| FB | Ashley Cole 2009/10; Gary Neville 2008/09; Leighton Baines 2012/13 |
| CDM | Roy Keane 2003/04 · 2 recorded PL matches; Patrick Vieira 2003/04 · 3 recorded PL matches; Claude Makelele 2003/04 · 2 recorded PL matches |
| CM | Frank Lampard 2009/10; Steven Gerrard 2008/09; Paul Scholes 2010/11 |
| CAM | Cesc Fàbregas 2014/15; Mesut Özil 2015/16 |
| WING | Eden Hazard 2018/19; Ryan Giggs 2008/09; Gareth Bale 2012/13 |
| ST | Didier Drogba 2009/10; Wayne Rooney 2011/12 |

The public pool is retired-only. Van der Sar, Rio Ferdinand, Gary Neville,
Baines, Vieira, **Roy Keane**, Bergkamp, Giggs and Bale replace the active
references. Carrick is not in the approved pool. Van Dijk remains a current
example, never a historical reference. All 25 career cards retain sourced PL
headlines and club colours weighted by PL appearances. Roy Keane's 366 PL
appearances comprise Manchester United 326 and Nottingham Forest 40.

There are **18 full-season references plus three CDM match-sample references**.
Four selected-season references remain unavailable: Bergkamp, Schmeichel and
Shearer predate consistent detailed coverage; Henry's endpoint returned 404.
Missing values are never filled with zero. Later-career selections such as
Ferdinand 2012/13 and Neville/Giggs 2008/09 are identified references, not claims
about every player's prime season or unchanged career-long role.

### CDM: actual recorded match samples

StatsBomb Open Data supplies event-level observations from selected 2003/04
Premier League matches. Keane: two matches, 180 regulation minutes. Vieira:
three matches, 270 minutes. Makélélé: two matches, 180 minutes. Fixtures and
source hashes are retained per player; each selected game involves Arsenal.
This is a small convenience sample with different opponents/sample sizes, not
season or career averages. No invented reference rates are used.

Passes count all Pass events; tackles count Tackle-type Duel events;
interceptions count Interception events; recoveries count Ball Recovery events
without recovery_failure. Long passes are omitted because no sufficiently
verified equivalence was established. Current ESPN summary definitions and
these historical StatsBomb definitions are **not independently harmonized**.
The UI labels the source/sampling limitations; the fit remains exploratory.

Minutes come from the union of source lineup position intervals on a regulation
clock, capped at ninety per game; event counts include first/second-half added
time. This is a standard regulation-minute exposure convention, not a claim
that no added time was played. Small samples can yield volatile rates. No
opponent/era adjustment or validated career resemblance is claimed.

Tools/build_cdm_samples.py derives these counts from a pinned publisher snapshot.
Tools/audit_cdm_samples.py independently recounts events with SQLite and checks
lineup exposure and source SHA-256 hashes. Raw events are not included in the
upload package. StatsBomb attribution, source links and its logo appear in the
CDM source expander. Missing reference coverage remains a distinct fallback,
keeping usable recorded facts/wheel/AI available rather than inventing a blend.

Tools/build_retired_roster.py creates the nine new career cards. Its separate
audit checks source digests, player identity and numerical headlines. Club sums
reconcile; the linked records establish club attribution. Career and headline
season facts do not enter the fit.

## The comparison

Per-90 rates use source-reported player minutes. Each axis is divided by the
highest rate among its available reference periods, then a nonnegative least-squares
mixture is fitted with weights summing to one. Each included, scaled axis has
equal weight. Percentages use largest-remainder rounding. The wheel is not a
percentile, ability rating, probability or validated career-similarity score.
One match is a noisy sample and tactical roles, opponents, game state and eras
are not adjusted for. Cross-provider equivalence of every field definition has
not been independently established; this remains an exploratory estimate.

The code requires at least 30 source-reported minutes and three shared metrics
to display a blend. A missing historical blend does not suppress a usable recorded-only performance or its optional analyst brief. These are display rules, not statistical reliability thresholds.
Missing values remain unavailable and are never filled with zero. The exact
ESPN-to-PL field mapping is in `pl_dna/season_feed.py`.

**No clear legend match:** if scaled RMSE exceeds 0.5 or the largest scaled
axis difference exceeds 1.0, public blend percentages and the purple composite
polygon are hidden. The teal player wheel and factual narrative remain visible.
These are provisional display checks, not calibrated statistical confidence or
a validated similarity test. Passing them does not establish true resemblance.
The downloaded evidence retains candidate weights for numerical inspection.

**Style and execution are separate.** A poor fit is not a poor-performance grade;
a familiar style can coexist with poor execution, and an effective performance
can have no clear match. Passing, tackle and duel outcomes are shown only when
both numerator and denominator are reported and consistent. No overall grade,
unsupported tactical explanation or fabricated comparison is generated.
Insufficient minutes/data has its own state, separate from an adequate-data mismatch.

**Source discrepancy:** some detailed shot-location breakdowns disagree with
player shot totals. Shot totals reconcile with team boxscores; the disagreement
is retained as a warning. Shots are excluded from all current role wheels.
Box touches are used where available; these are not box arrivals. Explicit
field mappings and omitted axes appear in the evidence export. Goalkeeper
conceded-goal counts describe recorded activity, not individual fault.

## Automatic live view

Select **This season & live → Follow a live match → Connect to the match feed**.

- The app initially requests today's Premier League fixtures using the London date. A date selector also browses other matchdays from 2026/27, including completed matches beyond the eight bundled examples.
- It polls fixture/player snapshots every 60 seconds while the view/session is active.
- Source data and calculated comparisons update automatically for the selected player.
- Snapshots replace earlier snapshots; repeated polls are not added as new events.
- Pre-match fixtures wait for kickoff and player statistics; no performance is inferred.
- All eight reference groups are available. Source labels suggest a group; it can be changed manually. Unknown labels require a manual selection.
- Empty schedules and missing statistics have explicit states.
- Failed or stale player data is labelled as a retained snapshot, with new AI stories paused.
- At full time the completed performance remains visible and automatic AI requests stop.
- Changing fixtures, players or reference groups hides AI stories that no longer match.

These are **public, undocumented website endpoints**, not an official API contract
or a provider partnership. Provider delays and endpoint changes are possible.
The UI distinguishes **last checked** from an unknown source publication time.
It does not promise instantaneous event-level coverage or every pass's coordinates.
Server-side caches limit identical reads to approximately once per minute.
There are no access-control workarounds, alternate-host retries, paid data credentials
or API subscriptions in this implementation.

The public fixture and player endpoints were exercised against completed 2026/27
matches. The 25 Oct fixture list and pre-match detail also returned successfully.
All five fixtures were pre-match at verification time. **A real in-progress match
still needs end-to-end verification on the deployed Streamlit app.** Tests simulate
successive live updates, failures and full time; those test responses are not
presented as product match data.

## Microsoft AI and cost controls

Calculated comparisons and the collapsed **Calculated snapshot** require no AI
call. The snapshot is a compact list of recorded counts, not a match narrative.
**Generate Microsoft interpretation** makes one potentially billable request,
with no automatic retry. Microsoft now authors a headline and a brief synthesis
of the pattern across different measurements, rather than selecting fixed
sentences for the same local template.

The structured response contains headline, narrative and two or three distinct
known evidence IDs. Numerical tokens are rejected from the prose; the app
attaches the exact cited fact sentences locally. Format, length, distinct
measurements and citation membership are checked. Certain unsupported overall
assessments and named legend claims during a no-clear-match state are rejected.
These checks do **not** verify every semantic claim in AI prose. The output is
labelled AI interpretation, with cited facts checked but interpretation not
independently verified. The prompt prohibits invented tactics, intent, causation,
errors, dominance or ability grades. Weak fits must not be forced into legend
resemblance. Changing the player or data hides the prior brief.

The previous duplicate local/AI story cards are removed. One AI interpretation
appears after generation, with supporting facts and copy text under an expander.
No generated interpretation appears in the static preview. Developer tests use
simulated AI responses; no paid Azure test was made for this revision.

**Update Microsoft interpretation automatically during live play** is off by default.
If explicitly enabled in the app, it makes at most one automatic request every
five minutes in that browser session, only when the comparison changes, the
source is not stale, and the fixture is in progress. Attempts are recorded before
the request, including failures. Manual clicks remain explicit individual requests.
Existing private Azure settings are reused; no secrets are in the download.
No paid Azure requests were used during development/testing of this update.

## Reproduce and verify

```bash
python tools/build_current_season.py --cache-dir ../source-audit-cache
python tools/audit_current_season.py ../source-audit-cache
python tools/audit_retired_roster.py ../source-audit-cache
python tools/audit_cdm_samples.py ../cdm-source-cache
python -m unittest discover -s tests -q
```

The cache retains decoded provider responses for audit. Their original response
byte hashes and canonical JSON hashes are stored separately. Raw provider
responses are not redistributed in the update; the bundle contains selected
derived facts and provenance. A new empty cache causes a fresh source read.

The independent SQLite audit checks all 18 full-season references and eight selected
performances, including source identity, minute denominators, count fields, execution facts,
cache fingerprints, fixture-score corroboration and team/player shot reconciliation.
It does not establish full provider-definition equivalence or validate a style model.

Sources: [Premier League statistics coverage](https://www.premierleague.com/en/stats/clarification),
[Premier League fixtures](https://www.premierleague.com/en/matches/premier-league/2026-27),
and the individual ESPN match/player-stat links carried in the evidence JSON.
