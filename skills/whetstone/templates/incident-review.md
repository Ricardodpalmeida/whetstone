# Incident review: <short title>

<!-- Blameless: focus on contributing causes in systems and processes, assume everyone acted reasonably
     on the information they had, and never name individuals as causes. Write it within a few days,
     review it with the people involved, and track every action to completion. -->

| Field | Value |
|---|---|
| Date and duration | <YYYY-MM-DD, start to end in UTC, total duration> |
| Severity | <severity level and why> |
| Authors | <names or roles> |
| Status | draft, reviewed, actions complete |

## Summary

<Three or four sentences: what happened, who was affected, how it was resolved.>

## Impact

<Users or customers affected, duration, failed requests, data lost or exposed, financial or contractual impact, SLO budget consumed.>

## Timeline (UTC)

| Time | Event |
|---|---|
| HH:MM | <first trigger or change> |
| HH:MM | <detection: alert, customer report, engineer noticed> |
| HH:MM | <key decisions and actions> |
| HH:MM | <mitigated> |
| HH:MM | <resolved> |

## Detection and response

<How it was detected, time to detect, time to mitigate. Whether alerts, dashboards and runbooks helped or hindered.>

## Contributing causes

<The conditions that together allowed the incident, technical and organisational. Ask why repeatedly until reaching causes that can be changed. There is rarely a single root cause.>

## What went well, what went poorly, where we were lucky

| Went well | Went poorly | Lucky |
|---|---|---|
| | | |

## Actions

| Action | Type (prevent, detect, mitigate, process) | Owner | Due | Issue |
|---|---|---|---|---|
| | | | | |

## Lessons

<What should change in how we build, test, deploy or operate. Note any instruction file, runbook or test that was updated as a result.>
