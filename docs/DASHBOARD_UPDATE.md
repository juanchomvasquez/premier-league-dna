# Audience dashboard update

## Included

- Fan, Broadcaster and Expert views share the same event measurements.
- Fan: immediate local story, profile cards and contribution chart.
- Broadcaster: talking point, supporting facts with event IDs, copyable text.
- Expert: counts, rates per 100 recorded sequences, model distances, definitions.
- Responsive navy theme, teal contributions, purple model-score cards.
- Player header and schematic position marker; no tracking claim.
- Cech, Van Dijk, Kyle Walker and Makelele reference changes; Henry and Rooney
  both remain alongside Shearer and Drogba in the four-profile striker group.

Reference rates are invented. New references change relevant model scores;
generated match events and measurement rules are unchanged. The current Henry
profile does not measure carrying or finishing efficiency.

## Update the existing hosted app

1. Extract the dashboard ZIP into a new folder.
2. Open the existing GitHub repository, then Add file > Upload files.
3. Upload the contents, not the enclosing folder. Include `.streamlit`;
   on a Mac press Command + Shift + . in Finder to reveal hidden folders.
4. Keep `app.py` and `requirements.txt` at the repository root, with `pl_dna`
   alongside them. Do not upload any `.env`, secrets.toml, or virtual environment.
5. Commit to the branch used by Streamlit. Wait for the hosted app to update.
6. If the theme does not update, use Streamlit's Manage app > Reboot app.

No Azure credentials or billing changes are needed for local mode.
The live Microsoft connector still requires a supported deployment and quota.

## Review after deployment

- Fan: Alex Morganfield, minute 90, story and three profile cards.
- Broadcaster: same counts, supporting facts and copyable talking point.
- Expert: rates, model distances and event definitions.
- Striker: four references including Henry and Rooney.
- Goalkeeper: Schmeichel, Cech and Alisson.
- Minute 1: insufficient-sample message, no model score bars.
- Change minute or audience after generating: an old model result is not reused.
- On a phone: profile cards stack vertically and controls remain usable.

## Still outside this update

Live Azure verification, real historical data, extra fictional players and a
side-by-side player comparison are not implemented by this presentation update.
