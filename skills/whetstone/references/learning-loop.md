# Learning loop

Read this at the end of every task at T1 or above, after an incident, when a reviewer catches something you missed, and whenever the user corrects you.

## Contents

- [Close each task with a short retrospective](#close-each-task-with-a-short-retrospective)
- [Prefer prevention over memory](#prefer-prevention-over-memory)
- [Write lessons where the next session will read them](#write-lessons-where-the-next-session-will-read-them)
- [Respect consent and scope](#respect-consent-and-scope)
- [Write lessons that work](#write-lessons-that-work)
- [Turn incidents and reviews into improvements](#turn-incidents-and-reviews-into-improvements)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Close each task with a short retrospective

Compound engineering, as described by Dan Shipper and Kieran Klaassen, adds a fourth step to plan, work and review: compound, so that "each unit of engineering work should make subsequent units easier". Skipping it leaves you doing traditional engineering with AI assistance.

Ask four questions before you report the task as done:

1. What surprised me, or took longer than it should have?
2. What did a test, a reviewer or the user catch that I should have caught myself?
3. Did I rediscover something that a previous session must also have had to discover?
4. What would stop this whole class of problem from recurring?

If every answer is "nothing", record nothing. Most tasks teach nothing new, and noise in instruction files has a cost.

## Prefer prevention over memory

A rule an agent must remember is the weakest form of prevention. Choose the strongest option that is proportionate:

| Strength | Mechanism | Example |
|---|---|---|
| Strongest | Make the mistake impossible | A type, a database constraint, a safer API that removes the dangerous option |
| Strong | An automated check | A test, a lint rule, a CI gate, a pre-commit or tool hook |
| Medium | A documented convention in the repository's instruction file | "Use the shared HTTP client in `lib/http`; it sets timeouts and tracing" |
| Weak | A note in a personal or session memory | Useful for preferences, not for safety |

Claude Code's documentation makes the same point: instruction files are context, not enforced configuration, and an action that must always be blocked needs a hook instead.

## Write lessons where the next session will read them

Apply it:

1. Put project lessons in the repository's existing instruction file. Claude Code reads `CLAUDE.md` (or `.claude/CLAUDE.md`) and reads `AGENTS.md` when there is no `CLAUDE.md`; many other agents, including OpenClaw agents, read `AGENTS.md`. Use whichever file the repository already has. Do not create a second file that duplicates it.
2. Keep each instruction file short. Claude Code's guidance targets under 200 lines per `CLAUDE.md`, because longer files consume context and reduce adherence.
3. Keep only facts every session needs in the main file: build and test commands, conventions, layout, "always" and "never" rules. Move multi-step procedures into a skill, and rules for one part of the codebase into a path-scoped rule file (for example `.claude/rules/`) or a nested instruction file in that directory.
4. Put longer explanations of solved problems in the repository's documentation, and link to them from the instruction file instead of pasting them in.

## Respect consent and scope

Instruction files change how every future session behaves, so changes to them must be visible and approved.

Apply it:

1. Make changes to repository instruction files as part of the same reviewed change as the work that taught the lesson, and call them out in the PR description or final report.
2. Never edit personal or global instruction files (for example `~/.claude/CLAUDE.md`, an OpenClaw agent's workspace files, or another tool's memory store) without asking. Propose the exact text and where it would go, and let the user apply or approve it.
3. Never record secrets, credentials, personal data or customer details in instruction files or memory.
4. Never weaken a safety rule in an instruction file to make your current task easier. Raise the conflict with the user instead.

## Write lessons that work

Apply it:

1. State each lesson as a specific, checkable instruction with its reason: "Run `make db-test` before committing migrations, because the unit suite uses SQLite and misses Postgres-only syntax."
2. Prefer one line per rule, grouped under clear headings. Add a short example only when the rule is easy to misread.
3. Before adding a rule, search the file for an existing rule on the same topic, and edit it instead of adding a near-duplicate.
4. Remove rules that are obsolete or contradicted. Two conflicting instructions make behaviour unpredictable.
5. Write the rule for the repository as it is, not for the mistake as it happened; avoid narratives such as "last time I forgot to...".

Bad:

```text
- Be careful with the database.
- Remember the thing about the tests from the payments work.
```

Good:

```text
- Wrap multi-table writes in `db.transaction()`; partial writes corrupted ledgers in incident 2026-03.
- Payment tests need `PAYMENTS_FAKE=1`; without it they call the provider's real sandbox and fail on rate limits.
```

## Turn incidents and reviews into improvements

Apply it:

1. Give every action item from an incident review an owner, a due date and a tracking issue, and check later that it was done. Google's postmortem chapter defines a postmortem as including the follow-up actions that prevent recurrence, and warns that "an unreviewed postmortem might as well never have existed".
2. When the same review comment appears twice, turn it into an automated check or a documented convention.
3. When a runbook step was wrong or missing during an incident, fix the runbook in the follow-up change.
4. When the user corrects your approach, ask whether the correction is project-specific (propose a repository instruction), personal (propose a personal instruction), or one-off (record nothing).

Check:

- [ ] The retrospective questions were asked, and any lesson was recorded in the strongest proportionate form.
- [ ] Repository instruction changes are in the diff and mentioned in the report.
- [ ] Personal or global instruction changes were proposed, not made.
- [ ] Instruction files contain no secrets, personal data or contradictions.

## Failure modes

- Every task appends a paragraph to `CLAUDE.md`, the file grows to a thousand lines, and adherence drops for all of it.
- A lesson is written to memory when it should have been a test, and the same bug returns when a different agent or person works on the code.
- An agent silently edits the user's global instruction file, changing behaviour across unrelated projects.
- Contradictory rules accumulate ("always use the ORM", "write raw SQL for reports"), and the agent picks one at random.
- Incident action items are recorded but never assigned, and the same incident happens again.

## Sources

- Dan Shipper and Kieran Klaassen, [Compound Engineering: How Every Codes With Agents](https://every.to/source-code/compound-engineering-how-every-codes-with-agents), describe the plan, work, review and compound loop and capturing lessons in instruction files and automated checks.
- Claude Code, [How Claude remembers your project](https://code.claude.com/docs/en/memory), documents `CLAUDE.md`, `AGENTS.md`, path-scoped rules, the 200-line target and the role of hooks.
- OpenClaw, [Agent workspace](https://docs.openclaw.ai/concepts/agent-workspace), describes the workspace and its instruction files.
- Google's SRE book, [Postmortem Culture](https://sre.google/sre-book/postmortem-culture/), covers follow-up actions and reviewing every postmortem.
