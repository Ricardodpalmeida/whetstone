# Reliability and performance

Use for network calls, background work, significant load or latency, throughput and availability targets.

## Contents

- [Put a timeout on every remote call](#put-a-timeout-on-every-remote-call)
- [Retry only what is safe](#retry-only-what-is-safe)
- [Contain failures](#contain-failures)
- [Health checks and graceful lifecycle](#health-checks-and-graceful-lifecycle)
- [Measure before you optimise](#measure-before-you-optimise)
- [Fix the usual performance problems](#fix-the-usual-performance-problems)
- [Meet front-end performance targets](#meet-front-end-performance-targets)
- [Test under load](#test-under-load)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Put a timeout on every remote call

Missing timeouts can hold threads, connections and user requests forever; many clients default to none.

| Client | Default behaviour | What to do |
|---|---|---|
| Python Requests | No timeout unless you pass one | Pass `timeout=(connect, read)` on every call |
| Python HTTPX | Raises after 5 seconds of network inactivity | Set an explicit timeout on the client that fits the dependency |
| .NET `HttpClient` | 100 seconds | Set attempt and total timeouts, for example through a resilience handler (see [stack-dotnet.md](stack-dotnet.md)) |
| `fetch` in browsers and Node.js | No timeout option of its own | Pass `signal: AbortSignal.timeout(ms)` |

1. Set connect and read (or total) timeouts on every HTTP, database, cache, queue and model call.
2. Derive the value from the dependency's measured latency. The AWS Builders' Library suggests choosing an acceptable rate of false timeouts (for example 0.1 percent) and setting the timeout near the matching latency percentile (p99.9).
3. Propagate deadlines. When a request arrives with 2 seconds left, downstream calls get what remains of those 2 seconds, not a fresh hard-coded value. Check the remaining time before expensive steps and stop doomed work early.
4. Make the caller's timeout longer than the sum of the callee's timeouts and retries, or the caller gives up while work continues below it.

## Retry only what is safe

Retries trade server capacity for one caller's success, helping transient failures but worsening sustained ones.

1. Retry only operations that are idempotent, or made idempotent with an idempotency key (see [api-design.md](api-design.md)).
2. Retry only transient failures: connection errors, timeouts, and HTTP 408, 429, 500, 502, 503 and 504. Do not retry other 4xx responses. Honour a `Retry-After` header when one is sent.
3. Use capped exponential backoff with full jitter: sleep a random time between zero and `min(cap, base * 2 ** attempt)`. Jitter stops clients that failed together from retrying together.
4. Cap attempts. Google's SRE book describes allowing at most three attempts per request and retrying only while retries stay below 10 percent of a client's requests.
5. Retry at one layer only, ideally the layer immediately above the one that failed. Three attempts at each of five layers can multiply load on the bottom layer by 243 (three to the fifth power).
6. Log and count retries. A rising retry rate is an early warning.

```python
import random


def backoff_delay(attempt: int, base: float = 0.1, cap: float = 5.0) -> float:
    """Full jitter: random delay between 0 and the capped exponential bound."""
    return random.uniform(0, min(cap, base * 2 ** attempt))
```

## Contain failures

1. Wrap calls to a dependency that can fail in bulk with a circuit breaker: after failures cross a threshold, fail fast for a cooling period, then let a trial call through.
2. Bound concurrency per dependency (a bulkhead), so one slow dependency cannot consume every worker or connection.
3. Bound every queue and buffer, and decide what happens when it is full: reject, shed the oldest, or apply back-pressure to the producer.
4. Shed load early and cheaply when overloaded, before resources run out. Serving some users well beats serving every user badly.
5. Define degraded modes in advance (cached results, fewer features, read-only mode), exercise them regularly, and alert when the system enters them.
6. Make background jobs and message consumers idempotent and resumable, with a dead-letter destination for messages that keep failing.

## Health checks and graceful lifecycle

1. Expose separate signals for liveness (the process is not stuck), readiness (it can serve traffic now) and, for slow starters, start-up.
2. Keep liveness checks local to the process. If liveness depends on a database, a database outage makes the orchestrator restart every replica at once, adding load at the worst moment. Put dependency checks in readiness.
3. On a termination signal, stop accepting new work, mark the instance not ready, finish in-flight work within a deadline, then exit.
4. Start quickly. Long start-up times slow down deploys, rollbacks and autoscaling.

## Measure before you optimise

1. Define the target first, as a percentile with a load level: "p95 under 300 ms at 200 requests per second".
2. Measure the current state with production-like data volumes. Profile to find where time actually goes before changing code.
3. Report percentiles (p50, p95, p99), not averages. Dean and Barroso's "The Tail at Scale" shows that rare slow responses dominate user experience once a request fans out to many servers.
4. Change one thing, measure again, and keep the change only if the numbers improved.
5. Add a regression check (a benchmark or a performance budget in CI) for paths with a stated target.

## Fix the usual performance problems

| Symptom | Usual cause | Fix |
|---|---|---|
| Query count grows with result size | N+1 queries from lazy loading | Eager-load or batch the related records |
| One query is slow at scale | Missing index, or a function applied to an indexed column | Read the query plan, add or fix the index (see [data-and-privacy.md](data-and-privacy.md) for safe index creation) |
| Memory or latency grows with data size | Unbounded result sets | Paginate, stream, or cap the size |
| Many small remote calls | Chatty interface | Batch requests or add a bulk endpoint |
| Repeated expensive reads | No caching | Cache with an explicit time-to-live and invalidation rule, and protect against a stampede when an entry expires |
| Latency spikes under load | Connection pool exhaustion or lock contention | Reuse clients and pools, size them deliberately, shorten transactions |
| Slow responses on large payloads | Over-fetching | Return only needed fields, compress, paginate |

## Meet front-end performance targets

Google's Core Web Vitals thresholds use the 75th percentile, separately for mobile and desktop:

| Metric | Good threshold |
|---|---|
| Largest Contentful Paint (loading) | 2.5 seconds or less |
| Interaction to Next Paint (responsiveness) | 200 milliseconds or less |
| Cumulative Layout Shift (visual stability) | 0.1 or less |

Prefer real-user field measurements; add CI budgets (bundle size, Lighthouse score or lab metrics) for important pages.

## Test under load

1. Load test changes on paths with a stated target, using production-like data and traffic shape.
2. Push components until they break, and observe how they fail and how they recover. A system that recovers on its own after overload is worth more than one with a slightly higher limit.
3. Run a soak test (steady load for hours) before T3 releases to find leaks and slow degradation.
4. Test client behaviour against a dependency that never responds, to prove the timeouts and breakers work.

- [ ] Every new remote call has a timeout, and retries are bounded, jittered and limited to idempotent operations.
- [ ] Liveness checks do not depend on other services.
- [ ] Performance claims are backed by before-and-after measurements at stated percentiles.

## Failure modes

- Hanging dependencies accumulate untimed calls until the service stops responding.
- Retries at every layer turn a database blip into an outage.
- Retrying non-idempotent timed-out payments double-charges customers.
- Database-dependent liveness probes restart the fleet during failover.
- Intuition-led optimisations add stale caches without measurable benefit.

## Sources

- Marc Brooker, AWS Builders' Library, [Timeouts, retries, and backoff with jitter](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter), and AWS Architecture Blog, [Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/), cover timeout selection, single-layer retries, the 243 times example and full jitter.
- Google's SRE book, [Handling Overload](https://sre.google/sre-book/handling-overload/) and [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/), give the retry budgets, deadline propagation, load shedding and load-testing advice.
- Martin Fowler, [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html), describes the closed, open and half-open states.
- Jeffrey Dean and Luiz André Barroso, [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/), explain why tail latency dominates at scale.
- Kubernetes, [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/), defines the three probe types.
- Client defaults: [Requests timeouts](https://requests.readthedocs.io/en/latest/user/advanced/), [HTTPX timeouts](https://www.python-httpx.org/advanced/timeouts/), [.NET HttpClient.Timeout](https://learn.microsoft.com/en-us/dotnet/api/system.net.http.httpclient.timeout) and [AbortSignal.timeout()](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static).
- Google, [Web Vitals](https://web.dev/articles/vitals), defines the Core Web Vitals thresholds.
