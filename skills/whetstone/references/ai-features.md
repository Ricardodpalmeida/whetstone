# AI boundaries

Use when a feature sends data to a model, retrieves private content or lets model output influence actions. A local prototype with synthetic data needs less process than an agent with customer data and write credentials.

## Constrain authority outside the model

Map what the model can read, which input is untrusted and which effects its tools can cause. Retrieved text, email, tool results and model-generated arguments do not grant permission. Prompt wording or an injection detector alone is not an access-control boundary.

Enforce identity, allowed operations, destinations and parameter validation in application code. Scope credentials narrowly. For consequential actions, use the product's approved human confirmation or deterministic limits tied to the exact action; a model cannot approve its own refund or data export. Apply budgets, deadlines and bounded tool steps. An ambiguous write result needs outcome checking before a retry.

Treat generated output as untrusted: validate schemas and business constraints, encode rendered content, and do not execute generated SQL, shell code or tool names directly. A structurally valid response can still be unauthorized or wrong.

For MCP, verify the server's identity, intended scopes and token audience. Do not forward a token to an unrelated service or let server metadata authorize a new destination. Confirm current protocol/security requirements for the actual deployment.

## Keep retrieval within the caller's access

Enforce document permissions before content reaches the model, including snippets, caches and citations. Filtering only the final answer is too late. Preserve document identity, version and provenance; propagate deletion and permission changes to indexes and caches.

Test two users with different access. Check retrieval separately from answer quality: the correct document may not be found, or the answer may misrepresent it. Define what to do when evidence is absent, stale or contradictory. A citation must support the claim, not merely name a related page.

## Verify the feature, not the prompt's appearance

Build a small evaluation set from the real task, with expected outcomes and cases for unavailable evidence, denied access, malicious retrieved instructions and failed tools. Use the models/configurations actually deployed. Keep a holdout set where feasible, and inspect disagreements rather than trusting another model's grade automatically.

Compare a proposed prompt/model/retrieval change with the current behavior on the same cases. Measure the outcome that matters plus cost/latency where relevant. Passing a few cases is a smoke check, not proof of reliability across users or models.

Check provider retention and processing location against the project's requirements before sending private data. Avoid raw prompts/documents in telemetry by default. Preserve approved logging needed to investigate actions, with redaction and bounded retention.

## Sources

- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [MCP security best practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices)
- [Microsoft: document-level access in search](https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview)
