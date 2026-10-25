# AI features

Read this when you build or change a feature that calls a language model or another generative model: chat, summarisation, extraction, classification, code generation, agents that call tools, and MCP servers or clients. Retrieval and evaluation are covered in [rag-and-evals.md](rag-and-evals.md).

## Contents

- [Decide whether a model is the right tool](#decide-whether-a-model-is-the-right-tool)
- [Map the risks](#map-the-risks)
- [Treat model input as untrusted](#treat-model-input-as-untrusted)
- [Treat model output as untrusted](#treat-model-output-as-untrusted)
- [Constrain agents and tools](#constrain-agents-and-tools)
- [Build MCP servers and clients safely](#build-mcp-servers-and-clients-safely)
- [Protect data in prompts and context](#protect-data-in-prompts-and-context)
- [Engineer for reliability, cost and latency](#engineer-for-reliability-cost-and-latency)
- [Manage prompts and models as code](#manage-prompts-and-models-as-code)
- [Observe the feature](#observe-the-feature)
- [Meet governance and legal duties](#meet-governance-and-legal-duties)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Decide whether a model is the right tool

Apply it:

1. Use deterministic code when the rules can be written down. A model is the right tool when inputs are open-ended language or images and an occasional wrong answer is tolerable or can be caught.
2. Write down the acceptable error rate, who sees a wrong answer, and what happens next. If a wrong answer can cause harm that nobody will catch, add a human review step or do not ship.
3. Estimate cost per request and per user per month at expected volume before building.
4. Define success criteria and an evaluation set before writing prompts (see [rag-and-evals.md](rag-and-evals.md)).

## Map the risks

The OWASP Top 10 for LLM Applications, 2026 edition (published August 2026), lists the risks to check:

| Risk | What to do about it |
|---|---|
| LLM01 Prompt Injection | Separate instructions from data, enforce controls outside the model, constrain tools |
| LLM02 Sensitive Information Disclosure | Minimise data sent to the model, filter outputs, enforce access control on retrieved data |
| LLM03 Excessive Agency | Least-privilege tools, per-user authorisation, human approval for consequential actions |
| LLM04 Supply Chain | Vet models, datasets, plug-ins and MCP servers like any dependency (see [supply-chain.md](supply-chain.md)) |
| LLM05 Data and Model Poisoning | Control and review what enters training data, fine-tuning sets and retrieval indexes |
| LLM06 Unbounded Consumption | Token limits, rate limits, budgets and alerts per user and per tenant |
| LLM07 Misinformation | Ground answers in sources, show citations, evaluate accuracy, tell users about limits |
| LLM08 Hidden Context Exposure | Assume system prompts and hidden context can leak; keep secrets out of them |
| LLM09 Vector and Embedding Weaknesses | Permission-aware retrieval, tenant separation in indexes, provenance of stored content |
| LLM10 Improper Output Handling | Validate and encode output before any downstream use |

For agents, OWASP's Top 10 for Agentic Applications for 2026 adds risks such as agent goal hijacking, tool misuse, identity and privilege abuse, memory and context poisoning, insecure communication between agents, cascading failures across agents, and exploitation of human trust in agents. Use both lists in the threat model (see [threat-modeling.md](threat-modeling.md)).

## Treat model input as untrusted

Prompt injection cannot be fully prevented by prompt wording. Any text the model reads (user messages, retrieved documents, web pages, emails, tool results, file contents, code comments) can carry instructions.

Apply it:

1. Keep trusted instructions separate from untrusted content, and mark content clearly as data. Labels and delimiters help the model but are not a security boundary.
2. Enforce every security decision in code outside the model: authorisation, input limits, which tools exist, which arguments are allowed.
3. Use injection classifiers or guardrail models as an extra layer for detection and logging, never as the only control.
4. Rate-limit and monitor repeated attempts, since attackers try many variations until one works.
5. Test with direct and indirect injection cases in the evaluation set.

## Treat model output as untrusted

Apply it:

1. Request structured output (JSON matching a schema) when code will consume the result, and validate it against the schema. Reject or retry on validation failure instead of guessing.
2. Encode output for its destination before rendering it: HTML-escape it, and do not let model-generated Markdown load remote images or links automatically, because a crafted URL can carry data out of the page.
3. Never execute model output as code, SQL, shell commands or file paths without a sandbox, an allowlist and, for consequential actions, human review.
4. Show users that content is AI-generated where it matters, and give them a way to report bad answers.

## Constrain agents and tools

Simon Willison's lethal trifecta is the core test: an agent that has access to private data, is exposed to untrusted content, and can communicate externally can be tricked into sending that data to an attacker. Remove at least one of the three for any agent that reads untrusted content.

Apply it:

1. Give each tool the narrowest capability that works: read-only where possible, scoped to the current user's data, with an allowlist of destinations and argument validation.
2. Authorise every tool call in code against the end user's permissions, not the agent's service identity.
3. Require explicit human approval for consequential or irreversible actions: payments, deletions, outbound messages, publishing, merging code, changing permissions.
4. Run generated code in a sandbox with no credentials, no network by default, and limits on CPU, memory and time.
5. Cap steps, tool calls, tokens and spend per task, and stop with a clear message when a cap is reached.
6. Keep an audit log of every tool call with its arguments, the acting user and the outcome.
7. Isolate memory and context between users and tenants, and review what an agent writes into long-term memory, because poisoned memory persists across sessions.

## Build MCP servers and clients safely

The Model Context Protocol's security best practices give specific rules. In short:

1. An MCP server must not accept tokens that were not issued for it, and must not pass a client's token through to downstream APIs ("token passthrough" is forbidden by the specification).
2. An MCP server that proxies a third-party API with a static client identifier must obtain consent per client before forwarding authorisation requests, to avoid confused-deputy attacks.
3. Verify every inbound request. Possession of a session or state handle is not authentication; generate handles randomly and bind them to the user.
4. Make OAuth `state` values single-use and short-lived, and validate authorisation URLs (HTTPS only, no `javascript:` or `file:` schemes); clients must open URLs without invoking a shell.
5. Request the minimum scopes, and protect any server-side fetching against SSRF (see [security.md](security.md)).
6. Treat local MCP servers as code running with the user's privileges: install them only from trusted sources and review the command before first run.

## Protect data in prompts and context

Apply it:

1. Never put secrets, credentials or internal-only data in system prompts or hidden context. Assume anything the model can see can be extracted.
2. Send the model only the personal data the task needs; mask or pseudonymise the rest.
3. Check the provider's data retention, training use and processing location against the project's requirements before sending real data (see [data-and-privacy.md](data-and-privacy.md)).
4. Apply the user's permissions to everything placed in the context, including retrieved documents and tool results.

## Engineer for reliability, cost and latency

Apply it:

1. Set timeouts on model calls, retry 429 and 5xx responses with backoff and jitter, and honour `Retry-After` (see [reliability-performance.md](reliability-performance.md)).
2. Stream responses for interactive use, and set a maximum output length for every call.
3. Enforce token and spend budgets per request, per user and per tenant, with alerts before limits are reached.
4. Cache responses or embeddings where inputs repeat and freshness rules allow.
5. Define the fallback when the model is unavailable or over budget: a smaller model, a cached answer, a non-AI path or a clear error.
6. Pin model versions or snapshots where the provider offers them, and track provider deprecation dates so upgrades are planned, evaluated and not forced.

## Manage prompts and models as code

Apply it:

1. Keep prompts in version control as templates, reviewed like code, with untrusted values inserted in clearly delimited slots.
2. Run the evaluation suite whenever a prompt, model, retrieval setting or tool definition changes, and compare results with the previous version before shipping.
3. Record the model identifier, prompt version and key parameters with every request, so any answer can be traced to its configuration.

## Observe the feature

Apply it:

1. Record per request: model, prompt version, input and output token counts, latency, finish reason, cost, tool calls and errors.
2. Follow the OpenTelemetry generative AI semantic conventions for attribute names where your tooling supports them. They are still at Development stability, so pin the convention version and expect renames.
3. Keep prompt and completion content capture off in production by default, because content routinely contains personal data. Enable it in non-production environments, or in production only with redaction and an agreed retention period.
4. Track user feedback, refusals, schema validation failures and guardrail triggers as quality signals.

## Meet governance and legal duties

The EU AI Act entered into force on 1 August 2024, and the AI Omnibus amendments entered into force on 27 July 2026. According to the European Commission's timeline, prohibited practices have applied since February 2025, transparency obligations from August 2026, high-risk obligations for Annex III use cases from 2 December 2027, and for Annex I products from 2 August 2028.

Apply it:

1. Tell people when they are interacting with an AI system, and mark AI-generated or manipulated content where the transparency rules require it.
2. Flag to the user, before building, any use that may be high-risk under the Act (for example recruitment, credit scoring, education or access to essential services) or prohibited. Classification is a legal decision for humans.
3. Use NIST's AI Risk Management Framework 1.0 and its Generative AI Profile (NIST AI 600-1) as a structure for identifying, measuring and managing risks, especially when no regulation applies.

Check:

- [ ] The threat model covers the OWASP LLM risks, and the lethal trifecta is broken for any agent reading untrusted content.
- [ ] Tool calls are authorised in code, and consequential actions need human approval.
- [ ] Output is validated and encoded before use; nothing generated runs unsandboxed.
- [ ] Budgets, timeouts and fallbacks exist; model and prompt versions are recorded.
- [ ] An evaluation suite runs on every prompt or model change.

## Failure modes

- A support bot summarises an email that contains hidden instructions, and forwards the customer database to an external address.
- A model-generated SQL query runs against production with the application's full privileges.
- An API key embedded in the system prompt is extracted by a user who asks the model to repeat its instructions.
- A loop of tool calls runs overnight and spends the monthly budget.
- The provider retires a model version, the replacement behaves differently, and nobody notices because there are no evaluations.
- Prompts and completions containing customer data are logged in plain text to a third-party observability service.

## Sources

- OWASP GenAI Security Project, [Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/); the entry list above is taken from the [project's repository](https://github.com/GenAI-Security-Project/GenAI-LLM-Top10) (CC BY-SA, summarised in this file's own words).
- OWASP GenAI Security Project, [Top 10 for Agentic Applications for 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/); the risk themes follow [Giskard's summary](https://www.giskard.ai/knowledge/owasp-top-10-for-agentic-application-2026) of the official document.
- OWASP, [LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html), describes layered defences against direct and indirect injection.
- Simon Willison, [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/).
- Model Context Protocol, [Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices), defines the token passthrough, confused deputy, session and URL rules summarised above.
- OpenTelemetry, [GenAI semantic conventions repository](https://github.com/open-telemetry/semantic-conventions-genai); Dash0, [OpenTelemetry GenAI semantic conventions explained](https://www.dash0.com/knowledge/opentelemetry-genai-semantic-conventions-explained), describes their Development status and opt-in content capture.
- European Commission, [AI Act regulatory framework](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai), gives the application timeline after the AI Omnibus. This file is engineering guidance, not legal advice.
- NIST, [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework), including the Generative AI Profile (NIST AI 600-1).
