# AI boundaries

Use when a feature sends data to a model, retrieves private content or lets model output influence actions. A local prototype with synthetic data needs less process than an agent with customer data and write credentials.

## Constrain authority outside the model

Map what the model can read, which input is untrusted and which effects its tools can cause. Retrieved text, email, tool results and model-generated arguments do not grant permission. Prompt wording or an injection detector alone is not an access-control boundary.

Enforce identity, allowed operations, destinations and parameter validation in application code. Scope credentials narrowly. For consequential actions, use the product's approved human confirmation or deterministic limits tied to the exact action; a model cannot approve its own refund or data export. Apply budgets, deadlines and bounded tool steps. An ambiguous write result needs outcome checking before a retry.

Treat generated output as untrusted: validate schemas and business constraints, encode rendered content, and do not execute generated SQL, shell code or tool names directly. A structurally valid response can still be unauthorized or wrong.

For MCP, verify the server's identity, intended scopes and token audience. Do not forward a token to an unrelated service or let server metadata authorize a new destination. Confirm current protocol/security requirements for the actual deployment.

## Keep retrieval within the caller's access

Enforce document permissions at query time, before content reaches the model: pass the caller's current user and group identities into the search filter on every request, and apply the same scope to snippets, caches and citations. Filtering only the final answer is too late, and a prompt instruction is not access control. Preserve document identity, version and provenance; propagate deletion and permission changes to indexes and caches.

Test two users with different access. Check retrieval separately from answer quality: the correct document may not be found, or the answer may misrepresent it. Define what to do when evidence is absent, stale or contradictory. A citation must support the claim, not merely name a related page.

## Verify the feature, not the prompt's appearance

Build a small evaluation set from the real task, with expected outcomes and cases for unavailable evidence, denied access, malicious retrieved instructions and failed tools. Use the models/configurations actually deployed. Keep a holdout set where feasible, and add each production failure to the set.

Name the metrics and thresholds before tuning. For retrieval-backed answers:

| Metric | Question it answers |
|---|---|
| Recall at k | Is a document that answers the question among the top k results? |
| Groundedness | Is every claim in the answer supported by the retrieved text? |
| Answer relevance | Does the answer address the question that was asked? |
| Correct refusal rate | Does it decline when evidence is missing or the caller lacks access? |
| Restricted-content leaks | Did any answer, snippet or citation expose a document the caller cannot read? The target is zero. |

Prefer code-based checks such as exact match, schema validation and citation presence. Validate a model-based grader against human labels before trusting it, and inspect disagreements rather than accepting its grades automatically. Measure cost and latency where they matter.

Rerun the set whenever the prompt, the model or its version, retrieval settings, chunking or tools change, and compare the results case by case with the current version. A drop below a threshold is a failing check. Passing a few cases is a smoke check, not proof of reliability across users or models. The optional [AI evaluation plan](../templates/ai-eval-plan.md) records the set, metrics, thresholds and triggers.

## Data sent to model providers

Check provider retention and processing location against the project's requirements before sending private data. Avoid raw prompts/documents in telemetry by default. Preserve approved logging needed to investigate actions, with redaction and bounded retention.

## Sources

- [OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- [MCP security best practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices)
- [Microsoft: document-level access in search](https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview)
- [OWASP Top 10 for LLM applications: vector and embedding weaknesses](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)
- [Introduction to Information Retrieval: evaluating ranked results](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html)
- [TruLens: the RAG triad](https://www.trulens.org/getting_started/core_concepts/rag_triad/)
