# Contributing

A useful change names the failure it prevents, the evidence or official source, and a check that could reveal a regression. Prefer removing a rule that does not earn its context over adding another universal obligation.

Keep `SKILL.md` focused on scope and shared decisions. Put conditional detail in a reference and link every reference/template from the entrypoint. Use an existing project format before adding a template. Do not expand Whetstone into a general programming manual.

Run from the repository root before publishing:

```text
python3 -B tools/validate_skill.py --strict
python3 -B -m unittest discover -s tests
```

Write in English, with concrete, short instructions. Use ordinary hyphens rather than em/en dashes; avoid bold-label bullets. End references with their sources and add Contents when a reference exceeds 100 lines. Summarize sources in original prose and preserve required attribution.

Update behavior scenarios when the intended decision changes. Grade outcomes such as compatibility, scope, authorization and verification, not prescribed wording. A scenario is not a completed evaluation until it has actually run and its artifacts have been inspected. Report model/configuration, cases, failures and limits with results.

Changes are licensed under [MIT-0](LICENSE); contribute only material you can license that way.
