# Delivery and release

Read this when you change CI/CD, add a feature flag, deploy, plan a rollout or rollback, version a package or write a changelog.

## Contents

- [Rules for agents](#rules-for-agents)
- [Keep the main branch releasable](#keep-the-main-branch-releasable)
- [Separate deploying from releasing](#separate-deploying-from-releasing)
- [Roll out progressively](#roll-out-progressively)
- [Plan the rollback before the rollout](#plan-the-rollback-before-the-rollout)
- [Manage infrastructure as code](#manage-infrastructure-as-code)
- [Version and document releases](#version-and-document-releases)
- [Measure delivery performance](#measure-delivery-performance)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Rules for agents

1. Never deploy to production, publish a package, push a release tag, or change production configuration or feature flags without explicit approval for that specific action.
2. Never skip, disable or weaken CI checks, branch protection or required reviews to get a change through.
3. Prefer the reversible path: a flag you can turn off, a deploy you can roll back, a migration that keeps the old schema working.

## Keep the main branch releasable

Apply it:

1. Run the same checks on every change: build, formatting, linting, type checks, tests, dependency and secret scans. The pipeline definition lives in the repository and is reviewed like code.
2. Keep the pipeline fast enough that people wait for it rather than work around it. Parallelise, cache dependencies and move slow suites to a later stage instead of deleting them.
3. Treat a broken main branch as the team's top priority: revert first, then fix.
4. Build each artefact once, give it an immutable version, and promote the same artefact through every environment. Supply environment differences through configuration at release time, as the Twelve-Factor App's build, release and run separation describes.

## Separate deploying from releasing

Deploying puts code on servers; releasing exposes behaviour to users. Feature flags let you do the first often and the second deliberately. Pete Hodgson's article on feature toggles distinguishes four kinds:

| Kind | Purpose | Expected lifetime |
|---|---|---|
| Release | Hide unfinished or unlaunched work | Days to weeks, then removed |
| Experiment | A/B tests | Long enough for a significant result |
| Ops | Kill switches and load controls for incidents | Mostly short; a few permanent kill switches |
| Permission | Features for specific users or plans | Long-lived; often belongs in the product's authorisation model |

Apply it:

1. Give every flag an owner, a description, a default that is safe if the flag service is down, and, for release flags, a removal date with a tracked removal task.
2. Test both states of a flag while it exists.
3. Remove release flags and their dead branches promptly after launch. Flags are inventory with a carrying cost; some teams cap the number of live flags or fail a test when one passes its expiry date.
4. Prefer the existing flag system in the codebase. If you need a vendor-neutral interface, OpenFeature provides one.

## Roll out progressively

Google's SRE workbook describes canarying: expose a small part of production traffic to the new version and compare it with the old.

Apply it:

1. Start with a small share of traffic or a small set of instances, then widen in stages.
2. Compare the canary population with a control population, not with the whole service. A 20 percent error rate on a 5 percent canary looks like a 1 percent blip in aggregate metrics.
3. Judge the canary on a few user-facing indicators (error rate, latency) rather than noisy resource metrics, using metric windows no longer than the canary stage.
4. Run one canary at a time, and automate the decision to pause or roll back when the canary is worse than the control.
5. Where canarying is not possible, use blue-green deployment, or release to internal users first.

## Plan the rollback before the rollout

Apply it:

1. Write the rollback steps in the PR or runbook before deploying, and make sure the previous artefact is still available.
2. Keep every database migration compatible with the previous application version, so rolling back the code does not require rolling back the schema (see [data-and-privacy.md](data-and-privacy.md)).
3. When a deploy correlates with an incident, roll back or turn off the flag first, and investigate afterwards (see [debugging.md](debugging.md)).
4. Choose a forward fix only when rollback is impossible or more dangerous, and say so explicitly.
5. Practise rollbacks. A rollback path that has never run is a guess.

## Manage infrastructure as code

Apply it:

1. Define infrastructure, permissions and configuration in code in the repository, reviewed and applied through the pipeline. Avoid manual changes in production consoles; if one is unavoidable during an incident, record it and bring the code back in line.
2. Review the planned changes (a plan or what-if output) before applying them, and read every delete or replace operation.
3. Detect drift between the code and the real environment on a schedule.
4. Give the deployment identity only the permissions it needs, and separate it from human administrator access.

## Version and document releases

Apply it:

1. Version packages and public APIs with Semantic Versioning 2.0.0: increment MAJOR for incompatible API changes, MINOR for backward-compatible features, PATCH for backward-compatible fixes. Version 0.y.z means anything may change. Never modify a released version; publish a new one.
2. Announce a deprecation in a MINOR release before removing the feature in a MAJOR release, as the SemVer FAQ recommends.
3. Keep a human-written changelog in the Keep a Changelog 1.1.0 style: an `Unreleased` section at the top, entries grouped under Added, Changed, Deprecated, Removed, Fixed and Security, newest version first, dates in ISO 8601 format. Do not paste the commit log; it is full of noise.
4. Write release notes for the people affected: what changed for them, what they must do, and when.
5. Tag releases in version control so every deployed version maps to a commit.

Check (for T2 and T3 releases):

- [ ] The artefact passed CI and is the one that was tested.
- [ ] Rollback steps are written and the previous version is available.
- [ ] Migrations are backward compatible, and destructive steps are deferred.
- [ ] Dashboards and alerts for the change exist, and someone is watching the rollout.
- [ ] Flags have owners and removal dates; the changelog and release notes are updated.

## Measure delivery performance

DORA's research tracks five software delivery metrics, in two groups:

| Group | Metric | Meaning |
|---|---|---|
| Throughput | Change lead time | Time from commit to running in production |
| Throughput | Deployment frequency | How often you deploy |
| Throughput | Failed deployment recovery time | Time to recover from a deployment that needs immediate intervention |
| Instability | Change fail rate | Share of deployments that need immediate intervention |
| Instability | Deployment rework rate | Share of deployments that are unplanned and caused by a production incident |

Use them to improve the system of work, not to rank individuals or teams.

## Failure modes

- A release flag lives for two years, nobody remembers what its "off" state does, and turning it off during an incident breaks checkout.
- The artefact deployed to production is rebuilt from source and differs from the one that passed tests.
- A deploy includes a migration that drops a column, and rolling back the code no longer works.
- A canary is judged on aggregate metrics, looks healthy, and the defect reaches every user.
- An agent "helpfully" publishes a package version to fix a typo, and the version can never be reused.

## Sources

- Pete Hodgson, [Feature Toggles (aka Feature Flags)](https://martinfowler.com/articles/feature-toggles.html), defines the toggle categories and the practice of treating toggles as inventory.
- [OpenFeature](https://openfeature.dev/) is a vendor-neutral feature flag standard incubating at the CNCF.
- Google's SRE workbook, [Canarying Releases](https://sre.google/workbook/canarying-releases/), covers canary populations, metrics and durations.
- [Semantic Versioning 2.0.0](https://semver.org/) and [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) define the versioning and changelog conventions.
- DORA, [Software delivery performance metrics](https://dora.dev/guides/dora-metrics/), defines the five metrics.
- [The Twelve-Factor App](https://12factor.net/) separates the build, release and run stages.
