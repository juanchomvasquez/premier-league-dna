# Data sources and permission review

Reviewed 25 October 2026. This records the engineering review and unresolved permissions; it is not a legal opinion or a blanket rights clearance.

| Source | Use | Review outcome |
|---|---|---|
| Own deterministic synthetic events | Primary submission replay and AI payload | Generated in this project; no match footage or third-party live feed is needed |
| Premier League website/API | Historical headline facts and season research | Public visibility does not establish a general redistribution/API licence. Facts are attributed; no blanket permission is claimed. Further clearance is needed for unrestricted research/product reuse |
| ESPN public website endpoints | Current-season/live research | Disney/ESPN terms include restrictions on reuse and AI prompting. Permission for this connector has not been established. Not enabled in the default submission view |
| StatsBomb Open Data | Historical event research, including CDM samples | Agreement permits analysis/research and public conclusions with logo attribution, but restricts data redistribution and commercial exploitation. Raw event files are not bundled. Competition/future commercial use is not declared cleared |
| Azure / Microsoft Foundry | Synthetic-event model inference | Uses the owner's configured deployment and account. No judge credentials are requested |
| Club/player references | Contextual names and club-inspired colours | No official club crests, player photographs or match footage are supplied. No affiliation or endorsement is claimed |

## Submission boundary
Use the synthetic replay for the submitted demonstration and the runtime AI call. The current-season/live research mode is disabled by default; PL_DNA_ENABLE_RESEARCH=1 exposes it only after the owner has established the appropriate rights. The flag itself does not grant permission. Historical headline cards remain attributed contextual facts and are not sent into the synthetic AI prompt or used to validate its invented design profiles. Their use should not be described as officially licensed.

## Sources reviewed
- Disney terms, including ESPN and the consumer-license restrictions: https://disneytermsofuse.com/english/ (Section 2A).
- StatsBomb Public Data User Agreement: https://github.com/hudl/open-data/blob/master/LICENSE.pdf (analysis/research, restrictions and logo attribution).
- Hackathon rules: https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md (third-party integrations, submission ownership and footage/data sourcing).
- PL terms page attempted: https://www.premierleague.com/en/legal/terms-conditions. It was not successfully retrieved during this check; no clearance is inferred from that failure.

## Not done automatically
No permission request was sent to a provider, no terms were accepted on the user's behalf, and no conclusion that every public dataset is submission-cleared is made. Keep the research view out of the judge demonstration until its permissions are established. The submitted video must use screen recordings of the app, without unlicensed match footage or music.
