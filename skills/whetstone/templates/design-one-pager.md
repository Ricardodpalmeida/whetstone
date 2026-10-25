# Design: <feature or change name>

<!-- Keep this to one or two pages. Write it before implementation for T3 work and for T2 work that adds
     a component, dependency, data model or public contract. Delete sections that truly do not apply,
     and say why in one line rather than leaving them empty. -->

| Field | Value |
|---|---|
| Author | <name or agent, plus the human owner> |
| Reviewers | <names or roles> |
| Status | draft, in review, approved, superseded |
| Tier | T2 or T3 |
| Date | YYYY-MM-DD |
| Links | <issue, decision records, threat model> |

## Problem

<Who is affected, what is wrong or missing, and current numbers if any. One paragraph.>

## Goals and non-goals

| Goals (measurable) | Non-goals |
|---|---|
| <for example "Export up to 50,000 rows in under 10 s at p95"> | <for example "Scheduled exports"> |

## Constraints and quality priorities

<Deadlines, budget, compliance, compatibility, supported platforms. Name the top three quality attributes, in priority order.>

## Proposal

<How it works: components, data flow, interfaces, data model changes. Include a context or container diagram as text (Mermaid or PlantUML).>

## Alternatives considered

| Option | Why not chosen |
|---|---|
| <option> | <reason tied to goals or constraints> |
| Smallest possible change | <reason> |

## Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| | | | |

## Security and privacy

<Trust boundaries crossed, data classification, authentication and authorisation, link to the threat model. Personal data: purpose, retention, location.>

## Reliability, performance and observability

<Behaviour when each dependency is slow or down, timeouts and retries, SLOs affected, load expectations, the signals and alerts that show it works.>

## Accessibility

<For UI changes: patterns used, WCAG 2.2 AA considerations, how it will be tested.>

## Rollout and rollback

<Flags, migration sequence (expand and contract), canary or staged rollout, rollback steps and how long rollback stays possible.>

## Verification

<Acceptance criteria and how each is verified: automated tests, manual checks, metrics.>

## Cost

<Expected running cost at today's load and at ten times today's load.>

## Open questions

1. <Question, owner, date needed.>

## Decision

<Approved by whom and when, with conditions. Link resulting decision records.>
