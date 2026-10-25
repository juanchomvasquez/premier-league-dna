# Premier League DNA

Every player has a blend. Every insight has evidence.

The default submission route connects our own synthetic football events to an
accelerated replay, position-specific statistics, a Microsoft AI interpretation,
a performance wheel and event-level evidence. It supports eight positions,
player/time-window selection, English/Spanish and fan/broadcast brief focus.

## Run

Requires Python 3.10 or later.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -s tests -q
```

Select a player, click Start replay and watch the clock release observed events.
Pause to inspect a fixed window. Choose Microsoft AI and explicitly generate an
interpretation. At full time the request becomes a performance recap. The same
observed evidence drives the charts and the cited numerical facts.

The replay advances three match minutes every two seconds by default. Its events
are fictional independent action scenarios, not a real PL feed or a complete
possession-consistent football match. Future rows are withheld from analysis.
The pitch marker is schematic. Invented legend-inspired profile overlays are
design previews, off by default, and never validated historical likeness scores.
Sourced career cards are separate context, not synthetic similarity inputs.

## Microsoft inference and cost

An Azure OpenAI deployment provisioned through Microsoft Foundry provides the
runtime interpretation. Configure existing private settings as described in
[Microsoft setup](docs/MICROSOFT_SETUP.md). Never commit keys to GitHub.

No model call on startup or ordinary controls while automatic updates are off.
Each Generate button click makes one potentially billable request. Optional
replay updates are off by default and limited to one automatic attempt every
thirty seconds per browser session when evidence changes. This is not a global
spending cap. API failure leaves the replay and local facts available.

The model writes prose and cites known measurements. The app checks structure,
citation membership and numeric-token rules, then renders exact facts locally.
These checks do not independently verify all semantic claims in the prose.
No paid Azure call was made while developing this revision; the deployed
interpretation/recap still needs an owner smoke test.

## Submission materials

- [Pitch and project description](docs/submission/PROJECT_PITCH.md)
- [Judge testing instructions](docs/submission/JUDGE_INSTRUCTIONS.md)
- [Architecture](docs/submission/ARCHITECTURE.md)
- [Data permission review](docs/submission/DATA_RIGHTS_REVIEW.md)
- [Final checklist](docs/submission/SUBMISSION_CHECKLIST.md)

The public repository is https://github.com/juanchomvasquez/premier-league-dna.
The demo is https://juanchomvasquez-premier-league-dna-app-1qylhs.streamlit.app/.
New local code is not deployed merely by preparing this package. The owner uploads
files manually and reboots Streamlit. No final hackathon submission or video was
created in this session.

## Research modules

The codebase preserves eight recorded 2026/27 player examples, a retired-only
legend roster, sourced career cards and identified historical reference data.
The roster includes Roy Keane, Vieira and Makélélé CDM samples from real 2003/04
matches, not season/career averages. Full cross-provider equivalence and style
similarity remain unvalidated. Missing references remain unavailable.

The current-season/live research view is disabled by default while data reuse
permissions remain unresolved. An owner with appropriate rights can expose it
with PL_DNA_ENABLE_RESEARCH=1. The flag itself does not grant permission. Public
visibility of a provider endpoint does not establish a licence to reuse its data
or send it into AI. This research connector is not represented as an authorized
production feed in the submission.

See [research sources and coverage](docs/CURRENT_SEASON_AND_LIVE.md). The earlier
archived midfield UI remains outside public navigation. Raw third-party event
files, credentials and caches are not included in the release package.
