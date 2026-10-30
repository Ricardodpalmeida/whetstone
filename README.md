# Whetstone

Risk-aware review for consequential software changes. Whetstone helps an agent identify what can break, choose sufficient checks and preserve a recovery path. Routine edits stay routine.

## When it helps

Use it for changes to shared data, public contracts, security, production or agent tool access, or request it explicitly for a risk review. It does not activate for every coding task.

- A production column rename needs consumer compatibility and a recovery path. A disposable database may need only a direct rename and a check.
- A timeout after a payment request needs an outcome/idempotency check before retrying.
- An internal document assistant needs access filtering before retrieval reaches the model.
- A dependency update needs verification of the actual change, not an automatic design document.

The user and repository define the scope and authorization. Whetstone does not add approval gates to already authorized work. Reports state outcomes, evidence and material limits without a mandatory six-field form.

## Contents

- [SKILL.md](skills/whetstone/SKILL.md): impact assessment, execution rules and selective reference routing.
- Nine focused references: verification, security, data, APIs/failures, dependencies, accessibility, AI boundaries, delivery and stack-specific traps.
- One optional [change note](skills/whetstone/templates/change-note.md) for a consequential decision or recovery record.
- An optional diff scanner for review cues, likely secrets and test-weakening signals.

Version 0.2.0 removes automatic T0-T3 workflow requirements, mandatory retrospectives and generic engineering tutorials. Existing scanner arguments, JSON fields and exit codes are retained. The previous reference library remains in Git history. Version 0.2.1 restores concrete failure checks from that library, including service lifecycle, unsafe deserialization, event publication gaps, retrieval/index compatibility and runtime-specific traps. Generic code-minimization and response-length instructions are outside Whetstone's scope.

## Install

Copy only `skills/whetstone`, including its supporting files, into your agent's documented skill directory. Avoid installing multiple copies into the same agent.

From ClawHub, once this version is public:

```text
clawhub install @ricardodpalmeida/whetstone --version 0.2.1
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

Invoke the skill by name through your agent's skill interface, for example `$whetstone` in Codex. Automatic discovery is limited by the description above; an explicit invocation still works for a small task without imposing a large workflow.

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

`minimum_tier` and `tier_reasons` remain in JSON for compatibility. T0-T3 values are legacy heuristic cues from paths/text, not minimum process or release gates. Assess the actual impact before acting on them. Known false positives can use `change-scan: ignore` or `pragma: allowlist secret` on the relevant line.

Binary content and untracked files over 1 MB are skipped. Read failures are explicit. The scanner redacts likely secret values; it does not inspect a complete Git history or prove that no secret exists.

## Verification

From the repository root:

```text
python3 -B tools/validate_skill.py --strict
python3 -B -m unittest discover -s tests
```

The unit tests cover the scanner and validator. Behavioral scenarios and selection queries live in [evals](evals/); their assertions describe observable outcomes, not required headings or tier labels. A small smoke evaluation does not establish an advantage over an agent without the skill. Test the models and tasks actually used before claiming such an advantage.

## Contributing and license

Keep rules only when they prevent a concrete failure or change a useful decision. Preserve required checks and show evidence for behavior changes; see [CONTRIBUTING.md](CONTRIBUTING.md). Technical sources live beside the relevant guidance.

[MIT-0](LICENSE). Copyright 2026 Ricardo Almeida.

At version 0.2.0, a [four-case local forward smoke test](evals/forward-smoke.json) checked a typo, an authorized empty-cart behavior change, payment retries and document access filtering. All passed with two isolated evaluating agents and parent inspection. This is limited evidence, without a control group or cross-model performance claim.
