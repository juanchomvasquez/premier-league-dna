# Match-development analysis update

Microsoft AI mode now answers: what changed in the last 15 minutes?

- Compares adjacent nonoverlapping 15-minute windows ending at the selected minute.
- Azure selects a lead and optional supporting or contrasting development.
- Shows the count change, metric explanation, next-window watch prompt and event evidence.
- Does not equate fewer actions with worse performance or infer tactical causes.
- Local summaries remain unchanged. Analysis briefs are currently English-only.
- Calls Azure only on Generate match analysis. No new live Azure requests were made during development.
- Includes role-specific legend widget keys to avoid carrying a prior position's selection into another position.

Validation: 90 local automated tests passed. Focused tests against the prepared live-version app passed using simulated providers, including explicit-call boundaries, accepted analysis, broadcaster output, and early-minute handling.

Based on live GitHub main commit 096416a7fd312f42aaf7c3984ca655d6844211dd. The app.py patch preserves the currently deployed features and excludes the separate career/recorded-event preview work. Publishing has not occurred: GitHub API returned 403 Resource not accessible by integration.

Replace each included file at the matching repository path. Do not upload the ZIP itself as application source. No credentials are included.
