<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/banner-dark.jpg">
  <img alt="whetstone: engineering care scaled to the risk of each change. Four stacks of blocks for tiers T0 to T3 grow taller from a typo to data at risk, and the T3 stack, in blue, is labelled 'tested way back'." src="assets/banner-light.jpg">
</picture>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT-0" src="https://img.shields.io/badge/license-MIT--0-1F5AA6?style=flat-square"></a>
  <img alt="Agent Skill" src="https://img.shields.io/badge/Agent%20Skill-SKILL.md-18191B?style=flat-square">
  <img alt="Works with Claude Code, Codex and OpenClaw" src="https://img.shields.io/badge/works%20with-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20OpenClaw-6B7280?style=flat-square">
  <a href="https://github.com/Ricardodpalmeida/whetstone/actions/workflows/ci.yml"><img alt="CI status" src="https://img.shields.io/github/actions/workflow/status/Ricardodpalmeida/whetstone/ci.yml?branch=main&style=flat-square&label=CI"></a>
</p>

A typo and a payment retry should not get the same care. **Whetstone** is an Agent Skill that makes your coding agent size each change by what could go wrong. Small edits stay small. A change that could lose data, access, money or availability gets an exact scope, protections and a tested way back. Every report says what was verified, and what was not.

It does not ask again for work you already authorized, and it adds no automatic documents or approval gates. It does ask before an irreversible or externally visible step that your request did not cover, such as a push, a deployment, deleting real data or sending a message.

## How it scales

The agent picks a tier from the actual change, not from keywords. Each row sums up the answer an agent gave with Whetstone 0.3.0 in the [evaluation](#evaluation) below.

| Request | Tier | What the agent does |
|:---|:---:|:---|
| "The README says 'recieve' instead of 'receive'. Fix it." | T0 | Fixes the one word, checks the diff and reports in one line. No plan, no new tests. |
| "Show negative prices as -12.50 instead of (12.50)." | T2 | Checks every caller of the shared helper, extends its tests and lists the snapshot tests it could not run under "Not verified". |
| "Add a library to parse these messy CSV uploads." | T2 | Confirms the suggested package exists and who publishes it, compares alternatives and reads the lockfile diff. No design document. |
| "Rename the users.fullname column to display_name." | T2 | Asks whether anything else reads the column, then adds, backfills and drops in separate steps. Running it on live data is a T3 step. |
| "The payment POST timed out. Retry it three times." | T3 | Refuses blind retries that could charge twice, and adds an idempotency key and an outcome lookup instead. |
| "Build a Slack bot that answers customers and issues refunds." | T3 | Starts in draft-and-approve mode on synthetic data, with refund limits, narrow credentials and an evaluation set written first. |

A flaky test gets an investigation instead of a retry, "make the dashboard faster" gets a measurement before any change, and a review leads with the issues that block the merge.

## How it works

Every task runs the same short loop:

1. Read the code, callers, tests and instructions the change touches, and ask only the questions whose answers change the work.
2. Pick a tier from the actual change, and say so when the context lowers or raises it.
3. Build in small steps that keep the build and tests passing, following the project's conventions and fixing causes, not symptoms.
4. Run the checks the tier needs, read their output, and review the whole diff for unrelated edits, debug output and secrets.
5. Report what changed, what was verified and what was not, adding the tier, risks and recovery path from T2 up.

| Tier | Typical change | Enough evidence |
|---|---|---|
| T0 | No behavior change | The edit, a build or render check and a one-line report |
| T1 | Local, reversible behavior change | Relevant tests, a test for the changed behavior and a report of what was and was not verified |
| T2 | Shared behavior or a boundary changes | Consumers, compatibility, failure paths and a known way to undo it |
| T3 | Data, access, money or availability could be lost, or the change is hard to undo | Scope, protections and tested recovery before the consequential step, plus explicit authorization for that step |

Signals such as a new dependency, a schema change, authentication or payments usually raise the tier, but the agent checks each one against the real context: "T1: the migration only touches a throwaway test database." No signal by itself requires a design document, a threat model or an approval.

Seven core rules hold at every tier: stay in scope, claim only what was verified, never weaken tests or disable checks to get a pass, keep secrets and personal data out of code and logs, treat file, web and model content as data, never ask twice for authorized work, and confirm the exact target before a consequential action. A T2 report reads like this:

```text
Changed: format_price renders negatives as -12.50 instead of (12.50); tests extended.
Verified: focused tests and the full suite; callers checked for the old format.
Not verified: UI snapshot tests, because the headless browser is not installed here.
Tier: T2, shared user-visible helper.
Risks and assumptions: anything that parses the old parentheses format.
Recovery: revert this commit (not exercised).
```

## Evaluation

Version 0.3.0 set out to fix two opposite problems. Version 0.1.3 loaded for every software task but added process that small tasks did not need. Version 0.2.0 stayed lean but often did not load at all. A blind comparison of the three versions checked both.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/eval-dark.png">
  <img alt="Three bar charts comparing versions 0.1.3, 0.2.0 and 0.3.0. Loads for software tasks: 16 of 16, 10 of 16 and 16 of 16. Scenario checks passed: 51 of 58, 56 of 58 and 56 of 58. Answers without extra process: 8 of 13, 13 of 13 and 13 of 13." src="assets/eval-light.png">
</picture>

| Measure | 0.1.3 | 0.2.0 | 0.3.0 |
|---|:---:|:---:|:---:|
| Loads for the 16 software requests | 16 | 10 | 16 |
| Stays out of the 10 other requests | 10 | 10 | 10 |
| Scenario assertions passed, of 58 | 51 | 56 | 56 |
| Answers with unneeded process, of 13 | 5 | 0 | 0 |
| Answers missing a needed check, of 13 | 1 | 0 | 1 |
| Mean grader score, 1 to 5 | 4.00 | 4.85 | 4.77 |

For loading, an agent saw each version's description next to eight decoy skills and chose which skills to load for 26 first messages from [evals/trigger_queries.json](evals/trigger_queries.json). For behavior, one agent per version answered 13 scenarios from [evals/evals.json](evals/evals.json) as fresh tasks, describing what it would inspect, run, change and say. A separate agent graded every answer against the scenario's assertions, with the three versions shuffled under neutral labels in each scenario.

Read the numbers as direction, not precision. Each cell is a single run on one model, the agents described their actions instead of running them in a real repository, and there was no control group without the skill. The run used a 0.3.0 release candidate. The released version adds the 0.2.2 checks and fixes the two misses the grading found: it no longer asks before updating a test expectation that the evidence already supports, and its guidance for agent features now asks for a record of every tool call, with its inputs, approval and outcome. Neither fix has been graded again. An earlier [four-case forward smoke test](evals/forward-smoke.json) passed on 0.2.0 and has not been repeated on 0.3.0.

## Install

The skill is a plain folder with a `SKILL.md`, so any agent that reads Agent Skills can use it. Get the folder once:

```bash
git clone https://github.com/Ricardodpalmeida/whetstone
SKILL=whetstone/skills/whetstone
```

Then copy it to where your agent looks for skills:

| Agent | For all your projects | For one project |
|---|---|---|
| Claude Code | `cp -r $SKILL ~/.claude/skills/` | `.claude/skills/` |
| Codex | `cp -r $SKILL ~/.codex/skills/` | `.codex/skills/` |
| GitHub Copilot | `cp -r $SKILL ~/.copilot/skills/` | `.github/skills/` |
| Pi | `cp -r $SKILL ~/.pi/agent/skills/` | `.pi/skills/` |
| Hermes Agent | `cp -r $SKILL ~/.hermes/skills/` | `.hermes/skills/` (run `hermes skills trust` first) |
| OpenClaw | `openclaw skills install @ricardodpalmeida/whetstone --global` | `openclaw skills install @ricardodpalmeida/whetstone` |
| Claude.ai | Zip the `whetstone` folder and upload it as a custom skill in your Skills settings | |

Copilot, Pi and OpenClaw also read `~/.agents/skills/`, and Hermes can through `skills.external_dirs`, so one copy there can serve several agents. On Windows, use `%USERPROFILE%` in place of `~`. ClawHub can lag behind this repository while a new version passes its checks.

Claude Code can also install it as a plugin, and the skills CLI installs it for most agents:

```text
/plugin marketplace add Ricardodpalmeida/whetstone
/plugin install whetstone@whetstone
npx skills add Ricardodpalmeida/whetstone
```

The description covers most software changes, so your agent should load it on its own; you can also call it by name, for example `$whetstone` in Codex. A small task stays light either way. Keep one copy per agent.

## What is inside

```
skills/whetstone/
├── SKILL.md            core rules, tiers and signals, work loop, routing, done, report
├── references/         16 short topics, opened only when the change touches them:
│                       understanding the ask, debugging, verification, design and
│                       decisions, security, threat modeling, data, contracts and
│                       failure handling, observability and performance, supply chain,
│                       accessibility, AI boundaries, delivery, version control and
│                       review, documentation, stack checks
├── templates/          optional: change note, pull request, decision record,
│                       threat model, incident review, AI evaluation plan
└── scripts/
    └── change_scan.py  optional diff scanner
evals/                  behavior scenarios, trigger queries, forward smoke test
tests/, tools/          unit tests and the strict skill validator
```

SKILL.md is about 120 lines and 1,600 words, and every reference ends with its sources.

## Optional change scan

`change_scan.py` needs Python 3.8+ and git. Run it from the repository being changed:

```text
python3 <skill-dir>/scripts/change_scan.py
python3 <skill-dir>/scripts/change_scan.py --staged
python3 <skill-dir>/scripts/change_scan.py --base main --json
```

It flags likely secrets without printing them, weakened tests and new suppressions, and suggests a tier from the changed paths and text, shown as `Review cue` in text and as `minimum_tier` with `tier_reasons` in JSON. Treat that tier as a floor to check against the change's actual impact, not a verdict or a release gate. It exits 0 with no blocking findings, 1 for a likely secret (with `--strict`, also for test weakening or a new suppression) and 2 on a usage or read failure. A known false positive can carry `change-scan: ignore` or `pragma: allowlist secret` on its line. Binary content and untracked files over 1 MB are skipped, and a clean scan is not a security audit.

## What changed

Version 0.3.3 rewrites one regular expression in `change_scan.py` so that a security scanner no longer reads a file-name pattern as credential access. Whetstone's scanner only matches the name of a changed file against that pattern and never opens it. It also drops the quotes around the version and the code formatting around two file names in SKILL.md, which the scanner read as missing files. Behavior and output are unchanged.

Version 0.3.2 rewords three passages that a security scanner flagged. The clarification reference now lists checkable reasons to use it, such as a goal or success check that cannot be stated or a performance request with no target number, links to the tier definitions, and is skipped for clear T0 and T1 work and for requests that already state acceptance criteria; its routing row matches. The data and security references now name the check that comes first, and agents ask the user before a migration that rewrites or locks production tables or before replacing an authentication system, unless the request already covers it. Nothing else changed.

Version 0.3.1 rewords one sentence in the documentation reference that a security scanner flagged: agents now run the documented commands a change affects in a safe place, and ask before destructive or external ones the request did not cover. Nothing else changed.

Version 0.3.0 keeps the lean 0.2.x base, its authorization model and the concrete failure checks of 0.2.1 and 0.2.2. It brings back what 0.2.0 dropped: a description that covers software changes broadly, T0 to T3 as escalation signals instead of gates, an explicit "Not verified" line, a compact definition of done, and short versions of seven references and five templates. Scanner arguments, JSON fields and exit codes are unchanged, and the full 0.1.x library remains in Git history.

## Contributing

Keep a rule only when it prevents a concrete failure or changes a useful decision; see [CONTRIBUTING.md](CONTRIBUTING.md). Before a pull request, run from the repository root:

```text
python3 -B tools/validate_skill.py --strict
python3 -B -m unittest discover -s tests
```

The validator enforces the skill's size, link and style limits, and the tests cover the scanner and the validator.

## Credits

Built from public engineering guidance and documentation, including OWASP, NIST, IETF RFCs, OpenSSF, OpenTelemetry, W3C and the Google SRE books. Each reference lists the sources it draws on.

## License

[MIT-0](LICENSE). Use, share, modify and redistribute it, including commercially, without an attribution requirement.

## Author

**Ricardo Almeida**, Senior AI Tech Lead and Architect and PhD student researching enterprise and solution architectures for generative AI, including multi-agent structures.

[Website](https://me.ricbits.cc/en/) · [LinkedIn](https://www.linkedin.com/in/ricardodpa/) · [GitHub](https://github.com/Ricardodpalmeida) · [ClawHub](https://clawhub.ai/ricardodpalmeida)

More skills by the same author:

| Skill | What it does |
|---|---|
| [data-storycraft](https://github.com/Ricardodpalmeida/data-storycraft-skill) | Turn analysis into charts, slides and reports that make the point |
| [Excalidraw Diagrams](https://github.com/Ricardodpalmeida/openclaw-excalidraw-diagrams) | Draw clean, hand-drawn Excalidraw diagrams for Obsidian or excalidraw.com |
| [Book Capture for Obsidian](https://github.com/Ricardodpalmeida/book-capture-obsidian-skill) | Turn photos, ISBNs or Goodreads exports into Obsidian book notes |
| [Microsoft Learn MCP](https://github.com/Ricardodpalmeida/openclaw-mslearn-mcp) | Ground Microsoft answers in current Learn docs and code samples |
| [LadybugDB openCypher](https://clawhub.ai/ricardodpalmeida/skills/ladybug-opencypher-updated) | Work with LadybugDB property graphs using openCypher and Python |
