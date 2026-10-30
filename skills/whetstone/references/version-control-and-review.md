# Version control and code review

Use for commits, branches, PRs and review responses or reviews of others' changes.

## Contents

- [Rules for agents using git](#rules-for-agents-using-git)
- [Keep each change small and single-purpose](#keep-each-change-small-and-single-purpose)
- [Write commit messages that explain why](#write-commit-messages-that-explain-why)
- [Integrate often](#integrate-often)
- [Describe the pull request](#describe-the-pull-request)
- [Review your own diff first](#review-your-own-diff-first)
- [Review other people's changes](#review-other-peoples-changes)
- [Respond to review](#respond-to-review)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Rules for agents using git

1. Commit, push, open pull requests, merge or tag only when the user asks or the repository's instructions say so.
2. Never force-push to a shared branch, rewrite published history, or delete branches you did not create, without explicit permission.
3. Never bypass hooks or checks (for example with `--no-verify`) to get a commit through. Fix the cause.
4. Before every commit, read `git status` and the staged diff. Stage files by name rather than everything at once, so stray files, build output, local configuration and secrets stay out.
5. Never commit credentials, personal data, large binaries or generated artefacts that the repository does not already track.
6. Follow the repository's conventions for branch names, commit format, sign-off and attribution trailers.

## Keep each change small and single-purpose

Google recommends "one self-contained change": 100 lines is usually reasonable; 1000 is usually too large. Small changes improve review speed/depth and rollback.

1. Give each pull request one purpose. Separate refactoring, formatting and dependency updates from behaviour changes.
2. Include the tests for the change in the same pull request.
3. Split large work into a sequence of changes that each leave the system working: preparatory refactoring first, then the new code behind a flag, then the switch-over, then the clean-up.
4. When a large mechanical change is unavoidable (a rename across the codebase), keep it purely mechanical and say how it was produced, so reviewers can check the method instead of every line.

## Write commit messages that explain why

Commit history permanently records why code changed.

1. Write a subject line of about 50 characters (72 at most) in the imperative mood ("Add retry budget to payment client"), with no trailing period.
2. Leave a blank line, then a body wrapped at about 72 characters that explains what changed and why, not how.
3. If the repository uses Conventional Commits 1.0.0, use the form `type(scope): description`. `fix` maps to a patch release, `feat` to a minor release, and a `!` after the type or a `BREAKING CHANGE:` footer to a major release.
4. Reference issues and record co-authors in footers, following the repository's convention.
5. Make each commit build and pass tests on its own where practical, so bisecting works (see [debugging.md](debugging.md)).

Bad:

```text
fixed stuff
```

Good:

```text
fix(export): neutralise formula characters in CSV cells

Cells beginning with =, +, - or @ were written unchanged, so a crafted
customer name could execute as a formula when the export was opened in
a spreadsheet application. Prefix such cells with a single quote.

Refs: #1842
```

## Integrate often

Trunk-based development stays close to main. DORA associates better delivery with three or fewer active branches, daily trunk merges, and no code freezes or integration phases.

1. Keep branches short-lived: hours or a few days, not weeks.
2. Merge or rebase from the main branch frequently, following the repository's preferred method, and resolve conflicts while they are small.
3. Hide unfinished work behind feature flags or branch by abstraction instead of a long-lived branch (see [delivery-and-release.md](delivery-and-release.md) and [design.md](design.md)).

## Describe the pull request

Use the [PR template](../templates/pull-request.md): imperative summary, then what changed, why and limitations. Google's guidance calls for enough lasting context without depending on external links.

1. State the goal and the tier, and link the issue.
2. Explain the approach and the alternatives you rejected when they were not obvious.
3. Show evidence of testing: the commands run and their results, screenshots for UI changes, and measurements for performance claims.
4. List the risks, the rollout plan and how to roll back.
5. List assumptions, known limitations and follow-ups honestly. Say what you did not test.
6. Update the description when the change evolves during review.

## Review your own diff first

Review the full diff before requesting review.

- [ ] Every changed line serves the stated purpose; no unrelated edits slipped in.
- [ ] No debug output, commented-out code, TODOs without issues, or secrets.
- [ ] Tests cover the new behaviour and the negative paths, and they pass.
- [ ] Names, comments and documentation are updated to match the new behaviour.
- [ ] The description matches what the diff actually does.

## Review other people's changes

Google's review standard favours approval when code health definitely improves, even without perfection.

1. Look at design first, then functionality and edge cases, complexity, tests, naming, comments, style and documentation. Read every line you are responsible for.
2. Check the change against the threat model, accessibility and observability expectations of its tier.
3. Label each comment's weight: required, "Nit:" for minor polish, "Optional" or "Consider" for suggestions, "FYI" for information only.
4. Be kind and specific. Comment on the code, not the author, and explain the reason behind each request.
5. When code confused you, ask for clearer code or a code comment rather than an explanation in the review tool, because future readers will not see the review.
6. Respond within one business day at most. Slow reviews block the whole team and push people towards larger, riskier changes.
7. Say what is good, too, so the author knows what to keep doing.

## Respond to review

1. Address every comment: change the code, or explain why not. Do not silently ignore one.
2. Push follow-up commits during review unless the repository prefers amended commits, so reviewers can see what changed since they last looked.
3. Resolve a thread only when the concern is actually addressed.
4. If you disagree, give your reasoning once, with evidence, and accept the reviewer's or the owner's decision.

## Failure modes

- A rubber-stamped 3,000-line PR mixing refactors, features and dependencies resists clean rollback.
- "wip"/"fix" commits leave future readers without rationale.
- `git add .` commits `.env` production credentials.
- Weeks of branch divergence produce subtle merge regressions.
- Perfectionist reviews stall changes and discourage review requests.

## Sources

- Google's engineering practices: [Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html), [Writing good CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html), [The standard of code review](https://google.github.io/eng-practices/review/reviewer/standard.html), [Speed of code reviews](https://google.github.io/eng-practices/review/reviewer/speed.html) and [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html).
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) defines the commit format and its mapping to semantic versioning.
- Chris Beams, [How to Write a Git Commit Message](https://cbea.ms/git-commit/), gives the seven rules summarised above.
- [Trunk Based Development](https://trunkbaseddevelopment.com/) and DORA's [trunk-based development capability](https://dora.dev/capabilities/trunk-based-development/) describe short-lived branches and daily integration.
