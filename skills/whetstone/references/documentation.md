# Documentation

Read this when a change alters how something is built, configured, run, used or operated, and when you are asked to write a README, guide, reference page, runbook, decision record or changelog.

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

Docs as code means writing documentation with the same tools and workflow as code: plain text in the repository, reviewed in pull requests, checked by automation. Google's review guide expects documentation to change whenever build, test, usage or release steps change.

Apply it:

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

Diátaxis, by Daniele Procida, separates documentation into four kinds that serve different needs. Mixing them produces documents that serve nobody well. Its compass asks two questions: does the reader need to act or to understand, and are they learning or working?

| Kind | Reader's situation | Shape |
|---|---|---|
| Tutorial | Learning by doing | A guided lesson with a guaranteed result; no choices or digressions |
| How-to guide | Working on a specific task | Numbered steps towards a goal; assumes competence |
| Reference | Looking up a fact while working | Complete, accurate, consistently structured; generated where possible |
| Explanation | Studying to understand | Background, reasons, trade-offs and history; no instructions |

## Write a README that gets people started

A new contributor should go from clone to a running system and a passing test suite using only the README.

Check:

- [ ] One paragraph on what the project does and who it is for.
- [ ] Prerequisites with versions.
- [ ] Copy-pasteable commands to install, configure, run, test and build.
- [ ] Where configuration lives and which settings are required; no real secrets in examples.
- [ ] How to deploy, or a link to where that is documented.
- [ ] Where to get help and how to contribute.
- [ ] Licence status, stated plainly even if no licence has been chosen.

## Generate reference material from the source of truth

Hand-written reference material drifts from the code. Generate it where possible.

Apply it:

1. Generate API reference from the OpenAPI or AsyncAPI contract, CLI reference from the argument parser's help, and configuration reference from the configuration schema.
2. Write docstrings for public modules, classes and functions in the style the language's tooling understands, and explain why in comments rather than what (see [implementation.md](implementation.md)).
3. Include at least one working example for every public operation, and test the examples where the tooling allows (for example doctests or example projects built in CI).

## Write for the reader

Apply it:

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

Apply it:

1. Run every command you document, in a clean environment where possible, before you publish it.
2. Check links automatically in CI, and fix or remove broken ones.
3. Build the documentation site, if there is one, in CI so broken markup fails the build.
4. Re-read the page as a newcomer would. If a step depends on knowledge that is not written down, write it down.

Agent instruction files such as `CLAUDE.md` and `AGENTS.md` are documentation for agents. How to keep them short and current is covered in [learning-loop.md](learning-loop.md).

## Failure modes

- The code changes, the README does not, and the next person spends a day on outdated set-up steps.
- A tutorial wanders into reference tables and architecture history, and beginners give up halfway.
- Reference documentation is written by hand and silently drifts from the API.
- Examples contain a real API key, copied from a working terminal.
- Screenshots show an interface that no longer exists, and nothing says when they were taken.

## Sources

- Write the Docs, [Docs as Code](https://www.writethedocs.org/guide/docs-as-code/), defines the practice of writing documentation with code tools.
- Daniele Procida, [Diátaxis](https://diataxis.fr/) and [the Diátaxis compass](https://diataxis.fr/compass/), define the four kinds of documentation and the two questions that tell them apart.
- Google's engineering practices, [What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html), expect documentation updates alongside code changes.
