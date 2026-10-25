# Premier League DNA

Every player has a blend. Explore recorded Premier League performances, inspect exploratory historical-reference comparisons, and follow automatically refreshed match statistics.

## Run the prototype

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The default **This season & live** dashboard includes eight recorded 2026/27
performances: one per position group, from eight clubs. Choose a recorded example
or connect to a match feed. Live statistics refresh every 60 seconds while the
view is active; matchdays can also be browsed by UK date.

One dashboard replaces the Fan/Broadcaster/Expert controls. A weak comparison
shows **No clear legend match**, hides mixture percentages and the composite
reference polygon, and keeps the player's wheel and evidence-based story.
Execution facts are separate from playing style; no overall grade is inferred.
Insufficient minutes or shared fields has a separate unavailable state.

[Current-season data, live behavior, sources and limits](docs/CURRENT_SEASON_AND_LIVE.md)
documents the 20 usable historical season references and five unavailable ones.
All 25 career cards remain accessible with club colours weighted by PL appearances.
The fitted mix is exploratory; neither provider equivalence nor style similarity
has been independently validated.

The separate **Eight-position synthetic demo** retains the fictional scenarios,
minute slider, local English/Spanish summaries and explicitly invented overlay.
**Archived midfield research** preserves the earlier historical event study.
Recorded match totals are never turned into invented minute-by-minute replays.

The responsive navy, teal and purple theme is in `.streamlit/config.toml`.
Include that folder when uploading or deploying the app.

```bash
python -m unittest discover -s tests -v
```

Local calculations require no Azure credentials. The optional Microsoft connector
selects evidence IDs, validates them, and renders controlled wording. A manual
click makes one potentially billable request. Automatic Microsoft stories are
off by default and, if enabled during live play, limited to one attempt per five
minutes per browser session when fresh statistics change. No paid Azure calls
were used in development tests. Real in-progress feed behavior still needs an
end-to-end check on the deployed app; completed and pre-match feeds were exercised.
See [Microsoft setup](docs/MICROSOFT_SETUP.md).

## Project vision and development scope

Premier League DNA aims to explain playing-style blends across a team,
using position-specific measurements and references drawn from
Premier League history.

Development begins with central midfielders to establish the analysis
and explainability workflow. The submission target is a broader,
position-aware experience, with additional role groups introduced
as their measurements and reference models are implemented and tested.

Currently implemented: a local experimental explorer for goalkeepers,
centre-backs, full-backs, defensive midfielders (CDM), central midfielders (CM),
attacking midfielders (CAM), wingers and strikers.
Each role has five applicable measurements, three invented archetypes (four for strikers) and a
fictional demonstration player. The new role scenarios are separate from the
original notebook dataset; the same player name does not imply the same data.
Goalkeepers use their own measurements and invented reference profiles.

## Synthetic-demo interpretation

The dataset is synthetic and the players are fictional. Legend-inspired reference profiles are invented design hypotheses. Scores are independent model outputs, not probabilities, validated historical comparisons or player-quality rankings. Activity dimensions overlap. The ten-sequence display threshold is provisional.

The original exploration is in `notebooks/01_midfield_style_prototype.ipynb` and
its reusable calculations are preserved in `pl_dna/engine.py`. The expanded role
scenarios and calculations are in `pl_dna/roles.py`; the interface is in `app.py`.
These are independent action scenarios, not a possession-consistent simulation
of a complete match. See [build checkpoints](docs/BUILD_PLAN.md) and
[acceptance criteria](docs/ACCEPTANCE.md) for remaining scope and limitations.

## Player DNA visual preview

The dashboard includes a selectable radar wheel and club-coloured legend season card.
Sourced full-season facts are loaded for all 25 legends across eight positions. They are displayed separately from the synthetic performance wheel; the current-season mode separately uses sourced season-rate references. Neither mode supplies validated similarity scores. The invented
overlay is an explicit design-preview option, off by default.
See [historical sources, selection criteria and upload instructions](docs/HISTORICAL_SEASONS.md).


## Recorded-event research study

A separate optional study compares Henry’s Liverpool match with his other 2003/04
appearances using same-provider, same-definition event rates. It includes source
reconciliation and a second SQL recount, without claiming a validated style score
or career event coverage. All 25 optional career headline cards include club colours
weighted by PL appearances. See [evidence and limitations](docs/RECORDED_EVENT_STUDY.md).
