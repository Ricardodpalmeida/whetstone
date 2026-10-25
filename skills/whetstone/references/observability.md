# Observability

Read this when you add a service, endpoint, job or dependency, when you add or change logging, when you define alerts, dashboards or service level objectives, and before any T2 or T3 release.

## Contents

- [Instrument as you build](#instrument-as-you-build)
- [Write structured logs](#write-structured-logs)
- [Keep secrets and personal data out of telemetry](#keep-secrets-and-personal-data-out-of-telemetry)
- [Record security events](#record-security-events)
- [Trace requests across services](#trace-requests-across-services)
- [Emit metrics that answer questions](#emit-metrics-that-answer-questions)
- [Define service level objectives](#define-service-level-objectives)
- [Alert on symptoms, using burn rates](#alert-on-symptoms-using-burn-rates)
- [Prove the telemetry works](#prove-the-telemetry-works)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Instrument as you build

Telemetry is part of the feature, written in the same change. Before you write code, list the questions an operator will ask at 3 a.m.: Is it working? For whom is it failing? Since when? Which dependency is slow? Then make sure logs, traces and metrics can answer each one.

## Write structured logs

Apply it:

1. Emit logs as structured events (for example JSON), one event per line, to standard output. Let the platform collect and route them.
2. Include on every event: a UTC timestamp, level, a stable event name, a human-readable message, service name, version, environment, and the trace and span identifiers of the current request.
3. Use levels consistently. ERROR means someone may need to act; WARN means degraded but handled; INFO records significant business or lifecycle events; DEBUG is off in production by default.
4. Log an error once, where it is handled, with its context and cause chain. Logging and re-raising at every layer floods the logs with duplicates.
5. Log facts as fields, not baked into message text, so they can be queried: `{"event": "payment_declined", "order_id": "o_123", "reason": "insufficient_funds"}`.
6. Avoid logging inside tight loops or on every successful health check. Volume costs money and hides the signal.

## Keep secrets and personal data out of telemetry

OWASP's logging guidance lists data that should never be logged directly, including passwords, access tokens, session identifiers, connection strings, encryption keys, payment card and bank data, and sensitive personal data such as health information or government identifiers.

Apply it:

1. Log identifiers (user ID, order ID) instead of personal data (names, email addresses, free-text input).
2. Redact or drop sensitive fields centrally in the logging configuration, and also at the source. If you need to correlate sessions, log a keyed hash rather than the session identifier.
3. Never log full request or response bodies, headers containing credentials, or prompts and completions that may contain personal data, unless capture is explicitly enabled for a non-production environment.
4. Neutralise user-controlled text before logging it, so newline characters cannot forge log entries.
5. Add a test that exercises a flow with a known secret value and asserts the value does not appear in captured logs.

## Record security events

OWASP lists security logging and alerting failures in its Top 10 (A09:2025). Record at least: sign-in success and failure, multi-factor events, password and permission changes, authorisation failures, input validation failures that suggest probing, administrative actions, and changes to security configuration. Each event names the actor, action, target, outcome, time and source, and is kept where the actor cannot change it.

## Trace requests across services

Apply it:

1. Use OpenTelemetry for traces, metrics and logs, so instrumentation is vendor-neutral and the back end can change without code changes.
2. Propagate context with the W3C Trace Context `traceparent` header across every HTTP call, and carry it in message metadata across queues, so a trace survives asynchronous hops. Its format is `version-traceid-parentid-flags`, for example `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`.
3. Set the resource attributes `service.name`, `service.version` and `deployment.environment.name` on every service.
4. Follow the OpenTelemetry semantic conventions for attribute names. The HTTP client and server span conventions are stable; the generative AI conventions now live in a separate repository and are still at Development stability, so expect renames (see [ai-features.md](ai-features.md)).
5. Prefer automatic instrumentation for frameworks and clients, then add manual spans around significant business operations.
6. Choose a sampling strategy deliberately and keep every trace that contains an error.

## Emit metrics that answer questions

| Method | Applies to | Measures |
|---|---|---|
| RED | Request-driven services | Rate, Errors, Duration |
| USE | Resources such as CPU, memory, disks, pools, queues | Utilisation, Saturation, Errors |
| Four golden signals | User-facing systems | Latency, Traffic, Errors, Saturation |

Apply it:

1. Record latency as a histogram, so you can compute percentiles; never only an average. Track the latency of failed requests separately from successful ones.
2. Keep label cardinality bounded. User IDs, request IDs, raw URLs and email addresses do not belong in metric labels; use route templates such as `/orders/{id}`.
3. Add a few business metrics for the feature (orders placed, exports completed), because technical metrics can look healthy while the product is broken.

## Define service level objectives

Apply it:

1. Express each service level indicator as a ratio of good events to total events, such as successful requests divided by all requests, or requests faster than 300 ms divided by all requests.
2. Keep to five or fewer indicators per service, chosen from what users experience: availability, latency, correctness, freshness.
3. Set objectives below 100 percent. Google's SRE workbook calls 100 percent the wrong target: it is unattainable and blocks change.
4. Write an error budget policy that says what happens when the budget is spent (for example, reliability work takes priority over features), and get the owners to agree to it before you need it.

## Alert on symptoms, using burn rates

Page on what users experience, not on internal causes. Every page must be urgent and actionable, and must link to a runbook (see [the runbook template](../templates/runbook.md)). Anything that can wait until working hours is a ticket.

Burn rate is how fast the service spends its error budget relative to the objective. Google's SRE workbook recommends multiwindow, multi-burn-rate alerts; for a 99.9 percent objective:

| Severity | Long window | Short window | Burn rate | Budget consumed |
|---|---|---|---|---|
| Page | 1 hour | 5 minutes | 14.4 | 2 percent |
| Page | 6 hours | 30 minutes | 6 | 5 percent |
| Ticket | 3 days | 6 hours | 1 | 10 percent |

Both windows must exceed the burn rate before the alert fires. The short window lets the alert reset quickly once the problem stops.

## Prove the telemetry works

Apply it:

1. Trigger the failure path in a test or staging environment and confirm that the log event, the trace with its error status, the metric and, where defined, the alert all appear.
2. Check that a single request can be followed from the entry point through every service and queue using its trace identifier.
3. Add or update the dashboard for the feature in the same change, showing its RED metrics and business metrics.

Check:

- [ ] New code paths emit structured logs with trace identifiers and no sensitive data.
- [ ] New dependencies are traced and have latency and error metrics.
- [ ] Every new alert is symptom-based, actionable and linked to a runbook.

## Failure modes

- Logs are free text, so the one question that matters during an incident cannot be queried.
- An access token is logged at DEBUG level, and DEBUG is turned on in production during an incident.
- A metric labelled with user IDs explodes in cardinality and the monitoring bill.
- Alerts fire on CPU usage while users see errors that no alert covers.
- Context is not propagated through the queue, so traces end at the producer and the slow consumer stays invisible.

## Sources

- Google's SRE book, [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/), defines the four golden signals and argues for symptom-based, actionable pages.
- Google's SRE workbook, [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) and [Implementing SLOs](https://sre.google/workbook/implementing-slos/), provide the burn-rate table, SLI ratios and error budget policies.
- Brendan Gregg, [The USE Method](https://www.brendangregg.com/usemethod.html), and Tom Wilkie, [The RED Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/), define the two metric methods.
- W3C, [Trace Context](https://www.w3.org/TR/trace-context/), defines the `traceparent` header.
- OpenTelemetry, [semantic conventions](https://opentelemetry.io/docs/specs/semconv/), [HTTP spans](https://opentelemetry.io/docs/specs/semconv/http/http-spans/) and [deployment environment](https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/), give attribute names and stability; the [GenAI conventions repository](https://github.com/open-telemetry/semantic-conventions-genai) hosts the generative AI conventions.
- OWASP, [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html), lists data not to log; it is CC BY-SA, so the list above is paraphrased.
