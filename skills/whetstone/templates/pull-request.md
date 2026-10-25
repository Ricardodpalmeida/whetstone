<!-- One-line summary as the PR title, in the imperative: "Add retry budget to payment client". -->

## Why

<The problem or goal in one or two sentences. Link the issue.>

## What changed

<The approach at a high level, and alternatives rejected where they were not obvious. Call out any change to instruction files such as CLAUDE.md or AGENTS.md.>

## Tier and risk

<T0 to T3, the escalation triggers that apply, and the main risk in one sentence.>

## How it was verified

```text
<commands run and their results, for example: pytest -q  ->  212 passed>
```

<Screenshots for UI changes, measurements for performance claims, manual checks performed.>

Not verified: <anything you could not test, and why>.

## Rollout and rollback

<Flags, migrations, deployment order, how to roll back and until when rollback is possible.>

## Security, privacy and accessibility

<Trust boundaries, data handled, threat model link, accessibility checks. Write "None affected" only when true.>

## Assumptions and follow-ups

1. <Assumption, and how it could be checked.>
2. <Follow-up work, with issue links.>

## Checklist

- [ ] Self-reviewed the full diff; no unrelated changes, debug output or secrets.
- [ ] Tests added or updated; none skipped, deleted or weakened without a stated reason.
- [ ] Documentation, changelog and contract files updated where behaviour changed.
- [ ] Observability added for new paths (logs, metrics, traces, alerts as needed).
