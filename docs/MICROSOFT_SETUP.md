# Microsoft inference connector

The adapter targets Azure OpenAI's v1 Responses endpoint in Microsoft Foundry.
It uses HTTPS requests from the server and requires no additional SDK. Official reference:
https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/responses

## Current status

The connector has been tested with a simulated response transport. No live Azure
model call has been verified. It is a model inference integration, not a deployed
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
