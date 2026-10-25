# Contributing to Whetstone

Whetstone improves when someone shows that a rule is wrong, missing or not worth its tokens. Issues, rule proposals, eval results and pull requests are all welcome.

## Propose a rule or reference

Open a [rule or topic proposal](https://github.com/Ricardodpalmeida/whetstone/issues/new?template=rule-or-topic-proposal.yml) before you write a large change. A proposal needs four things.

1. The failure it prevents. Describe what agents do today without the rule. A transcript or a diff is the strongest evidence.
2. A public source. Link a standard, an RFC, official documentation or a widely used guide. Personal preference is not enough.
3. Why it is worth its tokens. `SKILL.md` loads every time the skill triggers, so it only takes rules that apply to most changes. Everything else goes in a reference that loads on demand. Say where the rule belongs and what it replaces or shortens.
4. An eval or a test that shows it. Add a scenario with gradable assertions to `evals/evals.json`, or a unit test for the scanner or the validator in `tests/`.

A new reference or template also needs a row in the routing table in `SKILL.md`. The validator fails when a file in `references/` or `templates/` is not linked from it.

Corrections need less ceremony. Quote the wrong text, link the source that contradicts it and propose the fix, using the [bug or wrong guidance](https://github.com/Ricardodpalmeida/whetstone/issues/new?template=bug-or-wrong-guidance.yml) form. If you ran the evals, share what you found with the [eval result](https://github.com/Ricardodpalmeida/whetstone/issues/new?template=eval-result.yml) form, failures included.

## Run the checks

Both commands need only Python 3 and its standard library. Run them from the repository root:

```bash
python3 -B tools/validate_skill.py --strict
python3 -B -m unittest discover -s tests
```

The validator checks the frontmatter, the size of `SKILL.md`, every relative link and anchor, the Contents sections, the writing rules, the scripts and the eval files. The scanner tests that need git skip themselves when it is not installed. Both commands must pass before a pull request is merged.

## Write in the house style

1. Write in English, in short sentences and the active voice.
2. Be concrete. Name the command, the threshold, the header or the file.
3. Do not use em or en dashes. The validator rejects them in the skill and the evals.
4. Do not start a bullet or a heading with a bold label followed by a colon.
5. Prefer tables and code blocks to long paragraphs.
6. Write your own prose. Link to sources instead of pasting their text, and attribute any short quotation.
7. End each reference with its sources. Open any file longer than 100 lines with a Contents section.
8. Leave out hype, invented numbers and placeholders.

## Licence

Whetstone is licensed under [MIT-0](LICENSE). By contributing, you agree that your contribution is licensed under MIT-0 too, and that you have the right to license it that way.
