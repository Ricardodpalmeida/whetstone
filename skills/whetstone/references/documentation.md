# Documentation

Use when build, configuration, execution, usage or operations change, or for READMEs, guides, references, runbooks, decision records and changelogs.

## Contents

- [Update documentation in the same change](#update-documentation-in-the-same-change)
- [Choose the right kind of document](#choose-the-right-kind-of-document)
- [Write a README that gets people started](#write-a-readme-that-gets-people-started)
- [Generate reference material from the source of truth](#generate-reference-material-from-the-source-of-truth)
- [Write for the reader](#write-for-the-reader)
- [Verify documentation like code](#verify-documentation-like-code)
- [Failure modes](#failure-modes)
- [Sources](#sources)

## Update documentation in the same change

Docs as code: repository text, PR review and automated checks. Google's review guide requires documentation updates when build, test, usage or release steps change.

1. When a change alters behaviour, configuration, a command, an API, set-up steps or operations, update the affected documentation in the same pull request.
2. Keep documentation next to what it describes: the README at the root, module notes beside the module, decision records and runbooks in a `docs/` folder or wherever the repository already keeps them.
3. Delete documentation that is no longer true. Wrong documentation is worse than none, because readers trust it.

| Change | Documentation to update |
|---|---|
| New or changed configuration option | README or configuration reference, including default and example |
| New or changed endpoint, event or CLI flag | Contract file and generated reference, changelog |
| New dependency or set-up step | README quick start and prerequisites |
| New alert, job or operational procedure | Runbook ([template](../templates/runbook.md)) |
| Decision that is expensive to reverse | Decision record ([template](../templates/decision-record.md)) |
| User-visible change in a release | Changelog and release notes (see [delivery-and-release.md](delivery-and-release.md)) |

## Choose the right kind of document

Daniele Procida's Diátaxis separates four documentation needs. Choose using two axes: act or understand; learn or work. Mixing kinds serves readers poorly.

| Kind | Reader's situation | Shape |
|---|---|---|
| Tutorial | Learning by doing | A guided lesson with a guaranteed result; no choices or digressions |
| How-to guide | Working on a specific task | Numbered steps towards a goal; assumes competence |
| Reference | Looking up a fact while working | Complete, accurate, consistently structured; generated where possible |
| Explanation | Studying to understand | Background, reasons, trade-offs and history; no instructions |

## Write a README that gets people started

The README alone must take a newcomer from clone to a running system and passing tests.

- [ ] One paragraph on what the project does and who it is for.
- [ ] Prerequisites with versions.
- [ ] Copy-pasteable commands to install, configure, run, test and build.
- [ ] Where configuration lives and which settings are required; no real secrets in examples.
- [ ] How to deploy, or a link to where that is documented.
- [ ] Where to get help and how to contribute.
- [ ] Licence status, stated plainly even if no licence has been chosen.

## Generate reference material from the source of truth

Generate reference documentation where possible to prevent drift.

1. Generate API reference from the OpenAPI or AsyncAPI contract, CLI reference from the argument parser's help, and configuration reference from the configuration schema.
2. Write docstrings for public modules, classes and functions in the style the language's tooling understands, and explain why in comments rather than what (see [implementation.md](implementation.md)).
3. Include at least one working example for every public operation, and test the examples where the tooling allows (for example doctests or example projects built in CI).

## Write for the reader

1. Start with what the reader is trying to do, and put the most common task first.
2. Use plain language, short sentences and the active voice. Define each acronym on first use.
3. Use descriptive headings that work as a table of contents, and one idea per paragraph.
4. Show commands and code exactly as they must be typed, in fenced blocks with a language tag, with expected output where it helps.
5. Make documentation accessible: a logical heading hierarchy, alternative text for images, link text that describes the destination, and tables with header rows. Never put essential information only in an image.
6. Date anything that will go stale (versions, screenshots, "currently" statements), so readers can judge freshness.

Bad:

```text
## Misc
Run the thing with the flag (see above) if you need to.
```

Good:

```text
## Run the importer against staging
1. Export the staging database URL: `export DATABASE_URL=...`
2. Run `make import ENV=staging`.
   Expected output ends with: `Imported 1,204 records, 0 errors.`
```

## Verify documentation like code

1. Run every command you document, in a clean environment where possible, before you publish it.
2. Check links automatically in CI, and fix or remove broken ones.
3. Build the documentation site, if there is one, in CI so broken markup fails the build.
4. Re-read the page as a newcomer would. If a step depends on knowledge that is not written down, write it down.

`CLAUDE.md` and `AGENTS.md` document agent instructions; [learning-loop.md](learning-loop.md) covers keeping them concise and current.

## Failure modes

- Unchanged READMEs waste a newcomer's day on outdated setup.
- Reference tables and architecture history derail beginner tutorials.
- Hand-written references silently drift from the API.
- Examples expose real API keys copied from terminals.
- Undated screenshots show obsolete interfaces.

## Sources

- Write the Docs, [Docs as Code](https://www.writethedocs.org/guide/docs-as-code/), defines the practice of writing documentation with code tools.
- Daniele Procida, [Diátaxis](https://diataxis.fr/) and [the Diátaxis compass](https://diataxis.fr/compass/), define the four kinds of documentation and the two questions that tell them apart.
- Google's engineering practices, [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html), expect documentation updates alongside code changes.
