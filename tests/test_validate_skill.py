"""Tests for tools/validate_skill.py (standard library only).

Run from the repository root:  python3 -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "tools" / "validate_skill.py"

sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location("validate_skill", VALIDATOR)
vs = importlib.util.module_from_spec(_spec)
sys.modules["validate_skill"] = vs  # dataclasses resolve annotations through sys.modules
_spec.loader.exec_module(vs)

GOOD_DESCRIPTION = "Formats release notes from merged pull requests. Use when preparing a release or a changelog entry."
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


def contents_reference(sections, lines_per_section=40, toc=True, skip_in_toc=()):
    """Build a reference file longer than 100 lines, optionally with a Contents section."""
    out = ["# Reference", ""]
    if toc:
        out += ["## Contents", ""]
        out += [f"- [{s}](#{s.lower().replace(' ', '-')})" for s in sections if s not in skip_in_toc]
        out.append("")
    for section in sections:
        out += [f"## {section}", ""] + ["Text line."] * lines_per_section + [""]
    return "\n".join(out) + "\n"


class SkillFixture:
    """A throwaway skill folder in a temporary directory."""

    def __init__(self, test: unittest.TestCase, name="demo-skill", folder=None, frontmatter=None, body=None, files=None):
        self._tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.dir = self.root / (folder or name)
        self.dir.mkdir()
        if frontmatter is None:
            frontmatter = f"name: {name}\ndescription: {GOOD_DESCRIPTION}\n"
        if body is None:
            body = "# Demo\n\nRead [the guide](references/guide.md) and use [the template](templates/form.md).\n"
            files = {"references/guide.md": "# Guide\n\nShort guide.\n", "templates/form.md": "# Form\n", **(files or {})}
        self.write("SKILL.md", f"---\n{frontmatter}---\n\n{body}")
        for rel, text in (files or {}).items():
            self.write(rel, text)

    def write(self, rel, text):
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def validate(self):
        report = vs.Report()
        name = vs.validate_skill(self.dir, report)
        return name, report


def messages(report, level="error"):
    return [i.message for i in report.issues if i.level == level]


class RealSkillTests(unittest.TestCase):
    def test_repository_skill_and_evals_pass_cleanly(self):
        report = vs.Report()
        name = vs.validate_skill(REPO_ROOT / "skills" / "whetstone", report)
        self.assertEqual(name, "whetstone")
        if (REPO_ROOT / "evals").is_dir():
            vs.validate_evals(REPO_ROOT / "evals", [name], report)
        self.assertEqual([i.render() for i in report.issues], [])


class FrontmatterTests(unittest.TestCase):
    def test_minimal_valid_skill(self):
        name, report = SkillFixture(self).validate()
        self.assertEqual(name, "demo-skill")
        self.assertEqual(report.issues, [])

    def test_name_rules(self):
        cases = {
            "Demo-Skill": "lowercase ASCII",
            "demo--skill": "lowercase ASCII",
            "-demo": "lowercase ASCII",
            "claude-helper": "reserved word 'claude'",
            "x" * 65: "1 to 64 characters",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                _, report = SkillFixture(self, name=name).validate()
                self.assertTrue(any(expected in m for m in messages(report)), messages(report))

    def test_name_must_match_folder(self):
        _, report = SkillFixture(self, name="demo-skill", folder="other-folder").validate()
        self.assertTrue(any("must match the folder name" in m for m in messages(report)))

    def test_missing_fields_and_unknown_keys(self):
        _, report = SkillFixture(self, frontmatter="name: demo-skill\nargument-hint: x\n").validate()
        found = messages(report)
        self.assertTrue(any("missing required field 'description'" in m for m in found))
        self.assertTrue(any("unexpected frontmatter key(s) argument-hint" in m for m in found))

    def test_yaml_traps_in_plain_values(self):
        traps = {
            "description: Does things: well. Use when needed.\n": "contains ': '",
            "description: Does things. Use when needed #1 choice.\n": "starts a YAML comment",
            "description: [list, of, things]\n": "cannot start with '['",
            "description: yes\n": "'description' must be a string",
        }
        for line, expected in traps.items():
            with self.subTest(line=line):
                _, report = SkillFixture(self, frontmatter="name: demo-skill\n" + line).validate()
                self.assertTrue(any(expected in m for m in messages(report)), messages(report))

    def test_quoted_values_are_accepted(self):
        frontmatter = (
            'name: "demo-skill"\n'
            "description: 'Turns notes into a summary: short and clear. Use when asked for a summary.'\n"
            'metadata:\n  version: "1.0"\n  owner: docs-team\n'
        )
        _, report = SkillFixture(self, frontmatter=frontmatter).validate()
        self.assertEqual(report.issues, [])

    def test_description_limits(self):
        long_first = "Formats " + "very " * 40 + "long notes. Use when asked."
        _, report = SkillFixture(self, frontmatter=f"name: demo-skill\ndescription: {long_first}\n").validate()
        self.assertTrue(any("first sentence" in m for m in messages(report, "warning")))
        too_long = "Formats notes. Use when asked. " + "More words here. " * 70
        _, report = SkillFixture(self, frontmatter=f"name: demo-skill\ndescription: {too_long.strip()}\n").validate()
        self.assertTrue(any("the limit is 1024" in m for m in messages(report)))
        _, report = SkillFixture(self, frontmatter="name: demo-skill\ndescription: Builds <b>pages</b>. Use when asked.\n").validate()
        self.assertTrue(any("angle brackets" in m for m in messages(report)))

    def test_description_must_be_one_line_and_say_when(self):
        frontmatter = "name: demo-skill\ndescription: |\n  Formats notes.\n  Use when asked.\n"
        _, report = SkillFixture(self, frontmatter=frontmatter).validate()
        self.assertTrue(any("single line" in m for m in messages(report)))
        _, report = SkillFixture(self, frontmatter="name: demo-skill\ndescription: Formats release notes nicely.\n").validate()
        self.assertTrue(any("say when to use" in m for m in messages(report, "warning")))

    def test_metadata_values_must_stay_strings(self):
        frontmatter = f"name: demo-skill\ndescription: {GOOD_DESCRIPTION}\nmetadata:\n  version: 1.0\n"
        _, report = SkillFixture(self, frontmatter=frontmatter).validate()
        self.assertTrue(any("would load as a number" in m for m in messages(report)))

    def test_frontmatter_structure_errors(self):
        fixture = SkillFixture(self)
        fixture.write("SKILL.md", "# No frontmatter\n")
        _, report = fixture.validate()
        self.assertTrue(any("must start with a '---' line" in m for m in messages(report)))
        fixture.write("SKILL.md", vs.BOM + "---\nname: demo-skill\n---\n")
        _, report = fixture.validate()
        self.assertTrue(any("byte order mark" in m for m in messages(report)))
        fixture.write("SKILL.md", "---\nname: demo-skill\nname: again\n---\nBody\n")
        _, report = fixture.validate()
        self.assertTrue(any("duplicate key 'name'" in m for m in messages(report)))

    def test_skill_md_name_is_case_sensitive(self):
        fixture = SkillFixture(self)
        os.rename(fixture.dir / "SKILL.md", fixture.dir / "skill.md")
        _, report = fixture.validate()
        self.assertTrue(any("missing required file SKILL.md" in m for m in messages(report)))


class BodyAndLinkTests(unittest.TestCase):
    def test_body_length_limit(self):
        body = "# Demo\n\n[g](references/guide.md) [t](templates/form.md)\n" + "Line.\n" * 520
        _, report = SkillFixture(self, body=body, files={"references/guide.md": "# G\n", "templates/form.md": "# F\n"}).validate()
        self.assertTrue(any("keep it under 500" in m for m in messages(report)))

    def test_link_checks(self):
        body = (
            "# Demo\n\n"
            "[ok](references/guide.md#guide) [missing](references/nope.md) [escape](../outside.md)\n"
            "[bad anchor](references/guide.md#no-such-heading) [windows](references\\guide.md)\n"
            "[self](#demo) [web](https://example.com/page) [t](templates/form.md)\n\n"
            "```\n[ignored](not/checked.md)\n```\n\n"
            "Inline code `[ignored](also/not/checked.md)` is skipped too.\n"
        )
        fixture = SkillFixture(self, body=body, files={"references/guide.md": "# Guide\n", "templates/form.md": "# F\n"})
        (fixture.root / "outside.md").write_text("# Outside\n", encoding="utf-8")
        _, report = fixture.validate()
        found = messages(report)
        self.assertEqual(len(found), 4, found)
        self.assertTrue(any("broken link: references/nope.md" in m for m in found))
        self.assertTrue(any("leaves the skill folder" in m for m in found))
        self.assertTrue(any("'#no-such-heading'" in m for m in found))
        self.assertTrue(any("forward slashes" in m for m in found))

    def test_long_reference_needs_complete_contents(self):
        sections = ["First part", "Second part", "Sources"]
        for text, expected in (
            (contents_reference(sections, toc=False), "does not open with a '## Contents' section"),
            (contents_reference(sections, skip_in_toc=("Sources",)), "does not link to '## Sources'"),
        ):
            with self.subTest(expected=expected):
                _, report = SkillFixture(self, files={"references/guide.md": text}).validate()
                self.assertTrue(any(expected in m for m in messages(report)), messages(report))
        _, report = SkillFixture(self, files={"references/guide.md": contents_reference(sections)}).validate()
        self.assertEqual(messages(report), [])

    def test_every_reference_and_template_is_linked_from_skill_md(self):
        _, report = SkillFixture(self, files={"references/orphan.md": "# Orphan\n"}).validate()
        self.assertTrue(any("not linked from SKILL.md" in m for m in messages(report)))

    def test_writing_rules(self):
        guide = (
            f"# Guide\n\nUse a comma {EM_DASH} not this.\nPages 1{EN_DASH}3.\n\n"
            "- **Rule:** do the thing.\n- **Rule**: do it again.\n\n"
            "```markdown\n- **Allowed:** inside a code block.\n```\n"
        )
        _, report = SkillFixture(self, files={"references/guide.md": guide}).validate()
        found = messages(report)
        self.assertEqual(sum("em dash" in m for m in found), 1)
        self.assertEqual(sum("en dash" in m for m in found), 1)
        self.assertEqual(sum("'**Label:** description'" in m for m in found), 2)

    def test_scripts_compile_and_are_mentioned(self):
        fixture = SkillFixture(self, files={"scripts/broken.py": "def oops(:\n"})
        _, report = fixture.validate()
        self.assertTrue(any("does not compile" in m for m in messages(report)))
        self.assertTrue(any("not mentioned in SKILL.md" in m for m in messages(report, "warning")))

    def test_stray_generated_files_are_reported(self):
        fixture = SkillFixture(self, files={"scripts/__pycache__/x.cpython-313.pyc": "x"})
        _, report = fixture.validate()
        warnings = [i for i in report.issues if i.level == "warning" and "generated or system file" in i.message]
        self.assertEqual(len(warnings), 1)


class SlugTests(unittest.TestCase):
    def test_github_style_slugs(self):
        self.assertEqual(vs.github_slug("Stack notes: Azure"), "stack-notes-azure")
        self.assertEqual(vs.github_slug("CI/CD pipelines"), "cicd-pipelines")
        self.assertEqual(vs.github_slug("OAuth 2.0 and `PKCE`"), "oauth-20-and-pkce")
        self.assertEqual(vs.github_slug("Don't skip [links](x.md)"), "dont-skip-links")

    def test_duplicate_headings_get_suffixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text("# A\n## Sources\n## Sources\n```\n## Not a heading\n```\n", encoding="utf-8")
            doc = vs.read_markdown(path)
        self.assertEqual([slug for *_, slug in doc.headings], ["a", "sources", "sources-1"])


class EvalsTests(unittest.TestCase):
    def write_evals(self, evals=None, triggers=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        evals_dir = Path(tmp.name) / "evals"
        evals_dir.mkdir()
        if evals is not None:
            (evals_dir / "evals.json").write_text(json.dumps(evals), encoding="utf-8")
        if triggers is not None:
            (evals_dir / "trigger_queries.json").write_text(json.dumps(triggers), encoding="utf-8")
        report = vs.Report()
        vs.validate_evals(evals_dir, ["demo-skill"], report)
        return report

    @staticmethod
    def case(case_id, **overrides):
        base = {"id": case_id, "prompt": "Fix the typo in README.md", "expected_output": "A one-line fix.",
                "assertions": ["Only README.md changes"], "tags": ["trivial"]}
        base.update(overrides)
        return base

    def triggers(self, true_count=8, false_count=8):
        return [{"query": f"yes {i}", "should_trigger": True} for i in range(true_count)] + [
            {"query": f"no {i}", "should_trigger": False} for i in range(false_count)
        ]

    def test_valid_evals(self):
        report = self.write_evals({"skill_name": "demo-skill", "evals": [self.case(1), self.case(2)]}, self.triggers())
        self.assertEqual(report.issues, [])

    def test_eval_errors(self):
        report = self.write_evals({
            "skill_name": "other-skill",
            "evals": [self.case(1), self.case(1), self.case(3, prompt=""), self.case(4, assertions=[]),
                      self.case(5, files=["evals/files/missing.txt"])],
        })
        found = messages(report)
        self.assertTrue(any("'skill_name' must name a validated skill" in m for m in found))
        self.assertTrue(any("reuses id 1" in m for m in found))
        self.assertTrue(any("non-empty 'prompt'" in m for m in found))
        self.assertTrue(any("'assertions' must be a non-empty list" in m for m in found))
        self.assertTrue(any("input file not found" in m for m in found))

    def test_trigger_query_errors_and_balance(self):
        bad = self.triggers() + [{"query": "maybe", "should_trigger": "yes"}, {"query": "yes 0", "should_trigger": True}]
        report = self.write_evals(triggers=bad)
        found = messages(report)
        self.assertTrue(any("boolean 'should_trigger'" in m for m in found))
        self.assertTrue(any("duplicate" in m for m in found))
        report = self.write_evals(triggers=self.triggers(true_count=3))
        self.assertTrue(any("only 3 queries with should_trigger=true" in m for m in messages(report, "warning")))

    def test_evals_text_follows_writing_rules(self):
        report = self.write_evals({"skill_name": "demo-skill", "evals": [self.case(1, expected_output=f"Fast {EM_DASH} light")]})
        self.assertTrue(any("em dash" in m for m in messages(report)))


class CommandLineTests(unittest.TestCase):
    def run_main(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = vs.main(list(args))
        return code, out.getvalue()

    def test_exit_codes(self):
        good = SkillFixture(self)
        code, out = self.run_main("--no-evals", str(good.dir))
        self.assertEqual(code, 0, out)
        self.assertIn("0 error(s)", out)

        warned = SkillFixture(self, frontmatter="name: demo-skill\ndescription: Formats release notes nicely.\n")
        self.assertEqual(self.run_main("--no-evals", str(warned.dir))[0], 0)
        self.assertEqual(self.run_main("--no-evals", "--strict", str(warned.dir))[0], 1)

        broken = SkillFixture(self, name="Bad_Name")
        code, out = self.run_main("--no-evals", str(broken.dir))
        self.assertEqual(code, 1)
        self.assertIn("FAILED", out)


if __name__ == "__main__":
    unittest.main()
