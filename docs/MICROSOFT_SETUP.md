# Current submission: synthetic replay to Microsoft

The default Eight-position synthetic demo now uses the Microsoft analyst-brief
workflow directly. Choose Microsoft AI in Player overview and explicitly click
Generate Microsoft interpretation, or Generate Microsoft recap at full time.
Existing private Azure settings are reused. The code calls an Azure OpenAI
Responses endpoint for a model deployed through Microsoft Foundry.

English/Spanish and fan/broadcast focus are passed to the request. The model
receives observed facts and supported equal-window changes, never future events
or invented historical profile scores. Exact supporting numbers are rendered
locally; format/citation checks do not verify all prose semantics.

Refresh Microsoft brief during replay is off by default. If enabled, automatic
attempts are limited to once every thirty seconds per browser session when the
context changes. Recorded failures do not immediately retry the same context.
Each manual click is a separate potentially billable request. No global budget
cap is implied. Do not publish keys or include them in judge instructions.

The research view is off by default: its third-party data permissions are not
established. PL_DNA_ENABLE_RESEARCH=1 is an owner-controlled research gate, not a
licence. See submission/DATA_RIGHTS_REVIEW.md.

The remainder records earlier implementation details; where they differ, the
current synthetic workflow and docs/submission take precedence.

---

# Microsoft inference connector

The adapter targets Azure OpenAI's v1 Responses endpoint in Microsoft Foundry.
It uses HTTPS requests from the server and requires no additional SDK. Official reference:
https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses

## Current status

The existing claim-selection connector passed one live Azure test on 2026-10-23.
The match-development task has automated simulated-transport tests; its live test
is tracked separately. It is a model inference integration, not a deployed
Foundry Agent Service workflow or a multi-agent runtime.

## Configuration

Use a deployed model that supports the Responses API. Set these server environment
variables before starting Streamlit:

- `AZURE_OPENAI_BASE_URL`: resource URL ending in `/openai/v1/`, such as `https://YOUR-RESOURCE.openai.azure.com/openai/v1/`.
- `AZURE_OPENAI_DEPLOYMENT`: your deployment name.
- `AZURE_OPENAI_API_KEY`: the resource key, kept outside the repository.
- `PL_DNA_ENABLE_AZURE=1`: explicit server enablement.

`.env.example` documents the names; the app does not automatically load it.
In the app select Microsoft mode, then click Generate insight. That explicit click
makes one potentially billable inference request. Player, minute, and language
changes do not trigger automatic model requests. Local mode makes no model call.

## Grounding design

The model chooses and orders up to three measurements. Its response must copy the
counts and primary/secondary evidence IDs exactly. A validator rejects unexpected
fields, invented measurements, altered counts, missing IDs and arbitrary prose.
The renderer writes English or Spanish from the accepted claims using templates.
This checks consistency with supplied evidence; it does not validate the football
data, invented reference rates, or historical similarity.

Provider failure or invalid model output gives a labeled deterministic fallback.
The connector uses a 30-second timeout, one request without retry, a bounded
response size and `store=false`. Model availability and billing depend on your
actual Azure deployment and subscription.


## Match-development task

Microsoft mode now compares adjacent 15-minute windows at the selected minute,
independent of the overview window. The app computes both windows and supplies
only eligible changes to Azure. Azure acts as an editorial selector: it chooses
a lead and an optional complementary or contrasting development appropriate to
the player role and audience. It does not author unrestricted analytical prose.
The report displays the selected count changes, a definition-aware explanation,
a next-window observation prompt, and both windows' primary/supporting event IDs.

No call occurs before minute 30, when either window has fewer than three recorded
sequences, or when no changing measurement has at least three combined occurrences.
These are conservative display thresholds, not significance tests. Count decreases
are not interpreted as worse performance; no tactics, causes, ability ratings or
legend similarity are inferred. The first version of this brief is English-only;
local summaries retain Spanish. Failed validation produces no AI brief, and a
locally computed table remains available. One explicit button click makes one
request, without retries. Fixture tests exercise the new response contract.


## Current-season analyst brief (current UI)

The default current-season view supersedes the fixed-sentence workflows described
above. `performance_interpretation` requests a headline, a short AI-authored
interpretation and two or three known evidence IDs. Exact numerical facts are
rendered locally. Format and citation checks do not independently verify prose
semantics. Weak-fit output must not force a legend match. The local snapshot is
collapsed and contains counts, not a second story. The archived study is removed
from public navigation; its modules remain for research regression tests.
See CURRENT_SEASON_AND_LIVE.md for the current behavior and cost controls.
