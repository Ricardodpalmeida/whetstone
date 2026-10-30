# API design

Use for interfaces other code depends on: HTTP APIs, events/messages, webhooks, public library functions, CLI flags and configuration formats.

## Contents

- [Design the contract first](#design-the-contract-first)
- [Model resources consistently](#model-resources-consistently)
- [Use HTTP semantics correctly](#use-http-semantics-correctly)
- [Return errors as problem details](#return-errors-as-problem-details)
- [Make writes safe to retry](#make-writes-safe-to-retry)
- [Paginate from the start](#paginate-from-the-start)
- [Evolve without breaking clients](#evolve-without-breaking-clients)
- [Deprecate deliberately](#deprecate-deliberately)
- [Design events, webhooks and long-running operations](#design-events-webhooks-and-long-running-operations)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Design the contract first

1. Write or update the machine-readable contract before the implementation: OpenAPI 3.1 or later for HTTP APIs, AsyncAPI for event-driven interfaces.
2. Review the contract as the main artefact of the change. Ask whether a client developer could use it correctly without reading your code.
3. Generate reference documentation, and client code where useful, from the contract, and validate requests and responses against it in tests (see [testing.md](testing.md)).
4. Treat a new public API as T2 or above, and a change to a public contract as T3 when it can break existing consumers.

## Model resources consistently

1. Name resources with plural nouns and use consistent casing for paths and fields across the API. Follow the existing API's conventions over your preferences.
2. Use opaque, stable identifiers. Never expose sequential database keys when enumeration would leak information.
3. Send timestamps as RFC 3339 strings in UTC, money as an integer amount in minor units plus an ISO 4217 currency code, and durations with their unit in the field name.
4. Document every enumeration and tell clients to tolerate values they do not recognise, so you can add values later.
5. Keep response shapes predictable: the same field means the same thing everywhere, and absent and `null` have documented meanings.

## Use HTTP semantics correctly

| Method | Safe | Idempotent | Typical use |
|---|---|---|---|
| `GET` | Yes | Yes | Read a resource or collection |
| `PUT` | No | Yes | Replace a resource at a known URI |
| `DELETE` | No | Yes | Remove a resource |
| `PATCH` | No | No (unless designed to be) | Partial update |
| `POST` | No | No | Create in a collection, or trigger an action |

| Status | Use it when |
|---|---|
| 200, 201, 204 | Success with a body, a created resource (with `Location`), or no body |
| 202 | Work was accepted and continues asynchronously |
| 400 | The request is malformed |
| 401 | Authentication is missing or invalid |
| 403 | The caller is authenticated but not allowed (or 404, when revealing existence would leak information) |
| 404 | The resource does not exist for this caller |
| 409 | The request conflicts with the current state |
| 412, 428 | A precondition (`If-Match`) failed, or the server requires one |
| 413 | The request body is too large |
| 422 | The request is well formed but semantically invalid |
| 429 | The caller exceeded a rate limit; include `Retry-After` |
| 500, 503 | A server fault, or temporary unavailability (with `Retry-After` when known) |

Prevent lost updates: return an `ETag`, require `If-Match` on updates, return 412 on mismatch.

## Return errors as problem details

RFC 9457 supersedes RFC 7807 and defines `application/problem+json` error bodies.

1. Return the members `type` (a URI identifying the problem type, defaulting to `about:blank`), `title`, `status`, `detail` and `instance`.
2. Write `detail` to help the client fix the request, not to debug the server. Never include stack traces, SQL or internal hostnames.
3. Add extension members for machine-readable specifics, such as a list of invalid fields, and document them. Clients must ignore extensions they do not recognise.

```json
{
  "type": "https://api.example.com/problems/insufficient-credit",
  "title": "Insufficient credit",
  "status": 409,
  "detail": "The order total is 120.00 EUR but the available credit is 80.00 EUR.",
  "instance": "/orders/o_9f2c",
  "available_credit_minor": 8000
}
```

## Make writes safe to retry

Clients retry after timeouts without knowing whether the first attempt succeeded. The Idempotency-Key pattern remains an Internet-Draft: draft-ietf-httpapi-idempotency-key-header-08.

1. Accept an `Idempotency-Key` header on non-idempotent operations that create or charge, and recommend a random UUID per logical operation.
2. Store the key with a fingerprint of the request and the response. On a repeat with the same key and payload, return the stored response without repeating the side effect.
3. Follow the draft's error handling: 400 when a required key is missing, 422 when a key is reused with a different payload, and 409 when a request with the same key is still in progress.
4. Publish how long keys are kept, and expire them after that period.

## Paginate from the start

Design pagination into the first version: Google's AIP-158 classifies adding it to an existing list endpoint as breaking.

1. Use opaque cursor tokens rather than offsets for collections that change, so items are not skipped or repeated.
2. Accept a page size with a documented default and maximum, and clamp larger values to the maximum.
3. Signal the end of the collection only with an empty next-page token, because a short page does not mean the last page.
4. Never let a page token grant access. Check authorisation on every page request.

## Evolve without breaking clients

Treat all observable behaviour as contract. Hyrum's Law: "all observable behaviors of your system will be depended on by somebody" given enough users.

| Usually compatible | Breaking |
|---|---|
| Adding an endpoint, an optional request field, or a response field | Removing or renaming anything |
| Adding an enumeration value to a request type | Adding a required request field |
| Accepting a wider range of input | Changing a field's type, format or default |
| Adding a new optional header | Changing semantics, status codes or error types clients rely on |
| | Adding enumeration values to responses when clients were not told to tolerate them |

1. Make additive changes where possible, and use parallel change (add the new form, migrate clients, remove the old form) for the rest.
2. Introduce a new major version only for unavoidable breaking changes, run both versions during the migration, and keep the version scheme the API already uses.
3. Check every contract change with an automated compatibility diff of the OpenAPI or schema files in CI.

## Deprecate deliberately

1. Announce deprecation with the `Deprecation` response header (RFC 9745), whose value is a structured date in Unix seconds (for example `@1814399999`, which is 30 June 2027 at 23:59:59 UTC), and link to migration information with a `Link` header using the `deprecation` relation.
2. Announce the shutdown date with the `Sunset` header (RFC 8594), an HTTP date such as `Sunset: Fri, 31 Dec 2027 23:59:59 GMT`, which must not be earlier than the deprecation date.
3. Measure who still calls the deprecated surface, contact them, and do not remove it while significant traffic remains without an explicit decision.
4. Document the timeline and the migration path in the changelog and the reference docs.

## Design events, webhooks and long-running operations

1. Give each event a unique identifier, a type, a schema version, the time it happened and the identifier of the entity it concerns. Version event schemas like any other contract.
2. Assume at-least-once delivery and possible reordering. Consumers deduplicate by event identifier and tolerate events that arrive out of order.
3. Publish events from database changes with the transactional outbox pattern: write the event to an outbox table in the same transaction as the change, and let a relay publish it. This avoids losing events or announcing changes that rolled back.
4. Sign webhook payloads (for example with an HMAC over a timestamp and the body), reject stale timestamps, retry failed deliveries with backoff, and let receivers fetch missed events.
5. For operations that take longer than a normal request, return 202 with a status resource the client can poll, and make the final result retrievable.
6. Protect every API with authentication, object-level authorisation, rate limits and request size limits, as described in [security.md](security.md).

- [ ] The contract file changed in the same PR as the behaviour, and a compatibility check ran.
- [ ] Errors use problem details without internal information.
- [ ] Non-idempotent creates accept an idempotency key, and list endpoints paginate.
- [ ] Any breaking change has a version or a deprecation plan with dates.

## Failure modes

- Renaming a field breaks deployed mobile clients.
- Unbounded lists pass tests but time out at 200,000 customer records.
- Retrying a timed-out payment charges twice.
- Default error handlers expose HTML stack traces.
- Publishing before commit makes downstream systems act on rolled-back changes.

## Sources

- OpenAPI Initiative, [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) (3.2.1 is the latest at the time of writing), and [AsyncAPI](https://www.asyncapi.com/docs).
- IETF, [RFC 9110 HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html), [RFC 6585 Additional HTTP Status Codes](https://www.rfc-editor.org/rfc/rfc6585.html), [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html), [RFC 9745 Deprecation header](https://www.rfc-editor.org/rfc/rfc9745.html) and [RFC 8594 Sunset header](https://www.rfc-editor.org/rfc/rfc8594.html).
- IETF, [The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/), an Internet-Draft.
- Google, [AIP-158 Pagination](https://google.aip.dev/158) and [AIP-180 Backwards compatibility](https://google.aip.dev/180).
- Hyrum Wright, [Hyrum's Law](https://www.hyrumslaw.com/), is the source of the quotation.
- Chris Richardson, [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html), describes the outbox pattern.
