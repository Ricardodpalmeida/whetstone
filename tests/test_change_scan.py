"""Tests for skills/whetstone/scripts/change_scan.py (standard library only).

Run from the repository root:  python3 -m unittest discover -s tests

Every credential-shaped string below is fake and is assembled at run time, so this
file never contains a literal token that a secret scanner or push protection would
mistake for a real one.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "whetstone" / "scripts" / "change_scan.py"

sys.dont_write_bytecode = True  # keep __pycache__ out of the installable skill folder
_spec = importlib.util.spec_from_file_location("change_scan", SCRIPT)
cs = importlib.util.module_from_spec(_spec)
sys.modules["change_scan"] = cs  # dataclasses resolve annotations through sys.modules
_spec.loader.exec_module(cs)

AWS_ID = "AK" + "IA" + "Q7ZK3M9TLW4XPB2N"
AWS_DOC_SAMPLE = "AK" + "IA" + "IOSFODNN7" + "EXAMPLE"
GITHUB_TOKEN = "gh" + "p_" + "aB3dE5fG7h" * 4
STRONG_PASSWORD = "Xk9#mP2$" + "vLq8!wZ"
STRONG_VALUE = "Hq7Lm2Zp" + "9Xw4Kd8R"
PEM_HEADER = "-----BEGIN " + "RSA PRIVATE KEY-----"


def git_diff(path, added=(), removed=(), status="modified", start=1):
    """Build a minimal git-style unified diff for one file."""
    lines = [f"diff --git a/{path} b/{path}"]
    if status == "added":
        lines += ["new file mode 100644", "--- /dev/null", f"+++ b/{path}"]
    elif status == "deleted":
        lines += ["deleted file mode 100644", f"--- a/{path}", "+++ /dev/null"]
    else:
        lines += [f"--- a/{path}", f"+++ b/{path}"]
    if added or removed:
        lines.append(f"@@ -{start},{len(removed)} +{start},{len(added)} @@")
        lines += ["-" + text for text in removed]
        lines += ["+" + text for text in added]
    return "\n".join(lines) + "\n"


def changes_for(*diffs):
    return cs.parse_unified_diff("".join(diffs))


def tier_of(*diffs):
    tier, reasons, notes = cs.suggest_tier(changes_for(*diffs))
    return tier, [r["label"] for r in reasons], notes


def secrets_in(*diffs):
    return cs.find_secrets(changes_for(*diffs))


def weakening_in(*diffs):
    return cs.find_weakening(changes_for(*diffs))


class ParseDiffTests(unittest.TestCase):
    def test_git_diff_with_two_files(self):
        text = git_diff("src/app.py", added=["b = 2", "c = 3"], removed=["a = 1"], start=10) + git_diff(
            "README.md", added=["Hello"], status="added"
        )
        changes = cs.parse_unified_diff(text)
        self.assertEqual([c.path for c in changes], ["src/app.py", "README.md"])
        self.assertEqual(changes[0].added, [(10, "b = 2"), (11, "c = 3")])
        self.assertEqual(changes[0].removed, [(10, "a = 1")])
        self.assertEqual(changes[1].status, "added")

    def test_content_that_looks_like_headers_stays_in_the_hunk(self):
        text = (
            "diff --git a/q.sql b/q.sql\n--- a/q.sql\n+++ b/q.sql\n"
            "@@ -1,2 +1,2 @@\n--- old comment\n-select 1;\n+++ counter\n+select 2;\n"
            "\\ No newline at end of file\n"
        )
        (change,) = cs.parse_unified_diff(text)
        self.assertEqual(change.path, "q.sql")
        self.assertEqual([t for _, t in change.removed], ["-- old comment", "select 1;"])
        self.assertEqual([t for _, t in change.added], ["++ counter", "select 2;"])

    def test_deleted_and_renamed_files(self):
        text = git_diff("tests/test_old.py", removed=["def test_x(): pass"], status="deleted") + (
            "diff --git a/src/a.py b/src/b.py\nsimilarity index 100%\nrename from src/a.py\nrename to src/b.py\n"
        )
        deleted, renamed = cs.parse_unified_diff(text)
        self.assertEqual((deleted.path, deleted.status), ("tests/test_old.py", "deleted"))
        self.assertEqual((renamed.old_path, renamed.path, renamed.status), ("src/a.py", "src/b.py", "renamed"))

    def test_plain_unified_diff_without_git_headers(self):
        text = (
            "--- a/one.txt\t2026-01-01\n+++ b/one.txt\t2026-01-02\n@@ -1 +1 @@\n-x\n+y\n"
            "--- a/two.py\n+++ b/two.py\n@@ -3,0 +4,1 @@\n+z = 1\n"
        )
        changes = cs.parse_unified_diff(text)
        self.assertEqual([c.path for c in changes], ["one.txt", "two.py"])
        self.assertEqual(changes[1].added, [(4, "z = 1")])


class TierTests(unittest.TestCase):
    def test_agent_instruction_files_are_not_trivial_documentation(self):
        for path in ("AGENTS.md", "CLAUDE.md", "skills/demo/SKILL.md", "src/AGENTS.md"):
            with self.subTest(path=path):
                tier, _, _ = tier_of(git_diff(path, added=["Change agent behaviour."]))
                self.assertEqual(tier, 2)
        self.assertEqual(tier_of(git_diff("docs/README.md", added=["Fix spelling."]))[0], 0)

    def test_documentation_only_is_t0(self):
        tier, labels, _ = tier_of(git_diff("README.md", added=["Fix typo"]), git_diff("docs/auth.md", added=["x"]))
        self.assertEqual(tier, 0)
        self.assertEqual(labels, ["documentation only"])

    def test_code_change_is_t1(self):
        tier, labels, _ = tier_of(git_diff("src/report.py", added=["total = sum(rows)"]), git_diff("README.md", added=["x"]))
        self.assertEqual(tier, 1)
        self.assertEqual(labels, ["code or configuration change"])

    def test_txt_files_outside_docs_are_not_documentation(self):
        self.assertFalse(cs.is_doc_path("CMakeLists.txt"))
        self.assertFalse(cs.is_doc_path("requirements.txt"))
        self.assertTrue(cs.is_doc_path("LICENSE"))
        self.assertTrue(cs.is_doc_path("docs/notes.txt"))

    def test_dependency_manifest_is_t2(self):
        tier, labels, _ = tier_of(git_diff("requirements.txt", added=["httpx==0.27.2"]))
        self.assertEqual(tier, 2)
        self.assertIn("dependency manifest or lockfile", labels)

    def test_auth_paths_are_t3_including_split_words(self):
        for path in ("src/auth/login.py", "web/src/SignInButton.tsx", "app/sign_in.py", "api/payments/refund.cs"):
            with self.subTest(path=path):
                self.assertEqual(tier_of(git_diff(path, added=["x = 1"]))[0], 3)

    def test_tests_about_auth_are_not_t3(self):
        self.assertEqual(tier_of(git_diff("tests/test_auth.py", added=["def test_login(): pass"]))[0], 1)

    def test_auth_code_added_or_removed_is_t3(self):
        self.assertEqual(tier_of(git_diff("src/api.py", added=["claims = jwt.decode(token, key)"]))[0], 3)
        self.assertEqual(tier_of(git_diff("src/views.py", removed=["@login_required"]))[0], 3)
        self.assertEqual(tier_of(git_diff("src/client.py", added=["requests.get(url, verify=False)"]))[0], 3)

    def test_migrations(self):
        additive = git_diff("migrations/0002_add_email.py", added=["op.add_column('users', sa.Column('email'))"])
        destructive = git_diff("db/migrate/0003_drop.sql", added=["ALTER TABLE users DROP COLUMN fullname;"])
        orm_drop = git_diff("alembic/versions/0004.py", added=["    op.drop_column('users', 'fullname')"])
        self.assertEqual(tier_of(additive)[0], 2)
        self.assertEqual(tier_of(destructive)[0], 3)
        self.assertEqual(tier_of(orm_drop)[0], 3)

    def test_environment_files(self):
        self.assertEqual(tier_of(git_diff(".env", added=["DEBUG=1"]))[0], 3)
        self.assertEqual(tier_of(git_diff("config/prod.env", added=["DEBUG=1"]))[0], 3)
        self.assertEqual(tier_of(git_diff(".env.example", added=["API_KEY="]))[0], 1)

    def test_pipelines_build_infra_and_contracts_are_t2(self):
        for path in (".github/workflows/ci.yml", "Makefile", "infra/main.bicep", "Dockerfile", "api/openapi.yaml"):
            with self.subTest(path=path):
                self.assertEqual(tier_of(git_diff(path, added=["x: 1"]))[0], 2)

    def test_prompt_files_are_t2(self):
        tier, labels, _ = tier_of(git_diff("app/prompts/system.md", added=["You are a helpful assistant."]))
        self.assertEqual(tier, 2)
        self.assertIn("language model prompt or agent instructions", labels)

    def test_content_triggers_in_code(self):
        self.assertEqual(tier_of(git_diff("src/sync.py", added=["resp = httpx.get(url, timeout=5)"]))[0], 2)
        self.assertEqual(tier_of(git_diff("src/load.js", added=['const r = await fetch("/api")']))[0], 2)
        self.assertEqual(tier_of(git_diff("src/bot.py", added=["from anthropic import Anthropic"]))[0], 2)
        self.assertEqual(tier_of(git_diff("src/models.py", added=["date_of_birth = Column(Date)"]))[0], 2)

    def test_ui_and_lint_notes(self):
        _, _, notes = tier_of(git_diff("web/Card.tsx", added=["<div/>"]), git_diff(".eslintrc.json", added=["{}"]))
        self.assertTrue(any("accessibility" in n for n in notes))
        self.assertTrue(any("relaxed" in n for n in notes))

    def test_test_path_detection(self):
        for path in ("tests/x.py", "src/test_x.py", "pkg/x_test.go", "web/a.spec.ts", "src/FooTests.cs", "conftest.py"):
            with self.subTest(path=path):
                self.assertTrue(cs.is_test_path(path))
        for path in ("src/latest.java", "src/contest.py", "src/SpecialOffer.cs", "src/inspector.py"):
            with self.subTest(path=path):
                self.assertFalse(cs.is_test_path(path))


class WeakeningTests(unittest.TestCase):
    def test_skip_focus_and_deleted_tests(self):
        weakening, _ = weakening_in(
            git_diff("tests/test_api.py", added=["@pytest.mark.skip(reason='flaky')"]),
            git_diff("web/cart.test.ts", added=["it.only('adds', () => {})"]),
            git_diff("tests/test_old.py", removed=["def test_x(): assert f()"], status="deleted"),
        )
        kinds = sorted(f.kind for f in weakening)
        self.assertEqual(kinds, ["focused test added", "skip marker added", "test file deleted"])

    def test_fit_in_python_tests_is_not_a_focus_marker(self):
        weakening, _ = weakening_in(git_diff("tests/test_model.py", added=["    model.fit(x, y)", "    assert model"]))
        self.assertEqual(weakening, [])

    def test_net_assertion_removal(self):
        diff = git_diff(
            "tests/test_calc.py",
            removed=["    assert add(1, 2) == 3", "    assert add(-1, 1) == 0"],
            added=["    assert add(1, 2) == 3"],
        )
        weakening, _ = weakening_in(diff)
        self.assertEqual([f.kind for f in weakening], ["assertions removed"])

    def test_retries_flagged_only_in_test_configuration(self):
        weakening, _ = weakening_in(git_diff("playwright.config.ts", added=["  retries: 2,"]))
        self.assertEqual([f.kind for f in weakening], ["test retries added"])
        weakening, _ = weakening_in(git_diff("src/http.ts", added=["const opts = { retries: 3 };"]))
        self.assertEqual(weakening, [])

    def test_suppressions_in_code_but_not_in_docs(self):
        _, suppressions = weakening_in(
            git_diff("src/a.py", added=["x = f()  # type: ignore"]),
            git_diff("docs/guide.md", added=["Avoid `# type: ignore` comments."]),
        )
        self.assertEqual([(f.path, f.detail) for f in suppressions], [("src/a.py", "# type: ignore")])

    def test_coverage_threshold_lowered(self):
        weakening, _ = weakening_in(git_diff("pyproject.toml", removed=["fail_under = 90"], added=["fail_under = 80"]))
        self.assertEqual([f.detail for f in weakening], ["fail_under: 90 -> 80"])

    def test_details_never_include_the_rest_of_the_line(self):
        _, suppressions = weakening_in(git_diff("src/a.py", added=[f'KEY = "{STRONG_VALUE}"  # noqa']))
        self.assertEqual(suppressions[0].detail, "# noqa")


class SecretTests(unittest.TestCase):
    def test_provider_tokens_are_found_and_redacted(self):
        findings = secrets_in(git_diff("src/settings.py", added=[f'AWS = "{AWS_ID}"', f"TOKEN = '{GITHUB_TOKEN}'"]))
        self.assertEqual([f.kind for f in findings], ["AWS access key ID", "GitHub token"])
        for finding in findings:
            self.assertIn("********", finding.detail)
        rendered = json.dumps([f.as_dict() for f in findings])
        self.assertNotIn(AWS_ID, rendered)
        self.assertNotIn(GITHUB_TOKEN, rendered)

    def test_documented_sample_key_is_ignored(self):
        self.assertEqual(secrets_in(git_diff("docs/aws.md", added=[f"Use {AWS_DOC_SAMPLE} in examples."])), [])

    def test_heuristic_assignment_rules(self):
        flagged = secrets_in(
            git_diff("src/db.py", added=[f'db_password = "{STRONG_PASSWORD}"']),
            git_diff("cmd/main.go", added=[f'apiKey := "{STRONG_VALUE}"']),
            git_diff("src/conf.py", added=[f'password: str = "{STRONG_VALUE}"']),
        )
        self.assertEqual([f.kind for f in flagged], ["credential assigned in code"] * 3)
        ignored = secrets_in(
            git_diff("src/a.py", added=['api_key = "your-api-key-here"']),
            git_diff("src/b.py", added=['password = "password1"']),
            git_diff("src/c.py", added=['token = "${API_TOKEN}"']),
            git_diff("src/d.py", added=['if password == "Zq8#Lm2kWp9x":']),
            git_diff("src/e.py", added=[f'token = "{STRONG_VALUE}"  # pragma: allowlist secret']),
        )
        self.assertEqual(ignored, [])

    def test_heuristics_skip_tests_but_provider_rules_do_not(self):
        findings = secrets_in(
            git_diff("tests/test_db.py", added=[f'password = "{STRONG_PASSWORD}"', f'key = "{AWS_ID}"'])
        )
        self.assertEqual([f.kind for f in findings], ["AWS access key ID"])

    def test_connection_urls_and_config_files(self):
        findings = secrets_in(
            git_diff("src/db.py", added=[f'URL = "postgresql://app:{STRONG_PASSWORD}@db:5432/app"']),
            git_diff("src/ok.py", added=['URL = "postgresql://app:${DB_PASSWORD}@db/app"']),
            git_diff(".env", added=[f"STRIPE_SECRET={STRONG_VALUE}"]),
            git_diff("config/app.yaml", added=[f"  client_secret: {STRONG_VALUE}  # rotated"]),
            git_diff("config/ok.yaml", added=["  password: ${DB_PASSWORD}"]),
        )
        self.assertEqual(
            [(f.kind, f.path) for f in findings],
            [
                ("password in connection URL", "src/db.py"),
                ("credential in configuration file", ".env"),
                ("credential in configuration file", "config/app.yaml"),
            ],
        )

    def test_private_key_header_is_shown_because_it_is_not_the_secret(self):
        (finding,) = secrets_in(git_diff("deploy/key.txt", added=[PEM_HEADER]))
        self.assertEqual(finding.detail, PEM_HEADER)

    def test_redact_keeps_only_the_public_prefix(self):
        self.assertEqual(cs.redact("abcdefghij", 3), "abc******** (10 chars)")
        self.assertEqual(cs.redact("abcd", 3), "******** (4 chars)")


class CommandLineTests(unittest.TestCase):
    def run_main(self, diff_text, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "change.diff")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(diff_text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cs.main(["--diff-file", path, *extra])
        return code, out.getvalue()

    def test_clean_change_exits_zero(self):
        code, out = self.run_main(git_diff("README.md", added=["Typo fixed"]))
        self.assertEqual(code, 0)
        self.assertIn("Suggested minimum tier: T0", out)

    def test_secret_exits_one_without_printing_the_value(self):
        code, out = self.run_main(git_diff("src/a.py", added=[f'K = "{AWS_ID}"']))
        self.assertEqual(code, 1)
        self.assertNotIn(AWS_ID, out)
        self.assertIn("revoke and rotate", out)

    def test_strict_mode_and_json(self):
        diff = git_diff("src/a.py", added=["x = f()  # noqa"])
        self.assertEqual(self.run_main(diff)[0], 0)
        code, out = self.run_main(diff, "--strict", "--json")
        self.assertEqual(code, 1)
        report = json.loads(out)
        self.assertEqual(report["minimum_tier"], "T1")
        self.assertEqual(report["suppressions"][0]["detail"], "# noqa")

    def test_source_options_are_mutually_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            cs.main(["--staged", "--base", "main"])
        self.assertEqual(raised.exception.code, 2)

    def test_script_runs_as_a_program_reading_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--diff-file", "-"],
            input=git_diff("src/a.py", added=[f'K = "{GITHUB_TOKEN}"']),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("GitHub token", result.stdout)
        self.assertNotIn(GITHUB_TOKEN, result.stdout)


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class GitIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Isolate the tests from the user's global and system git configuration.
        cls._saved_env = {k: os.environ.get(k) for k in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")}
        os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"

    @classmethod
    def tearDownClass(cls):
        for key, value in cls._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = self._tmp.name
        self.git("init", "-q")
        self.git("symbolic-ref", "HEAD", "refs/heads/main")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args):
        subprocess.run(
            ["git", "-C", self.repo, "-c", "user.name=Test", "-c", "user.email=test@example.com",
             "-c", "commit.gpgsign=false", *args],
            check=True, capture_output=True, text=True,
        )

    def write(self, rel, text):
        full = os.path.join(self.repo, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)

    def commit_all(self, message="commit"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def test_unreadable_untracked_file_fails_scan(self):
        self.write("settings.txt", "content cannot be read\n")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cs, "open", side_effect=PermissionError("denied"), create=True):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = cs.main(["--repo", self.repo])
        self.assertEqual(code, 2)
        self.assertIn("settings.txt", err.getvalue())
        self.assertNotIn("no blocking findings", out.getvalue())

    def test_textconv_cannot_hide_added_credentials(self):
        self.write(".gitattributes", "*.data diff=hide\n")
        self.write("payload.data", "safe\n")
        self.commit_all()
        self.write("converter.py", "print('redacted')\n")
        converter = Path(self.repo, "converter.py").as_posix()
        executable = Path(sys.executable).as_posix()
        self.git("config", "diff.hide.textconv", f'"{executable}" "{converter}"')
        self.write("payload.data", f"TOKEN = '{GITHUB_TOKEN}'\n")
        changes = cs.collect_changes(self.repo, staged=False, base=None, untracked=False)
        report = cs.build_report(changes, strict=False)
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual([s["kind"] for s in report["secrets"]], ["GitHub token"])

    def test_tracked_and_untracked_changes(self):
        self.write("src/app.py", "x = 1\n")
        self.commit_all()
        self.write("src/app.py", "import httpx\nx = 1\nhttpx.get(url, timeout=5)\n")
        self.write("config/settings.py", f"TOKEN = '{GITHUB_TOKEN}'\n")
        changes = cs.collect_changes(self.repo, staged=False, base=None, untracked=True)
        self.assertEqual(sorted(c.path for c in changes), ["config/settings.py", "src/app.py"])
        report = cs.build_report(changes, strict=False)
        self.assertEqual(report["minimum_tier"], "T2")
        self.assertEqual([s["kind"] for s in report["secrets"]], ["GitHub token"])
        self.assertEqual(report["exit_code"], 1)

    def test_prefix_config_does_not_break_paths(self):
        # "a/app.py" would lose its directory if the scan relied on the default "a/" prefix.
        self.write("a/app.py", "x = 1\n")
        self.commit_all()
        for setting in ("diff.mnemonicPrefix", "diff.noprefix"):
            with self.subTest(setting=setting):
                self.git("config", setting, "true")
                self.write("a/app.py", f"x = '{setting}'\n")
                (change,) = cs.collect_changes(self.repo, staged=False, base=None, untracked=False)
                self.assertEqual(change.path, "a/app.py")
                self.assertEqual(change.added, [(1, f"x = '{setting}'")])
                self.git("config", "--unset", setting)

    def test_staged_scan_ignores_unstaged_and_untracked(self):
        self.write("a.py", "a = 1\n")
        self.write("b.py", "b = 1\n")
        self.commit_all()
        self.write("a.py", "a = 2\n")
        self.write("b.py", "b = 2\n")
        self.write("new.py", "n = 1\n")
        self.git("add", "a.py")
        changes = cs.collect_changes(self.repo, staged=True, base=None, untracked=True)
        self.assertEqual([c.path for c in changes], ["a.py"])

    def test_base_branch_scan(self):
        self.write("a.py", "a = 1\n")
        self.commit_all()
        self.git("checkout", "-q", "-b", "feature")
        self.write("requirements.txt", "httpx==0.27.2\n")
        self.commit_all("add dependency")
        changes = cs.collect_changes(self.repo, staged=False, base="main", untracked=False)
        self.assertEqual([c.path for c in changes], ["requirements.txt"])
        self.assertEqual(cs.suggest_tier(changes)[0], 2)

    def test_scan_from_a_subdirectory_sees_the_whole_repository(self):
        self.write("pkg/sub/mod.py", "m = 1\n")
        self.commit_all()
        self.write("root_new.py", "r = 1\n")
        changes = cs.collect_changes(os.path.join(self.repo, "pkg"), staged=False, base=None, untracked=True)
        self.assertEqual([c.path for c in changes], ["root_new.py"])

    def test_repository_without_commits(self):
        self.write("a.py", "a = 1\n")
        self.git("add", "a.py")
        self.write("b.md", "notes\n")
        changes = cs.collect_changes(self.repo, staged=False, base=None, untracked=True)
        self.assertEqual(sorted(c.path for c in changes), ["a.py", "b.md"])

    def test_outside_a_repository_exits_two(self):
        with tempfile.TemporaryDirectory() as not_repo:
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = cs.main(["--repo", not_repo])
        self.assertEqual(code, 2)
        self.assertIn("change_scan:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
