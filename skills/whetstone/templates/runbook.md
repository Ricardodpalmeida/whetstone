# Runbook: <alert or procedure name>

<!-- One runbook per alert or operational task. Link it from the alert definition. Write each step so
     that an on-call engineer who has never seen the system can follow it at 3 a.m. Prefer safe,
     reversible actions first. Test the steps and record when. -->

| Field | Value |
|---|---|
| Service | <service name and owning team> |
| Alert or trigger | <alert name and the condition that fires it> |
| Severity | <page or ticket, and why> |
| Last tested | <YYYY-MM-DD, by whom> |

## What this means

<What users are probably experiencing, in one or two sentences. What the alert measures.>

## Check first

1. <Dashboard link, and what healthy and unhealthy look like.>
2. <Log or trace query to run, with the exact query text.>
3. <Recent changes to check: deploys, flags, configuration, dependency status pages.>

## Mitigate

| Situation | Action | Approval needed |
|---|---|---|
| A deploy in the last few hours correlates with the alert | Roll back to the previous version: <exact steps> | <none, or who> |
| A feature flag correlates with the alert | Turn off <flag>: <exact steps> | |
| Load is above capacity | <scale or shed steps> | |
| A dependency is down | <degraded mode, failover or customer messaging steps> | |

## Verify recovery

<Which metric or check shows the service has recovered, and how long to watch it.>

## Escalate

<Who to contact, how, and when: for example after 30 minutes without mitigation, or immediately if data loss is suspected.>

## Known causes

| Cause | How to recognise it | Fix |
|---|---|---|
| | | |

## After the incident

<When to open an incident review (see the incident review template), and where to record actions.>
