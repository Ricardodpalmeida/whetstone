# Debugging

Use for failing tests, bug reports, crashes, production incidents and unexplained behaviour.

## Contents

- [Ground rules](#ground-rules)
- [Reproduce the failure](#reproduce-the-failure)
- [Gather evidence](#gather-evidence)
- [Form and test hypotheses](#form-and-test-hypotheses)
- [Find the change that introduced it](#find-the-change-that-introduced-it)
- [Fix the cause and guard it](#fix-the-cause-and-guard-it)
- [Production incidents](#production-incidents)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Ground rules

1. State the cause, with evidence, before you change code. A change made without a known cause is a guess, and a guess that seems to work hides the real defect. The one exception is mitigation in production, covered below, which you label as mitigation rather than as a fix.
2. Change one variable at a time, and revert experiments that did not help before you try the next one.
3. Keep a short investigation log of hypothesis, test and result. It stops you from repeating experiments and becomes the explanation in the PR.
4. Never make a failing test pass by weakening it, skipping it, widening a tolerance or adding retries. If the test itself is wrong, show the evidence, get the user's agreement, and fix the test in its own commit.

## Reproduce the failure

Without reproduction, you cannot prove a fix.

1. Collect the exact input, version, environment, configuration and steps. Ask for them only if you cannot get them from logs, tickets or the running system.
2. Capture the failure as an automated test at the lowest level that still fails: a unit test if the logic is local, an integration test if it needs a real dependency.
3. Shrink the reproduction until every remaining part is needed. Smaller inputs give clearer causes.
4. For intermittent failures, run the test in a loop (for example 100 times) and record the failure rate. Vary ordering, seeds, parallelism, time zone, locale and load. Shared state, time, randomness, ordering assumptions, network calls and resource leaks cause most flakiness.
5. If you still cannot reproduce it, add targeted instrumentation and gather more evidence. Do not ship a speculative fix in place of a reproduction.

- [ ] A test or scripted procedure fails reliably, or the failure rate is measured.
- [ ] You can explain why the reproduction exercises the reported symptom.

## Gather evidence

1. Read the whole error, including every "caused by" entry in the chain. The first error in a log is usually more informative than the last one.
2. Pull logs, traces and metrics for the failing request, using its correlation or trace identifier.
3. Inspect the configuration and versions actually in effect, not the ones you believe are deployed. Report secrets by presence, length or fingerprint, never by value.
4. List what changed recently: deploys, configuration, feature flags, dependency versions, data shape, traffic, certificates, quotas and clocks.
5. Compare a working case with a failing case and list every difference you can find.

## Form and test hypotheses

Google SRE's troubleshooting method: propose causes and test them against the system until the root cause is identified.

1. Write down candidate causes. Rank them by likelihood and by how cheaply you can test them.
2. For each experiment, write the expected result before you run it. Prefer experiments that can rule a hypothesis out over experiments that can only fit it.
3. Treat "it started after the last deploy" as the leading suspect, then confirm it with evidence. Correlation in time is not causation.
4. Use a debugger, a REPL or temporary logging to observe state directly instead of reasoning about what the state should be.
5. Stop and re-plan after three failed hypotheses. Widen the evidence before you narrow the guesses.

Frequent culprits worth checking early:

| Symptom | Usual suspects |
|---|---|
| Fails only in one environment | Configuration drift, missing secret, different dependency version, file system case sensitivity, permissions |
| Fails at certain times | Time zones, daylight saving changes, month or year boundaries, scheduled jobs, certificate or token expiry |
| Wrong values | Off-by-one, integer overflow, floating point comparison, unit mismatch, character encoding |
| Intermittent | Race conditions, shared mutable state, test ordering, unawaited async work, retries hiding errors |
| Slow or stuck | Missing timeout, exhausted connection pool, lock contention, N+1 queries, unbounded queue |
| Works after a restart | Memory or handle leak, stale cache, poisoned connection, state that accumulates |

## Find the change that introduced it

With a known good version, use `git bisect` to find the first bad commit.

1. Write a script that exits 0 when the code is good, 1 when it is bad, and 125 when the commit cannot be tested (for example, it does not build).
2. Run it with `git bisect run`. Exit codes 1 to 127, except 125, mark a commit bad; any other code aborts the bisect.
3. End with `git bisect reset` so the working tree is back where it started.

```sh
git bisect start HEAD v2.3.0 --
git bisect run ./scripts/repro.sh
git bisect reset
```

Also bisect dependency versions (compare lockfiles), configuration changes and migrations.

## Fix the cause and guard it

1. Confirm the reproduction test fails for the reason you identified, not for an incidental one.
2. Fix the root cause. Ask "why" until you reach a cause you can change. A null check or a broad exception handler that hides the error is a symptom fix.
3. Run the reproduction and the surrounding test suites. All must pass.
4. Search the codebase for the same pattern and fix the other instances, or list them as follow-ups.
5. Ask why existing tests missed the defect, and add the missing kind of test, not only the single case.
6. Remove temporary instrumentation, or turn it into proper telemetry as described in [observability.md](observability.md).
7. Write the explanation in the PR: symptom, root cause, evidence, fix, regression test and follow-ups.

- [ ] The regression test failed before the fix and passes after it.
- [ ] The root cause is named in the PR, with the evidence that supports it.
- [ ] No debug output, commented-out code or skipped tests remain.

## Production incidents

Restore affected users' service before investigating root cause. Google SRE: "Stopping the bleeding should be your first priority."

1. Mitigate with the fastest reversible action available: roll back the last deploy, turn off a feature flag, shift traffic, or add capacity. Mitigation comes before diagnosis.
2. Ask before you take any action in production unless a runbook pre-authorises it. Never run destructive or data-changing commands in production on your own initiative.
3. Preserve evidence before it disappears: logs, the bad build artefact, a heap dump or a snapshot of the affected records.
4. Communicate impact, current status and the time of the next update to whoever owns the incident.
5. After recovery, run a blameless review with [the incident review template](../templates/incident-review.md) when any common trigger applies: user-visible downtime or degradation beyond a threshold, data loss of any kind, an on-call intervention such as a rollback or traffic reroute, a resolution time above a threshold, or a monitoring failure that meant humans found the problem first.
6. Track every action item to an owner and a date. A review without completed actions changes nothing.

## Failure modes

- Simultaneous changes hide which fixed the symptom and what else broke.
- Broad catches, defaults or retries hide errors that later corrupt data.
- Rerunning flaky tests to green ships the underlying race.
- Declaring a fix without reproduction leaves it unproven.
- Leftover debug logging exposes tokens or personal data.
- Investigating root cause during an outage instead of rolling back first.

## Sources

- Google's SRE book, [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/), describes triage first and the hypothetico-deductive method; the quotation above comes from its Triage section.
- The Git manual, [git-bisect](https://git-scm.com/docs/git-bisect), defines the exit codes that `git bisect run` interprets.
- Google's SRE book, [Postmortem Culture](https://sre.google/sre-book/postmortem-culture/), lists the review triggers used above and defines blamelessness.
- Claude Code's [best practices](https://code.claude.com/docs/en/best-practices) ask agents to write a failing test that reproduces an issue, address root causes rather than suppressing errors, and show evidence instead of asserting success.
