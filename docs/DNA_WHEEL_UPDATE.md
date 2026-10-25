# Player DNA wheel — visual preview

This update adds a live radar wheel for all eight position groups, a reference selector,
and a club-coloured legend index preview card. The selected synthetic performance is
teal and solid; the invented reference is purple and dashed. Exact values are available
in an expandable table. The chart is served as an SVG image, avoiding inline-SVG
sanitization. It needs no new app dependencies and makes no model calls.

All axes use actual metric counts per 100 recorded action sequences. The role's baseline
scale covers all its invented reference values, rounded up to the next 20; it expands
if an observed rate exceeds it. No rates are clipped. Check ring labels across windows.
These are not percentiles or game-style ability ratings. Below ten sequences the selected
shape is hidden; this threshold remains provisional. Existing experimental scores are
retained under the Expert view's illustrative profiles; they are not historical indexes.

## Historical reference decision

Use one documented standout Premier League season per legend, with a stated selection
criterion and compatible metrics. Do not combine individual career-high statistics from
different seasons. A weighted PL career average can be an additional mode later.

Historical seasons and sources have NOT been selected or connected in this update.
Every index card explicitly identifies the current invented demonstration reference.
Do not label these numbers as historical data or validated legend similarity. Sourced
benchmarks require a data coverage/usage review and aligned measurement definitions
and denominators; current per-100-sequence fixtures cannot be replaced directly by per-90
historical rates. Hackathon demonstration inputs remain synthetic.

## Update the existing GitHub app

1. Download and unzip `premier-league-dna-wheel-update.zip`.
2. In the existing repository, choose **Add file → Upload files**.
3. Drag the unzipped **app.py** and **pl_dna folder** together into the upload area.
   Keep their paths: `app.py`, `pl_dna/presentation.py`, `pl_dna/dna_wheel.py`.
   Do not upload the ZIP itself or an extra outer folder. Do not delete existing files
   or the rest of the existing `pl_dna` folder. These three files update/add just those paths.
4. Commit the files, allow Streamlit to redeploy, and refresh the app.
5. Open **Fan → Player DNA**, switch Lampard to Gerrard or Scholes, then change the minute.
   The wheel should update. Other positions have their own reference choices.

For local use, replace/add those same three files within the existing project and run
`python -m streamlit run app.py` from the project folder. Existing requirements are unchanged.

## Boundaries

This package does not deploy to Streamlit or configure Azure. The Microsoft provider
remains explicitly triggered by the Generate insight button. A quota-tier eligibility
email does not establish model availability or a completed tier upgrade.
