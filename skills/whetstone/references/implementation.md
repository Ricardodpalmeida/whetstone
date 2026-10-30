# Implementation

Use when writing or changing code above T0.

## Contents

- [Read before you write](#read-before-you-write)
- [Work in small verified steps](#work-in-small-verified-steps)
- [Write for the next reader](#write-for-the-next-reader)
- [Handle errors deliberately](#handle-errors-deliberately)
- [Parse input at the boundary](#parse-input-at-the-boundary)
- [Control state, time and concurrency](#control-state-time-and-concurrency)
- [Treat configuration as an input](#treat-configuration-as-an-input)
- [Refactor safely](#refactor-safely)
- [Rules for agent-written code](#rules-for-agent-written-code)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Read before you write

1. Read the repository's instruction files (for example `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`) and follow them. They override generic advice, including this skill's, except where they would break a non-negotiable rule.
2. Read the code you will change, its callers and its tests. Find the closest existing example of what you are about to build and follow its patterns.
3. Before you call a library function, confirm it exists with that signature in the version pinned by the lockfile. Read the installed source or the documentation for that version. Plausible but non-existent APIs are a common failure of generated code.
4. Run the existing tests before you change anything, so you know which failures were already there.

## Work in small verified steps

1. Make one logical change at a time, run the relevant checks, and keep the code building after each step.
2. Prefer several small commits that each leave the build green over one large commit at the end.
3. When a step fails, fix it or revert it before starting the next one. Do not stack new changes on a broken state.

## Write for the next reader

Code is mostly read. Google's review guide tests whether readers can understand it quickly and developers change it safely.

1. Choose names that reveal intent and units: `timeout_ms`, `price_cents`, `is_active`, `fetch_overdue_invoices`. Avoid abbreviations unless they are standard in the domain.
2. Keep functions focused on one job. Replace a boolean parameter that switches behaviour with two functions. Return early to avoid deep nesting.
3. Write comments that explain why: the constraint, the trade-off, the link to the bug. Do not narrate what the next line does. Document public interfaces.
4. Match the surrounding code's style and structure even where you would choose differently. Let the repository's formatter and linter settle style, and do not reformat code you did not otherwise change.
5. Delete dead code, unused parameters and commented-out blocks. Version control remembers them. Leave a TODO only with a link to a tracked issue.

Bad:

```python
def proc(d, f=False):
    # loop over items
    for i in d:
        ...
```

Good:

```python
def archive_expired_sessions(sessions: list[Session], now: datetime) -> int:
    """Archive sessions past their expiry; returns the number archived.

    Archiving instead of deleting keeps the audit trail required for
    login investigations (see issue 1423).
    """
```

## Handle errors deliberately

OWASP Top 10:2025 added "Mishandling of Exceptional Conditions": swallowed errors, fail-open behaviour and leaked details threaten security and reliability.

1. Decide for each failure whether it is expected (not found, invalid input, conflict, dependency unavailable) or a programming error. Model expected failures in the interface; let programming errors fail fast and loudly.
2. Never swallow an error. Catch the narrowest type you can handle, and when you re-raise, add context and keep the original cause attached.
3. Fail closed. When an authorisation check, signature verification or policy lookup errors out, deny the request.
4. Release resources deterministically with the language's scoped constructs (`with`, `using`, `try`/`finally`, `defer`).
5. Show users a short, safe message with a correlation identifier. Keep stack traces and internal details in logs, never in responses.

Bad:

```python
try:
    allowed = policy.check(user, document)
except Exception:
    allowed = True  # do not block users if the policy service is down
```

Good:

```python
try:
    allowed = policy.check(user, document)
except PolicyUnavailable as exc:
    log.warning("policy check unavailable; denying", exc_info=exc)
    allowed = False
```

## Parse input at the boundary

Alexis King's "Parse, don't validate": convert untrusted input into precise boundary types; core code can trust their guarantees without rechecking.

1. Parse requests, messages, files, environment variables and command-line arguments into typed objects at the boundary. Reject invalid input there with a clear error.
2. Inside the core, accept only the parsed types. A function that takes `EmailAddress` cannot receive an unchecked string.
3. Represent money as integer minor units or a decimal type, never as binary floating point.
4. Store and compute times in UTC with time-zone-aware types, serialise them as RFC 3339 timestamps, and convert to local time only for display.
5. Use UTF-8 for all text at boundaries, and state units in names or types wherever a number has one.

## Control state, time and concurrency

1. Prefer immutable values and functions without side effects. Push side effects (I/O, clocks, randomness) to the edges.
2. Inject the clock, random number source and identifier generator, so tests can control them.
3. In asynchronous code, never block the event loop with synchronous I/O or heavy computation, await or supervise every task you start, and let cancellation propagate.
4. Replace check-then-act sequences on shared data with atomic operations: database constraints (unique, foreign key, check), conditional updates, or optimistic concurrency with a version column.
5. Make message and job handlers idempotent, because queues and retries deliver some messages more than once.

## Treat configuration as an input

1. Read configuration from the environment or a configuration service, as the Twelve-Factor App recommends, and keep secrets out of the repository (see [security.md](security.md)).
2. Validate all configuration at start-up and refuse to start with a clear message when it is invalid, rather than failing on the first request.
3. Make defaults safe: debug off, verbose errors off, TLS verification on, the most restrictive permissions.
4. Hide incomplete features behind flags as described in [delivery-and-release.md](delivery-and-release.md), and remove each flag once it has served its purpose.

## Refactor safely

Kent Beck, quoted by Martin Fowler: "make the change easy, then make the easy change".

1. Refactor in commits separate from behaviour changes, so each can be reviewed and reverted on its own.
2. Have tests that cover the behaviour before you refactor. If they are missing, add characterisation tests that pin down the current behaviour first.
3. Keep refactoring commits behaviour-preserving. If a test has to change, the commit is not a pure refactor.
4. Tidy only the code you are already touching. Record wider cleanups as follow-ups.
5. Treat anything externally observable as a contract, even if it was never documented (see [api-design.md](api-design.md)).

## Rules for agent-written code

1. Never present a stub, placeholder or "not implemented" path as finished work. If something is incomplete, say so in the report.
2. Never make a test pass by mocking out the code under test, hard-coding the expected value or special-casing the test environment.
3. Never disable a linter rule, type check or compiler warning to get a clean run. If a suppression is truly justified, scope it to one line and give the reason in a comment.
4. Keep the diff minimal and on task. Unrequested renames, reformatting and dependency changes belong in separate changes.

- [ ] The code builds, lints and type-checks with no new unexplained suppressions.
- [ ] No swallowed errors, commented-out code or leftover debug output remain.
- [ ] Every new external call has a timeout and a handled failure path.
- [ ] The diff contains only changes that serve the stated goal.

## Failure modes

- Generated calls to methods absent from pinned libraries fail at runtime.
- "Temporarily" ignored errors silently lose data.
- Authorisation allows access when its dependency times out.
- Floating-point money calculations leave invoices a cent off.
- Mixing refactors and behaviour changes prevents independent review or rollback.

## Sources

- Google's engineering practices, [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html), cover complexity, naming, comments that explain why, and consistency with surrounding code.
- OWASP, [Top 10:2025](https://owasp.org/Top10/2025/), introduced the category A10:2025 Mishandling of Exceptional Conditions.
- Alexis King, [Parse, don't validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/), explains parsing untrusted input into precise types.
- Martin Fowler, [An example of preparatory refactoring](https://martinfowler.com/articles/preparatory-refactoring-example.html), is the source of the Kent Beck quotation.
- [The Twelve-Factor App](https://12factor.net/) recommends storing configuration in the environment.
