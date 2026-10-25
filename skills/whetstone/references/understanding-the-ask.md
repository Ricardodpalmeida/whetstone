# Understanding the ask

Read this before building anything above tier T0, when a request is vague, large or contradictory, or when someone asks you to stress-test a plan.

## Contents

- [Restate the goal](#restate-the-goal)
- [Decide whether to ask or proceed](#decide-whether-to-ask-or-proceed)
- [Ask questions that earn their cost](#ask-questions-that-earn-their-cost)
- [Interrogate a plan before building](#interrogate-a-plan-before-building)
- [Write acceptance criteria](#write-acceptance-criteria)
- [Control scope](#control-scope)
- [Keep an assumptions log](#keep-an-assumptions-log)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Restate the goal

Write one sentence that names who benefits, what changes for them and how anyone will know it worked. If you cannot write it, you do not understand the ask yet.

Apply it:

1. Classify the ask: bug fix, feature, refactor, investigation, review, migration or spike. Each has a different output. An investigation ends in findings, not code; a spike ends in a decision and is thrown away.
2. Look for the problem behind a solution-shaped request. "Add a cache" usually means "this page is slow". Confirm the underlying problem before you build the named solution.
3. If you see a materially better route to the same goal, propose it before building. Never silently swap the requested solution for your own.

Check:

- [ ] The one-sentence goal is written in the plan, PR or chat.
- [ ] The type of ask is clear, and so is what "done" produces.

## Decide whether to ask or proceed

Ask only when the answer changes what you build, you cannot discover it yourself, and a wrong guess is costly to undo. Otherwise proceed and state the assumption.

| Situation | Do |
|---|---|
| The fact is discoverable from code, config, docs, history or by running the system | Look it up. Do not ask. |
| A preference with a clear precedent in the codebase | Follow the precedent and say so. |
| A choice that changes user-visible behaviour, a contract, stored data, cost or security posture | Ask before building. |
| An irreversible or externally visible action | Ask and wait for an explicit yes. |
| Ambiguity in a T0 or T1 task whose outcome is cheap to change | Proceed, state the assumption, offer the alternative. |
| Nobody is available to answer (unattended run) | Take the most reversible option, record the assumption prominently, and take no irreversible step. |

## Ask questions that earn their cost

A good question can be answered in seconds and visibly changes the work.

Apply it:

1. Batch questions into one message and number them.
2. Order them by dependency: ask first the questions whose answers decide which other questions matter.
3. Give a recommended default with each question, phrased so that "yes" accepts it.
4. Prefer closed or multiple-choice questions, and state the consequence of each option.
5. Discover facts yourself before asking; spend the human's attention only on decisions.

Bad:

```text
What should the CSV export look like? Any requirements?
```

Good:

```text
1. Scope: export all rows matching the current filters (recommended), or only the visible page?
2. Size: cap at 50,000 rows and email a download link above that (recommended), or stream any size?
3. Access: anyone who can view the report may export it (recommended)?
4. Columns: the same columns as the on-screen table, in the same order (recommended)?
```

## Interrogate a plan before building

Use this when asked to review or "grill" a plan, and before any T3 work. The goal is that nothing important is silently assumed.

Apply it:

1. List every decision the plan makes or implies, including implicit ones: data ownership, failure behaviour, who operates it, how it is removed later.
2. Arrange the decisions by dependency. Settle goal, users and constraints before schema, libraries and naming.
3. For each decision ask: what are the alternatives, what evidence supports this one, what would prove it wrong, and what does reversing it cost?
4. Probe the usual weak spots: partial failure and retries; load at 10 times and at zero; abuse and security; the data lifecycle (create, change, export, delete); operations (deploy, observe, roll back, support); migration from the current state; cost; accessibility; privacy and legal exposure.
5. Work in rounds. Ask the questions that are answerable now, each with a recommended answer, wait for replies, then recompute which questions are unlocked.
6. Stop when every decision is decided by the owner, backed by evidence, or recorded as an assumption with someone responsible for checking it.

Output a decision list with three groups (decided, assumed, open). It feeds the acceptance criteria and the design one-pager.

## Write acceptance criteria

Each criterion is an observable, testable statement, and each one maps to a verification: an automated test, a manual check or a metric.

Apply it:

1. Write criteria as Given/When/Then statements or as a checklist.
2. Include negative paths: unauthorised caller, invalid input, empty state, dependency failure, concurrent edits.
3. Add non-functional criteria when they matter: a latency budget (p95), WCAG 2.2 AA for UI, authorisation rules, data retention, cost per request.
4. Note how each criterion will be verified.

Example:

```text
Given a signed-in user who can view report 42
When they request GET /reports/42/export
Then they receive a CSV with the columns shown in the UI, in the same order
And cells starting with =, +, -, @, tab or carriage return are neutralised
Given a user who cannot view report 42
When they request the same export
Then they receive 403 and no report data
Verification: API tests for both cases; manual check that the file opens cleanly in a spreadsheet application
```

Check:

- [ ] Every criterion can fail. "Works well" and "is fast" cannot fail, so replace them with measurable statements.
- [ ] At least one negative path is covered for T2 and above.

## Control scope

One change has one purpose. Scope creep is the most common way a small task becomes a risky one.

Apply it:

1. Write non-goals next to the goal.
2. Keep refactors, formatting, renames and dependency bumps out of a behaviour change. Do them in their own change, or list them as follow-ups.
3. Record adjacent problems you notice as follow-ups. Fix one only when it blocks the task or the user agrees.
4. Re-tier and tell the user when the task grows: when your estimate doubles, or when a new escalation trigger appears.
5. Time-box spikes and prototypes, label them throwaway, and re-tier before any of that code moves to a production path.

## Keep an assumptions log

For every assumption record the statement, why it is reasonable, how to verify it, and the impact if it is wrong. Put the log in the PR description or the final report so a reviewer can challenge it. An assumption that would be expensive if wrong is a question, not an assumption: ask it.

## Failure modes

- The agent builds exactly what was literally asked, and it does not solve the actual problem.
- The agent asks questions the repository could have answered, which wastes the human's attention and erodes trust.
- The agent sends fifteen open-ended questions at once with no defaults, so nobody answers them.
- An assumption is made silently and surfaces only in production.
- Features or configuration options nobody asked for are added "for flexibility".
- "While I'm here" edits mix unrelated changes into the diff and make review and rollback harder.

## Sources

- Matt Pocock's [grill-me skill](https://github.com/mattpocock/skills) (MIT licence) inspired the dependency-ordered rounds of questions with recommended answers; the procedure above is written independently.
- Claude Code's [best practices](https://code.claude.com/docs/en/best-practices) recommend having the agent interview the user for larger features and making specs self-contained with an end-to-end verification step.
- Google's engineering practices, [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html), warn against building functionality the system does not need yet.
- Martin Fowler, [Yagni](https://martinfowler.com/bliki/Yagni.html), explains why speculative features cost more than they save.
- OWASP, [CSV Injection](https://community.owasp.org/attacks/CSV_Injection), lists the leading characters to neutralise in the acceptance-criteria example.
