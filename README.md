# Whetstone

Risk-scaled engineering care for coding agents. Whetstone helps an agent identify a change's consequential failure modes, preserve the contracts it touches, verify the protections and recovery those failures need, and report plainly what was and was not verified. Small edits stay light.

## When it helps

The skill is written to load for work that writes, fixes, debugs, reviews, refactors or ships code, configuration, schemas, infrastructure, user interfaces or LLM features in a software project, including casual requests. It is not meant for prose, slides, explanations or summaries.

- Renaming a variable or changing button text gets the edit, a build or render check and a report naming the file and the change.
- A local behavior change gets a test for the changed behavior and a report with an explicit "Not verified" line.
- A production column rename needs consumer compatibility and a recovery path. A disposable database may need only a direct rename and a check.
- A timeout after a payment request needs an outcome or idempotency check before any retry.
- An internal document assistant needs access filtering before retrieval reaches the model.
- A dependency update needs supply-chain checks, not a design document.

The user and the repository define scope and authorization. Whetstone does not ask again for work the user already authorized, and it adds no automatic document or approval gates. It asks before irreversible or externally visible actions that the request does not cover, such as a push, a deployment, deleting real data or sending a message.

## How it sizes work

| Tier | Typical change | Enough evidence |
|---|---|---|
| T0 | No behavior change | The edit, a build or render check and a report naming the file and the change |
| T1 | Local, reversible behavior change | Relevant tests, a test for the changed behavior and a report of what was and was not verified |
| T2 | Shared behavior or a boundary changes | Consumers, compatibility, failure paths and a known way to undo it |
| T3 | Data, access, money or availability could be lost, or the change is hard to undo | Scope, protections and tested recovery before the consequential step, plus explicit authorization for that step |

Signals such as a new dependency, a schema change, authentication or payments usually raise the tier. The agent confirms each signal against the real context and states the reason when the context lowers or raises the tier. No signal or keyword by itself requires a design document, threat model or approval.

## Contents

- [SKILL.md](skills/whetstone/SKILL.md): core rules, tiers and signals, a short work loop, routing, a definition of done and the report contract.
- Sixteen focused references: understanding the ask, debugging, verification, design and decisions, security, threat modeling, data, contracts and failure handling, observability and performance, supply chain, accessibility, AI boundaries, delivery, version control and review, documentation, and stack checks.
- Six optional templates: change note, pull request, decision record, threat model, incident review and AI evaluation plan.
- An optional diff scanner that suggests a tier floor and flags likely secrets, weakened tests and new suppressions.

## What changed in 0.3.0

Version 0.3.0 builds on 0.2.2. It keeps the lean 0.2.0 base and its authorization model, the concrete failure checks that 0.2.1 restored (service lifecycle, unsafe deserialization, event publication gaps, retrieval and index compatibility, and runtime-specific traps), and the agent outcome checks and reproducible evaluations from 0.2.2. The description covers software changes broadly again, with small edits kept light. T0 to T3 return as escalation signals that the agent checks against the actual context, not as document or approval gates. Reports carry an explicit "Not verified" line, and a compact definition of done is back. Seven short references and five optional templates return in condensed form, and the AI reference adds query-time permission filtering, named evaluation metrics and reruns when prompts or models change. Scanner arguments, JSON fields and exit codes are unchanged. Generic code-minimization and response-length instructions remain outside Whetstone's scope. The full 0.1.x library remains in Git history.

## Install

Copy only `skills/whetstone`, including its supporting files, into your agent's documented skill directory. Avoid installing multiple copies into the same agent.

From ClawHub, once this version is public:

```text
clawhub install @ricardodpalmeida/whetstone --version 0.3.0
```

Or use this repository with the skills CLI:

```text
npx skills add Ricardodpalmeida/whetstone
```

Claude Code plugin installation:

```text
/plugin marketplace add Ricardodpalmeida/whetstone
/plugin install whetstone@whetstone
```

Invoke the skill by name through your agent's skill interface, for example `$whetstone` in Codex. The description covers most software changes, so automatic discovery should usually load it; an explicit invocation also works, and a small task stays light either way.

## Optional scanner

Requires Python 3.8+ and git. Run from the repository being reviewed:

```text
python3 <skill-dir>/scripts/change_scan.py
python3 <skill-dir>/scripts/change_scan.py --staged
python3 <skill-dir>/scripts/change_scan.py --base main --json
```

- Exit 0: no blocking findings, not a security guarantee.
- Exit 1: likely secret; with `--strict`, also test-weakening or suppression signals.
- Exit 2: usage or read failure.

The scanner suggests a tier from changed paths and text, shown as `Review cue` in text output and as `minimum_tier` with `tier_reasons` in JSON. Treat it as a suggested floor to check against the change's actual impact, not a verdict or a release gate. Known false positives can use `change-scan: ignore` or `pragma: allowlist secret` on the relevant line.

Binary content and untracked files over 1 MB are skipped. Read failures are explicit. The scanner redacts likely secret values; it does not inspect a complete Git history or prove that no secret exists.

## Verification

From the repository root:

```text
python3 -B tools/validate_skill.py --strict
python3 -B -m unittest discover -s tests
```

The unit tests cover the scanner and validator. Behavioral scenarios and trigger queries live in [evals](evals/); their assertions describe observable outcomes, not required headings or tier labels. A small smoke evaluation does not establish an advantage over an agent without the skill. Test the models and tasks actually used before claiming such an advantage.

## Contributing and license

Keep rules only when they prevent a concrete failure or change a useful decision. Preserve required checks and show evidence for behavior changes; see [CONTRIBUTING.md](CONTRIBUTING.md). Technical sources live beside the relevant guidance.

[MIT-0](LICENSE). Copyright 2026 Ricardo Almeida.

At version 0.2.0, a [four-case local forward smoke test](evals/forward-smoke.json) checked a typo, an authorized empty-cart behavior change, payment retries and document access filtering. All passed with two isolated evaluating agents and parent inspection. This is limited evidence, without a control group or cross-model performance claim. It has not been repeated on 0.3.0.
