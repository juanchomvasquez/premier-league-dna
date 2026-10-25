# Runtime architecture

| Stage | Implementation | Evidence boundary |
|---|---|---|
| Synthetic event source | pl_dna/roles.py creates deterministic football action scenarios | Fictional players/events; no official live feed is required |
| Timed release | Streamlit fragment and synthetic_replay.advance_clock | Only rows observed by the replay minute contribute |
| Football measurements | analyze_role_player and synthetic_brief_payload | Exact event IDs, linked support actions and explicit windows |
| Microsoft interpretation | Azure OpenAI Responses API via the Foundry deployment | AI receives observed facts, supported equal-window changes and separately labelled invented profile comparisons; no measured historical similarity is claimed |
| Checked output | analyst_brief response validation | Known, distinct measurement citations; format/length/numerical-token checks; semantic truth is not guaranteed |
| Screen and personalization | Streamlit overview, wheel, evidence, player/window/language/focus controls | Changed selection hides stale output; running replay may retain an explicitly timestamped prior brief; exact numbers are rendered locally |

The prototype uses one model call per requested brief. It is not a multi-agent system and the model does not autonomously call tools. The deterministic analysis functions are ordinary Python code surrounding the inference call.

## Event timing and recap
The generated fixture is held locally, but the analysis filters it by observed time. Primary and supporting event IDs cannot use future rows. A new replay tick updates the local calculations without an Azure request unless optional automatic AI was enabled. The final phase asks for a full-time recap. The replay stops at full time; the screen remains available for review.

## Cost and failures
No inference call on startup, player/slider/language changes or ordinary replay ticks with automatic AI off. Manual clicks make individual requests. Optional automatic attempts are throttled to thirty seconds, with attempt state saved before calling and no retry for the same context. This is a per-session control, not a global Azure spending cap. Provider exceptions are replaced by safe fallback text without echoing credentials.

## Deliberate research boundary
The current-season/live and historical-event research modules remain in the codebase, including the retired roster and explicit match-sample coverage. The public submission route does not use them as a real-time data provider. They can be exposed only by the owner setting PL_DNA_ENABLE_RESEARCH=1 after establishing appropriate data-use rights. That flag is not a licence. Review DATA_RIGHTS_REVIEW.md before enabling.

## Illustrative legend-inspired explanation
The synthetic route ranks the existing invented role profiles using normalized distance and independent scores. At least ten sequences are needed. A provisional demo display policy admits distances up to 0.75, and a second eligible profile only within five score points of the first. This policy is not historically calibrated. The model explains only eligible named profiles and must label any resemblance illustrative/invented and inspired. Independent scores are displayed locally, never converted to percentage blends. A weak match has no candidates; it is not a poor-performance verdict. Stored briefs retain the comparison from their generation window.
