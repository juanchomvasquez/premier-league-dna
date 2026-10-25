# Judge testing instructions

## Access
Open https://juanchomvasquez-premier-league-dna-app-1qylhs.streamlit.app/ in a desktop or mobile browser. No judge login, local installation, API key or payment is required. Azure credentials, if enabled by the project owner, are held server-side.

These instructions describe the new upload package. The owner must deploy it before submitting these instructions.

## Quick route
1. The default view is Eight-position synthetic demo. All player performance events in this route are fictional and labelled synthetic.
2. Keep Central midfield / Alex Morganfield, or select another of the eight position groups. Start at minute forty-three for enough evidence, or reset to watch events arrive from the beginning.
3. Click Start replay. The default acceleration advances three simulated match minutes every two seconds. The clock, observed rows, measurements and wheel update while the view is open. Pause replay to inspect a fixed window. This is a controlled replay, not a real PL match feed.
4. Under Player overview, choose Microsoft AI as the insight source. Keep automatic updates unchecked for a single controlled request. Click Generate Microsoft interpretation.
5. Read the AI brief. Open Supporting facts & copy brief and inspect the exact cited measurements. The AI interpretation is not independently verified; its cited facts and format are checked.
6. Change the language to Spanish or the Brief focus to Broadcast talking point, then explicitly generate again to test personalization. A control change alone does not make an AI request with automatic updates off.
7. Move the clock to full time or let replay finish, then click Generate Microsoft recap. The request now asks for a concluding synthetic recap.
8. Open Evidence explorer or Download synthetic AI evidence to inspect the event identifiers and selected windows behind the result. Future events are not passed to the model.

## Automatic AI option
Refresh Microsoft brief during replay is off by default. If enabled, it allows at most one automatic attempt every thirty seconds per browser session when the context changes, including a final recap after the throttle permits it. Each attempt may incur an Azure charge to the owner; failure does not cause an automatic retry for the same evidence context. Keep it off for the lowest-call test route above.

## Expected limitations/fallbacks
- Fewer than ten recorded action sequences: a brief is withheld, while replay and calculated facts remain available.
- Azure not configured, unavailable or rejecting output: a labelled message appears. This is not represented as a successful AI interpretation.
- A changed player, language or manually selected window hides an older AI brief. During running replay, the last brief can remain visible with its explicit as-of minute and evidence window; it is not presented as a newly generated current-minute brief. Generate for a new fixed context.
- Legend-inspired numeric overlays are invented design previews, off by default. They are not validated historical similarity or player ability ratings.
- The synthetic scenarios are independent player action sequences, not a full possession-consistent match simulation. Pitch locations are schematic, not measured tracking.
- The research connector is not part of the default judge route. It is not an authorized production data-service integration.

## Local reproduction
Requires Python 3.10 or later and the dependencies in requirements.txt.

    python -m pip install -r requirements.txt
    python -m streamlit run app.py
    python -m unittest discover -s tests -q

Without Azure settings, replay and local calculations work; Microsoft generation is unavailable. Private configuration details are in docs/MICROSOFT_SETUP.md. Do not place credentials in GitHub or testing instructions.

Microsoft briefs can explain the closest illustrative legend-inspired profile or two close profiles. Their independent scores are calculated locally and shown with the brief, with calculation details available. These are invented design references, not validated historical player likeness or percentage blends.
