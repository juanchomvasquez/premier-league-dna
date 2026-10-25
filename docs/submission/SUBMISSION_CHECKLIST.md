# Submission checklist — 25 October 2026

Target: finish the submission on Monday, October 26, keeping Tuesday as a buffer. Official closing time is October 27 at 11:59 p.m. Pacific, equivalent to October 28 at 2:59 a.m. in Sunrise, Florida. Confirm the portal's displayed deadline before final submission.

## Prepared in this package
- Synthetic events connected to the same Microsoft analyst-brief workflow.
- Accelerated replay, pause/reset and a full-time recap phase.
- Player, position, window, language and brief-focus personalization.
- Exact measurement/event evidence and safe fallback behavior.
- English project title, tagline, pitch, description and technology list: PROJECT_PITCH.md.
- Judge access and testing instructions: JUDGE_INSTRUCTIONS.md.
- Runtime explanation: ARCHITECTURE.md.
- Source/permission review and research boundary: DATA_RIGHTS_REVIEW.md.
- Public GitHub visibility confirmed via repository metadata on October 25: private=false, branch=main.
- Existing public app page returned HTTP 200 using an anonymous cookie-enabled request. This does not verify the new local code is deployed.
- 132 local tests passed, including replay, future-event exclusion, personalization, recap phase, fallback and per-session AI throttling. Tests used simulated model responses; no paid Azure smoke test was made.

## Still requires the owner's action
- Upload this package's extracted files to GitHub and reboot Streamlit. This session has not published changes or changed the repository.
- Verify the latest default view on the public app, including a phone browser.
- Make one real Azure synthetic interpretation request and one final recap request. Tests use simulated model responses, so actual deployed generation quality remains to be checked.
- Paste the final text and testing instructions into the project page. Recommended category: Best Use of Microsoft Foundry Project; this is not yet selected in the portal.
- Record and publish the required video under two minutes, then add its public URL. Video intentionally not created in this session.
- Complete any remaining portal fields and submit; save the confirmation. A project draft or uploaded GitHub files are not final submission confirmation.
- Keep the working app available free to judges through the judging period, which the official rules list as ending November 10. Monitor its server-side Azure availability and cost.

## Scope held for this submission
Do not depend on an actual PL match being in progress. Today's Sunday October 25 fixtures are listed at 10:00 a.m. and 12:30 p.m. Florida time; Monday October 26 currently has no PL fixtures. More importantly, the public-feed connector's reuse permissions are not established. The synthetic stream is the primary reproducible judging route.

Real data rights beyond the synthetic route, validated historical similarity, production data-service reliability and multi-agent orchestration are not claimed completed. Those are future work rather than fabricated achievements.

## Review sources
Official hackathon rules: https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md
Official fixture schedule: https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season
