# Premier League DNA

## Tagline
Every player has a blend. Every insight has evidence.

## Short pitch
Premier League DNA turns synthetic football events into player-focused, explainable match stories. An accelerated replay releases events over time, calculates position-specific contributions and feeds the observed evidence to a Microsoft AI deployment through Azure OpenAI in Microsoft Foundry. Fans can follow a player, inspect a performance wheel, change the time window, and request an English or Spanish interpretation or a concise broadcast talking point. Each AI brief cites known measurements; the app attaches their exact calculated facts and event evidence. At full time, the same pipeline supports a performance recap. The demonstration is explicitly synthetic, and legend-inspired design profiles are not presented as validated historical similarity.

## Project description
Football coverage often gives viewers a scoreline and isolated statistics without a clear explanation of an individual player's contribution. Premier League DNA connects the observations, their interpretation and the evidence behind the story in one interactive dashboard.

The submission demonstration uses our own deterministic fictional action scenarios across eight position groups: goalkeeper, centre-back, full-back, defensive midfield, central midfield, attacking midfield, wing and striker. A controlled accelerated replay releases rows according to simulated match minute. Measurements include only events already observed, with linked supporting actions checked against the current replay boundary. Viewers can pause, inspect the match so far or the last fifteen minutes, and explore event-level evidence.

Microsoft AI receives the selected player's observed facts and, when enough evidence exists, adjacent equal-duration window comparisons. It also receives separately labelled invented role-profile comparisons, allowing it to explain an illustrative legend-inspired resemblance without claiming measured historical similarity. It writes a short interpretation or full-time recap and returns references to known measurements. The application checks response structure and citation membership, rejects numerical tokens in the prose, and renders exact supporting numbers locally. These checks do not independently verify every semantic claim in the AI interpretation.

Personalization is functional: selecting a different player or position changes the analysis; time windows change the evidence; language and brief focus change the generation request. A casual fan can ask for an accessible explanation, while a presenter can request a concise on-air talking point. Detailed counts and event identifiers remain available for inspection.

The runtime uses Python, pandas, NumPy and Streamlit, with an Azure OpenAI deployment provisioned through Microsoft Foundry and accessed through the Responses API. Secrets remain server-side. AI requests are explicit; optional replay updates are off by default and throttled. Missing configuration or rejected output leaves the replay and calculated facts available.

The codebase also preserves historical/current-season research modules. They are outside the default submission path while third-party data reuse permissions are unresolved. The submission does not claim an authorized production Premier League live feed, validated historical likeness, video analysis, or a multi-agent system.

## Technologies actually used
- Microsoft Foundry / Azure OpenAI deployment: model inference for the analyst brief.
- Azure OpenAI Responses API: structured headline, narrative and evidence-ID output.
- Python, pandas and NumPy: event measurement and deterministic calculations.
- Streamlit: timed replay, controls, charts and evidence export.
- GitHub: public source repository.
- ChatGPT/Codex: development assistance, not the application's runtime model provider.

## Recommended category
Best Use of Microsoft Foundry Project. This is a recommendation, not a claim that the category has already been selected in the portal. Do not claim Agent Framework, MCP orchestration, Fabric or a multi-agent architecture: they are not implemented in this prototype.

## Links
- App: https://juanchomvasquez-premier-league-dna-app-1qylhs.streamlit.app/
- Public code: https://github.com/juanchomvasquez/premier-league-dna

## Before pasting
Verify the new code is deployed and run one real Azure generation before making the video or marking the integration demonstrated. The new integration has local tests with simulated model responses; this packet does not claim a new paid Azure smoke test. No video URL is supplied yet.
