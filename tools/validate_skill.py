#!/usr/bin/env python3
"""Validate Agent Skill folders and their evals before they are installed or shared.

Standard library only. Run from anywhere:

  python3 tools/validate_skill.py                     # every skill under skills/, plus evals/
  python3 tools/validate_skill.py skills/whetstone    # one skill, plus evals/ when present
  python3 tools/validate_skill.py --no-evals skills/whetstone
  python3 tools/validate_skill.py --strict            # warnings fail the run too

The checks follow the Agent Skills specification (https://agentskills.io/specification),
Anthropic's skill authoring best practices, the loaders of Claude Code and OpenClaw, and
this repository's writing rules. Errors exit with status 1; warnings are printed but only
fail the run with --strict.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
RESERVED_NAME_WORDS = ("anthropic", "claude")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_COMPATIBILITY = 500
LONG_DESCRIPTION = 512          # every installed skill pays for its description in every session
LONG_FIRST_SENTENCE = 160       # OpenClaw advises one line under 160 characters
MAX_BODY_LINES = 500            # Anthropic: keep the SKILL.md body under 500 lines
WARN_BODY_LINES = 300
WARN_BODY_TOKENS = 5000         # Agent Skills spec: under 5,000 tokens recommended
TOC_THRESHOLD = 100             # reference files longer than this need a table of contents
WARN_REFERENCE_LINES = 300
STRAY_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db", ".pytest_cache", ".mypy_cache"}

FORBIDDEN_CHARS = {chr(0x2014): "em dash (U+2014)", chr(0x2013): "en dash (U+2013)"}
BOM = chr(0xFEFF)
BOLD_LABEL_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*[^*]+?(?::\*\*|\*\*\s*:)")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
INLINE_CODE_RE = re.compile(r"(`+).+?\1")
LINK_RE = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+.*)?$")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".sh", ".ps1", ".js", ".ts", ".html", ".css", ".csv"}


# --------------------------------------------------------------------------- reporting

@dataclass
class Issue:
    level: str  # "error" or "warning"
    path: Path
    line: Optional[int]
    message: str

    def render(self) -> str:
        try:
            shown = os.path.relpath(self.path)
        except ValueError:  # different drive on Windows
            shown = str(self.path)
        where = f"{shown}:{self.line}" if self.line else shown
        return f"{self.level}: {where}: {self.message}"


@dataclass
class Report:
    issues: List[Issue] = field(default_factory=list)

    def error(self, path: Path, line: Optional[int], message: str) -> None:
        self.issues.append(Issue("error", path, line, message))

    def warn(self, path: Path, line: Optional[int], message: str) -> None:
        self.issues.append(Issue("warning", path, line, message))

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.level == "warning"]


# --------------------------------------------------------------------------- frontmatter

class FrontmatterError(ValueError):
    def __init__(self, line: int, message: str):
        super().__init__(message)
        self.line = line


@dataclass
class FieldValue:
    value: object                 # str, list of str, or dict of str to FieldValue
    line: int                     # line number in SKILL.md
    plain: bool = False           # an unquoted scalar
    yaml_type: str = "str"        # what a YAML loader would turn a plain scalar into


DQ_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$')
SQ_RE = re.compile(r"^'((?:[^']|'')*)'\s*(?:#.*)?$")
KEY_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*):(?:[ \t]+(.*?))?\s*$")
INT_RE = re.compile(r"^[-+]?(?:0|[1-9][0-9_]*|0x[0-9a-fA-F_]+|0o[0-7_]+)$")
FLOAT_RE = re.compile(r"^[-+]?(?:\.[0-9]+|[0-9][0-9_]*(?:\.[0-9_]*)?)(?:[eE][-+]?[0-9]+)?$|^[-+]?\.(?:inf|Inf|INF)$|^\.(?:nan|NaN|NAN)$")
DATE_RE = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}(?:[Tt ].*)?$")
BOOL_NULL = {"true", "false", "yes", "no", "on", "off", "null", "~"}


def _plain_type(raw: str) -> str:
    lowered = raw.lower()
    if lowered in BOOL_NULL or raw == "":
        return "boolean or null"
    if INT_RE.match(raw):
        return "integer"
    if FLOAT_RE.match(raw):
        return "number"
    if DATE_RE.match(raw):
        return "date"
    return "str"


def _parse_scalar(raw: str, line: int) -> FieldValue:
    match = DQ_RE.match(raw)
    if match:
        try:
            value = json.loads('"' + match.group(1) + '"')
        except ValueError:
            raise FrontmatterError(line, "unsupported escape in a double-quoted value")
        return FieldValue(value, line)
    match = SQ_RE.match(raw)
    if match:
        return FieldValue(match.group(1).replace("''", "'"), line)
    if raw[:1] in ('"', "'"):
        raise FrontmatterError(line, "quoted value is not closed on the same line")
    if raw[:1] in tuple(",[]{}#&*!|>%@`"):
        raise FrontmatterError(line, f"a plain value cannot start with {raw[0]!r}; quote the value")
    if raw[:1] in ("-", "?", ":") and (len(raw) == 1 or raw[1] == " "):
        raise FrontmatterError(line, f"a plain value cannot start with {raw[:2]!r}; quote the value")
    if ": " in raw or raw.endswith(":"):
        raise FrontmatterError(line, "a plain value contains ': ', which YAML rejects; quote the value or reword it")
    if " #" in raw:
        raise FrontmatterError(line, "' #' starts a YAML comment, so the rest of the value would be dropped; quote the value")
    return FieldValue(raw, line, plain=True, yaml_type=_plain_type(raw))


def _block_lines(lines: List[str], start: int) -> Tuple[List[Tuple[int, str]], int]:
    """Collect the indented (or blank) lines after a key, returning them and the next index."""
    collected: List[Tuple[int, str]] = []
    index = start
    while index < len(lines) and (lines[index].startswith((" ", "\t")) or not lines[index].strip()):
        collected.append((index, lines[index]))
        index += 1
    while collected and not collected[-1][1].strip():
        collected.pop()
    return collected, index


def parse_frontmatter(lines: List[str], first_line: int = 2) -> Dict[str, FieldValue]:
    """Parse the small YAML subset that skill frontmatter needs, with line numbers.

    Supported: scalars (plain, single or double quoted), block scalars (| and >),
    one level of mapping (for metadata) and block lists of scalars.
    """
    fields: Dict[str, FieldValue] = {}
    index = 0
    while index < len(lines):
        raw = lines[index]
        number = first_line + index
        if not raw.strip() or raw.lstrip().startswith("#"):
            index += 1
            continue
        if raw.startswith((" ", "\t")):
            raise FrontmatterError(number, "unexpected indentation")
        match = KEY_RE.match(raw)
        if not match:
            raise FrontmatterError(number, "expected 'key: value'")
        key, value = match.group(1), match.group(2)
        if key in fields:
            raise FrontmatterError(number, f"duplicate key '{key}'")
        block, after = _block_lines(lines, index + 1)
        for block_index, block_line in block:
            if block_line[: len(block_line) - len(block_line.lstrip())].count("\t"):
                raise FrontmatterError(first_line + block_index, "tabs are not allowed in YAML indentation")
        if value and value[0] in "|>" and re.match(r"^[|>][-+]?\s*(?:#.*)?$", value):
            texts = [text.strip() for _, text in block]
            folded = " ".join(t for t in texts if t) if value[0] == ">" else "\n".join(texts)
            fields[key] = FieldValue(folded, number)
            index = after
            continue
        if value:
            if block:
                raise FrontmatterError(first_line + block[0][0], f"unexpected indented line after '{key}'")
            fields[key] = _parse_scalar(value, number)
            index += 1
            continue
        if not block:
            fields[key] = FieldValue("", number, plain=True, yaml_type="boolean or null")
            index = after
            continue
        if block[0][1].lstrip().startswith("- ") or block[0][1].strip() == "-":
            items = []
            for block_index, block_line in block:
                stripped = block_line.strip()
                if not stripped:
                    continue
                if not stripped.startswith("-"):
                    raise FrontmatterError(first_line + block_index, "mixed list and mapping under one key")
                items.append(_parse_scalar(stripped[1:].strip(), first_line + block_index).value)
            fields[key] = FieldValue(items, number)
        else:
            mapping: Dict[str, FieldValue] = {}
            base_indent = len(block[0][1]) - len(block[0][1].lstrip())
            last_key: Optional[str] = None
            for block_index, block_line in block:
                if not block_line.strip() or block_line.lstrip().startswith("#"):
                    continue
                indent = len(block_line) - len(block_line.lstrip())
                sub_number = first_line + block_index
                if indent > base_indent and last_key is not None:
                    # Deeper nesting (such as an OpenClaw metadata block) is recorded, not parsed.
                    mapping[last_key] = FieldValue({}, mapping[last_key].line, yaml_type="mapping")
                    continue
                if indent != base_indent:
                    raise FrontmatterError(sub_number, "inconsistent indentation inside a mapping")
                sub = KEY_RE.match(block_line.strip())
                if not sub:
                    raise FrontmatterError(sub_number, "expected 'key: value' inside a mapping")
                last_key = sub.group(1)
                if last_key in mapping:
                    raise FrontmatterError(sub_number, f"duplicate key '{key}.{last_key}'")
                sub_value = sub.group(2)
                mapping[last_key] = (
                    _parse_scalar(sub_value, sub_number) if sub_value
                    else FieldValue({}, sub_number, yaml_type="mapping")
                )
            fields[key] = FieldValue(mapping, number, yaml_type="mapping")
        index = after
    return fields


def split_frontmatter(text: str) -> Tuple[List[str], List[str], int]:
    """Return (frontmatter lines, body lines, line number where the body starts)."""
    if text.startswith(BOM):
        raise FrontmatterError(1, "remove the byte order mark at the start of SKILL.md")
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        raise FrontmatterError(1, "SKILL.md must start with a '---' line that opens the frontmatter")
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            return lines[1:index], lines[index + 1:], index + 2
    raise FrontmatterError(1, "frontmatter has no closing '---' line")


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]


def check_frontmatter(skill_dir: Path, skill_md: Path, fields: Dict[str, FieldValue], report: Report) -> Optional[str]:
    unknown = sorted(set(fields) - ALLOWED_KEYS)
    if unknown:
        report.error(skill_md, fields[unknown[0]].line,
                     f"unexpected frontmatter key(s) {', '.join(unknown)}; portable skills allow only "
                     f"{', '.join(sorted(ALLOWED_KEYS))}")

    name_field = fields.get("name")
    name: Optional[str] = None
    if name_field is None:
        report.error(skill_md, 1, "missing required field 'name'")
    elif not isinstance(name_field.value, str) or name_field.yaml_type != "str":
        report.error(skill_md, name_field.line, "'name' must be a string")
    else:
        name = name_field.value
        normalised = unicodedata.normalize("NFKC", name)
        if normalised != name or name != name.strip():
            report.error(skill_md, name_field.line, "'name' has surrounding spaces or characters that change under NFKC normalisation")
        if not 1 <= len(name) <= MAX_NAME:
            report.error(skill_md, name_field.line, f"'name' must be 1 to {MAX_NAME} characters (found {len(name)})")
        if not NAME_RE.match(name):
            report.error(skill_md, name_field.line,
                         "'name' must use lowercase ASCII letters, digits and single hyphens, and must not start or end with a hyphen")
        if name != skill_dir.name:
            report.error(skill_md, name_field.line, f"'name' ({name}) must match the folder name ({skill_dir.name})")
        for word in RESERVED_NAME_WORDS:
            if word in name:
                report.error(skill_md, name_field.line, f"'name' must not contain the reserved word '{word}'")

    desc_field = fields.get("description")
    if desc_field is None:
        report.error(skill_md, 1, "missing required field 'description'")
    elif not isinstance(desc_field.value, str) or desc_field.yaml_type != "str":
        report.error(skill_md, desc_field.line, "'description' must be a string")
    else:
        desc = desc_field.value
        line = desc_field.line
        if not desc.strip():
            report.error(skill_md, line, "'description' must not be empty")
        if len(desc) > MAX_DESCRIPTION:
            report.error(skill_md, line, f"'description' is {len(desc)} characters; the limit is {MAX_DESCRIPTION}")
        if "\n" in desc.strip():
            report.error(skill_md, line, "'description' must be a single line")
        if "<" in desc or ">" in desc:
            report.error(skill_md, line, "'description' must not contain angle brackets or XML tags")
        if len(desc) > LONG_DESCRIPTION:
            report.warn(skill_md, line, f"'description' is {len(desc)} characters; every session pays for it, so keep it near or under {LONG_DESCRIPTION}")
        first = first_sentence(desc)
        if len(first) > LONG_FIRST_SENTENCE:
            report.warn(skill_md, line, f"the first sentence of 'description' is {len(first)} characters; keep it under {LONG_FIRST_SENTENCE} so a truncated listing still makes sense")
        if not re.search(r"\bwhen\b", desc, re.IGNORECASE):
            report.warn(skill_md, line, "'description' should say when to use the skill, for example 'Use when ...'")
        if re.search(r"\b(I|I'm|my)\b", desc) or re.search(r"\byou(r|rs)?\b", desc, re.IGNORECASE):
            report.warn(skill_md, line, "write 'description' in the third person or as an instruction, not as 'I' or 'you'")

    compat = fields.get("compatibility")
    if compat is not None:
        if not isinstance(compat.value, str) or compat.yaml_type != "str" or not compat.value.strip():
            report.error(skill_md, compat.line, "'compatibility' must be a non-empty string")
        elif len(compat.value) > MAX_COMPATIBILITY:
            report.error(skill_md, compat.line, f"'compatibility' is {len(compat.value)} characters; the limit is {MAX_COMPATIBILITY}")

    lic = fields.get("license")
    if lic is not None and (not isinstance(lic.value, str) or lic.yaml_type != "str" or not lic.value.strip()):
        report.error(skill_md, lic.line, "'license' must be a non-empty string")

    meta = fields.get("metadata")
    if meta is not None:
        if not isinstance(meta.value, dict):
            report.error(skill_md, meta.line, "'metadata' must be a mapping of string keys to string values")
        else:
            for sub_key, sub in meta.value.items():
                if sub.yaml_type == "mapping":
                    report.warn(skill_md, sub.line,
                                f"'metadata.{sub_key}' is a nested mapping; the specification expects string values "
                                "(an OpenClaw metadata.openclaw block is the usual exception)")
                elif not isinstance(sub.value, str) or sub.yaml_type != "str":
                    report.error(skill_md, sub.line,
                                 f"'metadata.{sub_key}' would load as a {sub.yaml_type}; quote it so it stays a string")

    tools = fields.get("allowed-tools")
    if tools is not None:
        if not isinstance(tools.value, str):
            report.error(skill_md, tools.line, "'allowed-tools' must be a space-separated string")
        report.warn(skill_md, tools.line, "'allowed-tools' is experimental and agents support it unevenly")
    return name


# --------------------------------------------------------------------------- markdown

def github_slug(text: str) -> str:
    """Approximate GitHub's heading anchors: lower case, punctuation removed, spaces to hyphens."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text).replace("`", "").strip().lower()
    kept = [ch for ch in text if ch in " -" or unicodedata.category(ch)[0] in "LMN" or unicodedata.category(ch) == "Pc"]
    return "".join(kept).replace(" ", "-")


@dataclass
class MarkdownFile:
    path: Path
    lines: List[str]
    headings: List[Tuple[int, int, str, str]]  # (line, level, text, slug)
    links: List[Tuple[int, str]]               # (line, target)

    @property
    def slugs(self) -> set:
        return {slug for _, _, _, slug in self.headings}


def read_markdown(path: Path) -> MarkdownFile:
    lines = path.read_text(encoding="utf-8").splitlines()
    headings: List[Tuple[int, int, str, str]] = []
    links: List[Tuple[int, str]] = []
    seen: Dict[str, int] = {}
    fence: Optional[str] = None
    for number, line in enumerate(lines, start=1):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker[0] * 3
            elif marker.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue
        heading = HEADING_RE.match(line)
        if heading:
            text = heading.group(2)
            slug = github_slug(text)
            if slug in seen:
                seen[slug] += 1
                slug = f"{slug}-{seen[slug]}"
            else:
                seen[slug] = 0
            headings.append((number, len(heading.group(1)), text, slug))
        scrubbed = INLINE_CODE_RE.sub("", line)
        for match in LINK_RE.finditer(scrubbed):
            links.append((number, match.group(1)))
        ref = REF_DEF_RE.match(scrubbed)
        if ref:
            links.append((number, ref.group(1)))
    return MarkdownFile(path, lines, headings, links)


def check_links(skill_dir: Path, docs: Dict[Path, MarkdownFile], report: Report) -> Dict[Path, set]:
    """Check every link in every Markdown file; return, per file, the skill files it links to."""
    linked: Dict[Path, set] = {}
    root = skill_dir.resolve()
    for path, doc in docs.items():
        targets = linked.setdefault(path, set())
        for line, target in doc.links:
            if target.startswith("//") or SCHEME_RE.match(target):
                if target.lower().startswith("http://"):
                    report.warn(path, line, f"use https for {target}")
                continue
            if "\\" in target:
                report.error(path, line, f"use forward slashes in link paths: {target}")
                continue
            file_part, _, anchor = target.partition("#")
            if file_part:
                resolved = (path.parent / unquote(file_part)).resolve()
                try:
                    resolved.relative_to(root)
                except ValueError:
                    report.error(path, line, f"link leaves the skill folder, which breaks once the skill is installed: {target}")
                    continue
                if not resolved.exists():
                    report.error(path, line, f"broken link: {target}")
                    continue
                targets.add(resolved)
            else:
                resolved = path.resolve()
            if anchor:
                target_doc = docs.get(resolved)
                if target_doc is None:
                    if resolved.suffix == ".md":
                        report.error(path, line, f"cannot check the anchor in {target}")
                    continue
                if anchor not in target_doc.slugs:
                    report.error(path, line, f"no heading matches the anchor '#{anchor}' in {target or path.name}")
    return linked


def check_contents(path: Path, doc: MarkdownFile, report: Report) -> None:
    """Long files need a 'Contents' section first, listing every other second-level heading."""
    if len(doc.lines) <= TOC_THRESHOLD:
        return
    h2 = [(line, text, slug) for line, level, text, slug in doc.headings if level == 2]
    if not h2 or h2[0][1].strip().lower() not in {"contents", "table of contents"}:
        report.error(path, None, f"{len(doc.lines)} lines long but does not open with a '## Contents' section")
        return
    start = h2[0][0]
    end = h2[1][0] if len(h2) > 1 else len(doc.lines) + 1
    toc_text = "\n".join(doc.lines[start:end - 1])
    for line, text, slug in h2[1:]:
        if f"(#{slug})" not in toc_text:
            report.error(path, line, f"the Contents section does not link to '## {text}'")


def check_text_rules(path: Path, report: Report) -> None:
    """Repository writing rules: no em or en dashes; no '**Label:** text' bullets in Markdown."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        report.error(path, None, "file is not valid UTF-8")
        return
    fence: Optional[str] = None
    escapes = path.suffix in (".json", ".py")  # a backslash-u escape of the code point yields the same character
    for number, line in enumerate(text.splitlines(), start=1):
        for char, label in FORBIDDEN_CHARS.items():
            escaped = "\\u" + format(ord(char), "04x")
            if char in line or (escapes and escaped in line.lower()):
                report.error(path, number, f"contains an {label}; use a comma, colon, parentheses or a new sentence")
        if path.suffix != ".md":
            continue
        fence_match = FENCE_RE.match(line)
        if fence_match:
            fence = None if fence else fence_match.group(1)[0] * 3
            continue
        if fence is None and BOLD_LABEL_BULLET_RE.match(line):
            report.error(path, number, "bullet uses the '**Label:** description' pattern; write a plain sentence or use a table")


# --------------------------------------------------------------------------- skill

def validate_skill(skill_dir: Path, report: Report) -> Optional[str]:
    skill_dir = skill_dir.resolve()
    if not skill_dir.is_dir():
        report.error(skill_dir, None, "not a directory")
        return None
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file() or "SKILL.md" not in os.listdir(skill_dir):
        report.error(skill_dir, None, "missing required file SKILL.md (the name is case-sensitive)")
        return None

    text = skill_md.read_text(encoding="utf-8")
    name: Optional[str] = None
    body: List[str] = []
    try:
        fm_lines, body, _ = split_frontmatter(text)
        fields = parse_frontmatter(fm_lines)
        name = check_frontmatter(skill_dir, skill_md, fields, report)
    except FrontmatterError as exc:
        report.error(skill_md, exc.line, f"frontmatter: {exc} (Claude Code loads a skill with invalid YAML but drops every field)")

    if body:
        if len(body) > MAX_BODY_LINES:
            report.error(skill_md, None, f"body is {len(body)} lines; keep it under {MAX_BODY_LINES} and move detail into references")
        elif len(body) > WARN_BODY_LINES:
            report.warn(skill_md, None, f"body is {len(body)} lines; consider moving detail into references")
        tokens = len("\n".join(body)) // 4
        if tokens > WARN_BODY_TOKENS:
            report.warn(skill_md, None, f"body is about {tokens} tokens; the specification recommends under {WARN_BODY_TOKENS}")
    elif name is not None:
        report.error(skill_md, None, "SKILL.md has no instructions after the frontmatter")

    all_files = sorted(p for p in skill_dir.rglob("*") if p.is_file())
    for path in sorted(skill_dir.rglob("*")):
        if any(part in STRAY_NAMES for part in path.relative_to(skill_dir).parts[:-1]):
            continue  # inside a folder that is already reported
        if path.name in STRAY_NAMES or path.suffix == ".pyc":
            report.warn(path, None, "generated or system file; remove it before installing or sharing the skill")

    docs = {p.resolve(): read_markdown(p) for p in all_files if p.suffix == ".md"}
    linked = check_links(skill_dir, docs, report)
    for path, doc in docs.items():
        if path.name != "SKILL.md":
            check_contents(path, doc, report)
            if path.parent.name == "references" and len(doc.lines) > WARN_REFERENCE_LINES:
                report.warn(path, None, f"{len(doc.lines)} lines; consider splitting it by topic")
    for path in all_files:
        if path.suffix in TEXT_SUFFIXES:
            check_text_rules(path, report)

    from_skill_md = linked.get(skill_md.resolve(), set())
    for folder in ("references", "templates", "assets"):
        for path in sorted((skill_dir / folder).rglob("*")) if (skill_dir / folder).is_dir() else []:
            if path.is_file() and path.resolve() not in from_skill_md and path.name not in STRAY_NAMES:
                report.error(path, None, "not linked from SKILL.md, so agents will never find it; link it from the routing table")
            if path.is_file() and len(path.relative_to(skill_dir).parts) > 2:
                report.warn(path, None, "nested more than one level deep; keep supporting files directly under their folder")
    scripts = skill_dir / "scripts"
    if scripts.is_dir():
        for path in sorted(p for p in scripts.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            if path.name not in text:
                report.warn(path, None, "script is not mentioned in SKILL.md")
            if path.suffix == ".py":
                try:
                    compile(path.read_text(encoding="utf-8"), str(path), "exec")
                except SyntaxError as exc:
                    report.error(path, exc.lineno, f"does not compile: {exc.msg}")
    return name


# --------------------------------------------------------------------------- evals

def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_evals(evals_dir: Path, skill_names: List[str], report: Report) -> None:
    evals_path = evals_dir / "evals.json"
    trigger_path = evals_dir / "trigger_queries.json"
    if not evals_path.is_file() and not trigger_path.is_file():
        report.warn(evals_dir, None, "no evals.json or trigger_queries.json found")
        return
    for path in sorted(p for p in evals_dir.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES):
        check_text_rules(path, report)

    if evals_path.is_file():
        try:
            data = json.loads(evals_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            report.error(evals_path, None, f"invalid JSON: {exc}")
            data = None
        if data is not None:
            if not isinstance(data, dict) or not isinstance(data.get("evals"), list) or not data["evals"]:
                report.error(evals_path, None, "expected an object with 'skill_name' and a non-empty 'evals' list")
            else:
                if data.get("skill_name") not in skill_names:
                    report.error(evals_path, None, f"'skill_name' must name a validated skill ({', '.join(skill_names) or 'none'})")
                seen_ids = set()
                for position, case in enumerate(data["evals"], start=1):
                    label = f"eval #{position}"
                    if not isinstance(case, dict):
                        report.error(evals_path, None, f"{label} must be an object")
                        continue
                    case_id = case.get("id")
                    if not isinstance(case_id, (int, str)) or isinstance(case_id, bool):
                        report.error(evals_path, None, f"{label} needs an integer or string 'id'")
                    elif case_id in seen_ids:
                        report.error(evals_path, None, f"{label} reuses id {case_id!r}")
                    else:
                        seen_ids.add(case_id)
                        label = f"eval {case_id!r}"
                    for key in ("prompt", "expected_output"):
                        if not _non_empty_string(case.get(key)):
                            report.error(evals_path, None, f"{label} needs a non-empty '{key}'")
                    assertions = case.get("assertions")
                    if assertions is None:
                        report.warn(evals_path, None, f"{label} has no 'assertions' to grade")
                    elif not isinstance(assertions, list) or not assertions or not all(_non_empty_string(a) for a in assertions):
                        report.error(evals_path, None, f"{label}: 'assertions' must be a non-empty list of strings")
                    for key in ("files", "tags"):
                        value = case.get(key)
                        if value is not None and (not isinstance(value, list) or not all(_non_empty_string(v) for v in value)):
                            report.error(evals_path, None, f"{label}: '{key}' must be a list of strings")
                    files = case.get("files") if isinstance(case.get("files"), list) else []
                    for rel in files:
                        if isinstance(rel, str) and not (evals_dir.parent / rel).exists():
                            report.error(evals_path, None, f"{label}: input file not found: {rel}")
                    unknown = sorted(set(case) - {"id", "prompt", "expected_output", "assertions", "files", "tags"})
                    if unknown:
                        report.warn(evals_path, None, f"{label}: unrecognised key(s) {', '.join(unknown)}")

    if trigger_path.is_file():
        try:
            queries = json.loads(trigger_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            report.error(trigger_path, None, f"invalid JSON: {exc}")
            return
        if not isinstance(queries, list) or not queries:
            report.error(trigger_path, None, "expected a non-empty list of {query, should_trigger} objects")
            return
        texts = set()
        counts = {True: 0, False: 0}
        for position, item in enumerate(queries, start=1):
            if not isinstance(item, dict) or not _non_empty_string(item.get("query")) or not isinstance(item.get("should_trigger"), bool):
                report.error(trigger_path, None, f"query #{position} needs a non-empty 'query' and a boolean 'should_trigger'")
                continue
            if item["query"] in texts:
                report.error(trigger_path, None, f"query #{position} is a duplicate")
            texts.add(item["query"])
            counts[item["should_trigger"]] += 1
        for flag, count in counts.items():
            if count < 8:
                report.warn(trigger_path, None, f"only {count} queries with should_trigger={str(flag).lower()}; aim for 8 to 10 of each")


# --------------------------------------------------------------------------- command line

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Agent Skill folders and their evals.")
    parser.add_argument("skills", nargs="*", type=Path,
                        help="skill folders to check (default: every folder under skills/ with a SKILL.md)")
    parser.add_argument("--evals", type=Path, help="evals folder (default: evals/ at the repository root, when present)")
    parser.add_argument("--no-evals", action="store_true", help="skip the evals checks")
    parser.add_argument("--strict", action="store_true", help="fail on warnings as well as errors")
    args = parser.parse_args(argv)

    skill_dirs = args.skills or sorted(p.parent for p in (REPO_ROOT / "skills").glob("*/SKILL.md"))
    report = Report()
    if not skill_dirs:
        report.error(REPO_ROOT / "skills", None, "no skill folders found")
    names = [n for n in (validate_skill(d, report) for d in skill_dirs) if n]

    evals_dir = args.evals or (REPO_ROOT / "evals")
    if not args.no_evals and (args.evals or evals_dir.is_dir()):
        validate_evals(evals_dir.resolve(), names, report)

    for issue in report.issues:
        print(issue.render())
    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    print(f"validate_skill: {len(skill_dirs)} skill(s) checked, {len(report.errors)} error(s), "
          f"{len(report.warnings)} warning(s): {'FAILED' if failed else 'OK'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
