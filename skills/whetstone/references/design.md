# Design

Use before T2/T3 work, technology/architecture choices, or changes crossing module, service or team boundaries.

## Contents

- [Match the design effort to the change](#match-the-design-effort-to-the-change)
- [Frame the problem](#frame-the-problem)
- [Compare real options](#compare-real-options)
- [Prefer boring and reversible choices](#prefer-boring-and-reversible-choices)
- [Shape the code for change](#shape-the-code-for-change)
- [Change existing systems incrementally](#change-existing-systems-incrementally)
- [Design for operations](#design-for-operations)
- [Record decisions and draw useful diagrams](#record-decisions-and-draw-useful-diagrams)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Match the design effort to the change

| Tier | Design output |
|---|---|
| T0 | None. |
| T1 | One or two sentences in the PR on the approach taken. |
| T2 | An "Approach" section in the PR. Write a [design one-pager](../templates/design-one-pager.md) when the change adds a component, a dependency, a data model or a public contract. |
| T3 | A design one-pager reviewed before implementation starts, a [threat model](threat-modeling.md), and a [decision record](../templates/decision-record.md) for each decision that is expensive to reverse. |

Design before code. Disclose existing spike code and review the design independently of it.

## Frame the problem

1. State the problem in terms of users or operators, with current numbers where they exist (for example, "p95 page load is 4.1 s; the target is 1.5 s").
2. List goals and non-goals. Non-goals prevent scope creep and settle debates early.
3. List the constraints: deadlines, budget, compliance, existing contracts, team skills, supported platforms.
4. Pick the three quality attributes that matter most for this change (for example latency, cost and auditability). You cannot maximise all of them, and naming the top three makes trade-offs explicit.

## Compare real options

1. Describe at least two viable options plus the smallest possible change. "Do less" is often the winner.
2. Compare them in a table against the drivers from the framing step, adding cost of reversal, operational burden, security impact and migration path.
3. When one unknown dominates the decision (a library's behaviour, a performance limit), resolve it with a time-boxed spike before choosing. Throw the spike code away or re-tier it before reuse.
4. State the decision, the reason, and what evidence would make you revisit it.

Example comparison:

| Driver | Postgres full-text search | Dedicated search service |
|---|---|---|
| Meets relevance needs for 200k documents | Likely; verify with a spike | Yes |
| New infrastructure to run | None | Cluster, upgrades, backups |
| Data consistency | Transactional with the source rows | Eventually consistent; needs a sync pipeline |
| Cost to reverse | Low | High once clients depend on its query syntax |

## Prefer boring and reversible choices

New technology costs operations throughout its lifetime. Dan McKinley's "Choose Boring Technology" treats innovation as a small budget reserved for necessary novelty.

1. Solve the problem with the stack you already run unless there is evidence it cannot work. Adding a language, framework, datastore or managed service is an escalation trigger for T3.
2. Classify each decision by its cost of reversal. Make cheap-to-reverse decisions quickly and locally. Slow down, write a decision record and get review for the expensive ones: data models, public contracts, vendor lock-in, security architecture.
3. Build for the requirements you know today. Keep code easy to change instead of adding extension points for futures nobody has asked for; Martin Fowler's "Yagni" explains why presumptive features cost more than they save.
4. Wait for the third real instance before you extract a shared abstraction. Two similar pieces of code are cheaper to keep than a wrong abstraction is to unwind.

## Shape the code for change

1. Give each module one reason to change and hide the decisions most likely to change (a vendor, a storage format, a pricing rule) behind its interface.
2. Point dependencies toward stable business logic. Keep I/O (databases, HTTP, files, clocks, randomness) at the edges so the core logic is deterministic and easy to test.
3. Design interfaces from the caller's side: few operations, explicit inputs and outputs, and errors that are part of the contract.
4. Make invalid states unrepresentable with types, enumerations and constructors, so whole classes of checks disappear from the rest of the code.
5. Split a service only when the parts must deploy, scale or be owned independently. Services that must always be deployed together are a distributed monolith with network failures added.

## Change existing systems incrementally

Big-bang rewrites concentrate risk and delay feedback. Keep systems releasable at every step.

| Situation | Pattern |
|---|---|
| Replace a legacy system or a large subsystem | Strangler fig: build the new parts alongside the old one, route traffic to them piece by piece, and retire the old parts as they empty. |
| Replace an internal component used in many places | Branch by abstraction: introduce an abstraction, move callers to it, swap the implementation behind it, then remove the old one. |
| Change an interface, schema or message format with live consumers | Parallel change (expand, migrate, contract): add the new form alongside the old, migrate consumers, then remove the old form. Details live in [api-design.md](api-design.md) and [data-and-privacy.md](data-and-privacy.md). |
| Ship incomplete work safely | Feature flags, as described in [delivery-and-release.md](delivery-and-release.md). |

## Design for operations

Design deployment, observation, scaling, rollback and eventual removal. The Twelve-Factor App provides a service baseline.

1. Keep configuration that varies between environments out of the code and supply it through the environment or a configuration service. Secrets never live in the repository.
2. Treat databases, queues and other backing services as attached resources that you can replace through configuration.
3. Keep processes stateless and disposable: fast start-up, graceful shutdown on termination signals, and no reliance on local disk between requests.
4. Keep development, staging and production as similar as possible, so that "works in staging" means something.
5. Write logs as an event stream to standard output and let the platform route them.
6. For each dependency, decide what happens when it is slow or down (see [reliability-performance.md](reliability-performance.md)), and what you will measure to know (see [observability.md](observability.md)).
7. Estimate the running cost at expected and at ten times the expected load.

## Record decisions and draw useful diagrams

1. Write a decision record when a decision is expensive to reverse, affects other teams, or will make a future reader ask "why is it like this?". Use [the decision record template](../templates/decision-record.md), number records sequentially, keep them in the repository, and mark a reversed decision as superseded instead of deleting it.
2. Draw diagrams at the level the audience needs. The C4 model's system context and container diagrams answer most design questions; component diagrams help inside a complex service; code-level diagrams rarely repay their upkeep.
3. Keep diagrams as text (for example Mermaid or PlantUML) next to the code, give each a title and a key, and update them in the same change that alters the architecture.

- [ ] Every T3 decision that is expensive to reverse has a decision record with context, decision, status and consequences.
- [ ] The design names the rollout plan, the rollback plan and the signals that show it works.

## Failure modes

- Interesting technology brings failure modes the team cannot handle.
- Considering one option records a conclusion, not a decision.
- Speculative extension points and configuration obstruct later changes.
- Unshipped rewrites run for months while the old system keeps changing.
- Ignoring operations leaves new components unobservable and without rollback at the first incident.

## Sources

- Dan McKinley, [Choose Boring Technology](https://boringtechnology.club/), introduces innovation tokens and the long-term cost of new technology.
- Martin Fowler, [Yagni](https://martinfowler.com/bliki/Yagni.html), explains the cost of presumptive features.
- Michael Nygard, [Documenting Architecture Decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions), defines the short decision record with context, decision, status and consequences.
- [MADR](https://adr.github.io/madr/) is a widely used decision record format that adds decision drivers and considered options.
- Simon Brown, [The C4 model](https://c4model.com/), defines the context, container, component and code diagram levels.
- Martin Fowler, [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html) and [Branch By Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html), and Danilo Sato, [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html), describe the incremental change patterns.
- [The Twelve-Factor App](https://12factor.net/) sets out the operational baseline for services used above.
