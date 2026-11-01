#!/usr/bin/env python3
"""Mechanical checks for Agent Skills, keyed to the rule IDs in references/rules.md.

Usage:
    audit_skill.py <path> [<path> ...]

<path> may be a SKILL.md, a skill directory, or any directory containing skills
(searched recursively). Prints, per skill, a stats line and findings as
    SEVERITY  RULE  file:line  message
Findings are candidates: heuristics flag things for a human-quality judgment pass.

Exit codes: 0 no MUST findings, 1 at least one MUST finding, 2 usage error.
Python 3.9+, stdlib only.
"""

import difflib
import json
import importlib.util
import os
import re
import subprocess
import sys
import sysconfig
from pathlib import Path

# Limits and key lists come from rules.json, where each value is pinned to a quote from the
# docs; tools/check_docs_drift.py reports when those quotes or lists change upstream.
RULES_JSON = Path(__file__).resolve().parent.parent / "rules.json"
try:
    _RULES = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    _L = {k: v["value"] for k, v in _RULES["limits"].items()}
    _K = {k: v["value"] for k, v in _RULES["lists"].items()}
    VERIFIED = _RULES["verified"]
    NAME_MAX = _L["name_max"]
    DESC_MAX_PLATFORM = _L["description_max_upload"]
    LISTING_MAX = _L["listing_max"]
    BODY_LINES_MAX = _L["body_lines_max"]
    BODY_TOKENS_MAX = _L["body_tokens_max"]
    TOC_THRESHOLD_LINES = _L["toc_threshold_lines"]
    RESERVED = tuple(_K["reserved_words"])
    KNOWN_KEYS = set(_K["frontmatter_keys"])
    PORTABLE_KEYS = set(_K["portable_keys"])
    EFFORTS = set(_K["effort_levels"])
except (OSError, ValueError, KeyError) as e:
    sys.exit(f"Cannot load rule data from {RULES_JSON}: {e!r}. Reinstall the skill-audit plugin.")
TOC_SEARCH_LINES = 40  # heuristic: a TOC must sit this close to the top to show in a head -100 preview

TEXT_EXT = {".md", ".txt", ".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".json",
            ".yaml", ".yml", ".html", ".css", ".xml", ".csv", ".toml"}
SCRIPT_EXT = {".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts"}
IGNORED_PARTS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

PATH_RE = re.compile(
    r"(?:\$\{CLAUDE_SKILL_DIR\}/|\$\{CLAUDE_PLUGIN_ROOT\}/(?:skills/[\w.-]+/)?)?"
    r"((?:[\w.-]+/)*[\w.-]+\.(?:md|txt|py|sh|js|mjs|cjs|ts|json|ya?ml|html|css|xml|csv|toml|pdf|png|svg|template|tmpl|j2))(?![\w-]|\.\w)"
)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
XML_TAG_RE = re.compile(r"</?[A-Za-z][\w-]*(?:\s[^<>]*)?/?>")
FIRST_PERSON_RE = re.compile(r"\bI(?:'m|'ll| can| will| help)\b|\bmy\b|\byou can\b|\byou should\b|\blets you\b", re.I)
WHEN_RE = re.compile(
    r"\b(use|used|trigger|triggers|invoke|apply|applies)\b[^.]{0,60}\b(when|whenever|if|for|on)\b"
    r"|\bwhen(ever)? (the )?(user|you|working|asked|editing|writing|reviewing)\b",
    re.I,
)
EMPHATIC_RE = re.compile(r"\b(MUST|NEVER|ALWAYS|IMPORTANT|CRITICAL|DO NOT)\b")
SIDE_EFFECT_RE = re.compile(
    r"\b(git push|npm publish|deploy(?:s|ing)?\b|kubectl (?:apply|delete)|terraform apply|"
    r"gh (?:pr create|release create|pr merge)|rm -rf|DROP TABLE|send (?:an? )?(?:email|message)|post to slack)",
    re.I,
)
RUN_REL_RE = re.compile(r"\b(?:python3?|bash|sh|node|uv run|bun|deno run|npx tsx|tsx)\s+((?:\./)?(?:scripts|bin|tools)/[\w./-]+)")
INJECT_RE = re.compile(r"(?:^|\s)!`([^`]+)`")
TIME_RE = re.compile(
    r"\b(?:before|after|until|as of|since|starting|by)\s+"
    r"(?:(?:January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)\.?\s+(?:\d{1,2},?\s+)?20\d\d|Q[1-4]\s*20\d\d|20\d\d)\b"
    r"|\b(?:currently|at the time of writing|the latest version is|recently released)\b",
    re.I,
)
INLINE_CODE_RE = re.compile(r"``.+?``|`[^`]+`")
DOUBLE_CODE_RE = re.compile(r"``.+?``")
SHELL_FENCES = {"", "bash", "sh", "shell", "zsh", "console"}
BACKSLASH_PATH_RE = re.compile(r"(?<![\\\w])[\w.-]+\\[\w.-]+\.(?:md|py|sh|js|ts|json|txt)\b")
GENERIC_NAME_RE = re.compile(r"^(doc|docs|file|notes?|misc|stuff|temp|tmp|untitled|other|new)\d*\.md$", re.I)
SECRET_RES = [
    re.compile(r"sk-ant-[\w-]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bxox[abprs]-[\w-]{10,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(api[_-]?key|secret|access[_-]?token|password|passwd)\b\s*[:=]\s*['\"][^'\"\s$<{]{8,}['\"]"),
]
NETWORK_RE = re.compile(r"\b(curl|wget)\s|requests\.(?:get|post|put|delete)|urllib|httpx|axios|\bfetch\(|https?://[^\s)'\"<>`]+")
URL_RE = re.compile(r"https?://([^/\s)'\"<>`]+)")
ADVERSARIAL_RE = re.compile(
    r"ignore (?:all |any )?(?:previous|prior|safety|system)|"
    r"(?:do not|don't|never) (?:tell|inform|mention (?:this )?to|show) the user|"
    r"without (?:telling|informing|notifying) the user|hide (?:this|these|the) (?:action|command|step|output)s? from|"
    r"(?:base64|encode)[^.]{0,40}(?:send|upload|post)|exfiltrat",
    re.I,
)
OUTSIDE_PATH_RE = re.compile(r"(?<![\w.])\.\./|/Users/[\w.-]+|/home/[\w.-]+|[A-Z]:\\\\")
BARE_EXCEPT_RE = re.compile(r"^\s*except\s*:|^\s*except Exception(?: as \w+)?:\s*\n\s*pass\b", re.M)
HOME_DOMAINS = {"www.w3.org", "platform.claude.com", "code.claude.com", "docs.anthropic.com", "docs.claude.com",
                "github.com", "agentskills.io", "claude.com", "www.anthropic.com"}


SELF = Path(__file__).resolve()


class Finding:
    ORDER = {"MUST": 0, "SHOULD": 1, "CONSIDER": 2}

    def __init__(self, sev, rule, where, msg):
        self.sev, self.rule, self.where, self.msg = sev, rule, where, msg

    def __str__(self):
        return f"{self.sev:<8} {self.rule:<3} {self.where}  {self.msg}"


def est_tokens(text):
    ascii_n = sum(1 for c in text if ord(c) < 128)
    return ascii_n / 4 + (len(text) - ascii_n)


def read(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


# --- frontmatter ----------------------------------------------------------------------

def parse_frontmatter(text):
    """Return (fields, key_lines, body, body_first_line, problems).

    A small YAML subset parser: top-level scalars, block scalars, lists, nested maps
    (kept raw). Also reports constructs a real YAML parser would reject or truncate,
    because Claude Code then loads the skill with empty metadata.
    """
    problems = []
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, {}, text, 1, [("MUST", 1, "no YAML frontmatter: the skill has no description to trigger on")]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, {}, text, 1, [("MUST", 1, "frontmatter is never closed with '---'")]

    fm = lines[1:end]
    fields, key_lines = {}, {}
    i = 0
    while i < len(fm):
        line = fm[i]
        lineno = i + 2
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):(?:[ \t]+(.*?))?[ \t]*$", line)
        if not m:
            if not line.startswith((" ", "\t")):
                problems.append(("MUST", lineno, f"not a 'key: value' line, YAML will not parse: {line.strip()[:60]!r}"))
            i += 1
            continue
        key, raw = m.group(1), m.group(2) or ""
        key_lines[key] = lineno
        i += 1
        cont = []
        while i < len(fm) and (fm[i].startswith((" ", "\t")) or not fm[i].strip()):
            cont.append(fm[i])
            i += 1
        while cont and not cont[-1].strip():
            cont.pop()

        if re.match(r"^[|>][+-]?\d?$", raw):
            stripped = [c.strip() for c in cont]
            fields[key] = ("\n" if raw[0] == "|" else " ").join(stripped).strip()
        elif raw == "" and cont and cont[0].strip().startswith("- "):
            fields[key] = [c.strip()[2:].strip().strip("'\"") for c in cont if c.strip().startswith("- ")]
        elif raw == "" and cont:
            fields[key] = "\n".join(cont)  # nested map (hooks, metadata): keep raw
        elif raw[:1] in ("'", '"'):
            q = raw[0]
            joined = " ".join([raw] + [c.strip() for c in cont])
            if not joined.endswith(q) or len(joined) < 2:
                problems.append(("MUST", lineno, f"'{key}' opens a {q}-quoted string that is never closed"))
            inner = joined[1:-1] if joined.endswith(q) else joined[1:]
            fields[key] = inner.replace("''", "'") if q == "'" else inner.replace('\\"', '"')
        else:
            value = " ".join([raw] + [c.strip() for c in cont if c.strip()])
            if key in ("description", "when_to_use", "name"):
                if re.search(r":(\s|$)", value):
                    problems.append(("MUST", lineno,
                                     f"unquoted '{key}' contains ': ', which YAML rejects. "
                                     f"The skill then loads with empty metadata and never auto-triggers. "
                                     f"Use '{key}: >-' plus an indented block, or quote it"))
                if re.search(r"\s#", value):
                    problems.append(("SHOULD", lineno,
                                     f"unquoted '{key}' contains ' #': YAML drops everything after it as a comment"))
                    value = re.split(r"\s#", value, 1)[0]
                if value[:1] in "[{*&!%@`":
                    problems.append(("MUST", lineno, f"'{key}' starts with {value[0]!r}, a YAML indicator. Quote it"))
            fields[key] = value
    body_lines = lines[end + 1:]
    return fields, key_lines, "\n".join(body_lines), end + 2, problems


# --- reference graph ------------------------------------------------------------------

def refs_in(text, src_dir, skill_dir):
    """Yield (lineno, target_path, confidence, raw) for file references in text.

    confidence is "link" for markdown links and ${CLAUDE_SKILL_DIR}-anchored paths,
    "guess" for bare paths whose first directory exists in the skill, and "seen" for
    bare paths that resolve. Non-shell fenced blocks are skipped: they hold examples.
    """
    fence = None
    for n, line in enumerate(text.split("\n"), 1):
        m = re.match(r"^\s*(```+|~~~+)\s*([\w+-]*)", line)
        if m:
            fence = None if fence else m.group(2).lower()
            continue
        if fence is not None and fence not in SHELL_FENCES:
            continue
        seen = set()
        for m in MD_LINK_RE.finditer(INLINE_CODE_RE.sub("", line)):
            target = m.group(1).split("#", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                continue
            target = target.replace("${CLAUDE_SKILL_DIR}/", "")
            seen.add(target)
            yield n, (src_dir / target).resolve(), "link", target
        for m in PATH_RE.finditer(line):
            target = m.group(1)
            if target in seen or "://" in line[max(0, m.start() - 12):m.start()]:
                continue
            anchored = m.group(0) != target
            for base in (src_dir, skill_dir):
                cand = (base / target).resolve()
                if cand.exists():
                    yield n, cand, "seen", target
                    break
            else:
                first = target.split("/", 1)[0]
                if anchored:
                    yield n, (skill_dir / target).resolve(), "anchored", target
                elif "/" in target and (skill_dir / first).is_dir():
                    yield n, (skill_dir / target).resolve(), "guess", target


def skill_files(skill_dir):
    out = []
    for p in sorted(skill_dir.rglob("*")):
        rel = p.relative_to(skill_dir)
        if p.is_file() and not any(part in IGNORED_PARTS or part.startswith(".") for part in rel.parts):
            out.append(p)
    return out


def has_toc(lines):
    head = lines[:TOC_SEARCH_LINES]
    if any(re.match(r"^#{1,4}\s*(contents|table of contents|toc|index)\b", l.strip(), re.I) for l in head):
        return True
    anchors = sum(1 for l in head if re.match(r"^\s*[-*\d.]+\s.*\]\(#", l))
    return anchors >= 3


def is_third_party_module(mod):
    if hasattr(sys, "stdlib_module_names"):
        return mod not in sys.stdlib_module_names
    if mod in sys.builtin_module_names:
        return False
    try:
        spec = importlib.util.find_spec(mod)
    except (ImportError, ValueError):
        return True
    if spec is None:
        return True
    origin = spec.origin or ""
    if origin in ("built-in", "frozen"):
        return False
    stdlib = sysconfig.get_paths()["stdlib"]
    return not origin.startswith(stdlib) or "site-packages" in origin


# --- audit ----------------------------------------------------------------------------

def audit(skill_md, root):
    skill_dir = skill_md.parent
    rel = lambda p: os.path.relpath(p, skill_dir)  # noqa: E731  (header line shows where the skill is)
    text = read(skill_md)
    fields, key_lines, body, body_start, problems = parse_frontmatter(text)
    F = []
    add = lambda sev, rule, where, msg: F.append(Finding(sev, rule, where, msg))  # noqa: E731
    at = lambda line: f"{rel(skill_md)}:{line}"  # noqa: E731

    for sev, line, msg in problems:
        add(sev, "D1", at(line), msg)

    # D1 name
    name = fields.get("name")
    if name is None:
        add("CONSIDER", "D1", at(1), f"no 'name': Claude Code uses the directory name '{skill_dir.name}', but claude.ai/API upload requires it")
    elif isinstance(name, str):
        nl = at(key_lines.get("name", 1))
        if len(name) > NAME_MAX:
            add("MUST", "D1", nl, f"name is {len(name)} chars (max {NAME_MAX})")
        if not re.fullmatch(r"[a-z0-9-]+", name):
            add("MUST", "D1", nl, f"name {name!r} must be lowercase letters, digits and hyphens only")
        for word in RESERVED:
            if word in name.lower():
                add("MUST", "D1", nl, f"name contains reserved word '{word}'")
        if name != skill_dir.name:
            add("CONSIDER", "D1", nl, f"name {name!r} differs from directory '{skill_dir.name}'. Make sure the mismatch is intended")

    # D1/D2/D3 description
    desc = fields.get("description")
    wtu = fields.get("when_to_use") if isinstance(fields.get("when_to_use"), str) else ""
    dl = at(key_lines.get("description", 1))
    if not desc or not isinstance(desc, str):
        add("MUST", "D1", at(1), "no 'description': nothing for Claude to match requests against "
            "(Claude Code falls back to the first body line)")
        desc = ""
    else:
        if len(desc) > DESC_MAX_PLATFORM:
            add("SHOULD", "D1", dl, f"description is {len(desc)} chars: over the {DESC_MAX_PLATFORM} limit for claude.ai/API upload")
        if XML_TAG_RE.search(desc) or XML_TAG_RE.search(wtu):
            add("SHOULD", "D1", dl, "description contains <tags>: rejected on upload and shown as &lt;…&gt; in Claude Code. Use [brackets]")
        m = FIRST_PERSON_RE.search(desc)
        if m:
            add("SHOULD", "D2", dl, f"description is not third person ({m.group(0)!r}). It is injected into the system prompt")
        dmi_ = str(fields.get("disable-model-invocation", "false")).lower() in ("true", "yes", "on", "1")
        if not WHEN_RE.search(desc + " " + wtu):
            if dmi_:
                add("CONSIDER", "D2", dl, "no 'Use when …' clause. Manual-only (disable-model-invocation), so this only affects the / menu text")
            else:
                add("SHOULD", "D2", dl, "no 'Use when …' clause found: Claude can't tell when to pick this skill")
        if len(desc.split()) < 8:
            add("SHOULD", "D2", dl, f"description is only {len(desc.split())} words: too vague to win selection among many skills")
    combined = len(desc) + (len(wtu) + 1 if wtu else 0)
    if combined > LISTING_MAX:
        add("SHOULD", "D3", dl, f"description + when_to_use = {combined} chars: the listing cuts at {LISTING_MAX}, "
            f"so everything after '…{(desc + ' ' + wtu)[LISTING_MAX - 40:LISTING_MAX]}' is lost")

    # D1 keys
    for key, line in key_lines.items():
        if key not in KNOWN_KEYS:
            close = difflib.get_close_matches(key, KNOWN_KEYS, n=1)
            hint = f" (did you mean '{close[0]}'?)" if close else ""
            sev = "SHOULD" if close else "CONSIDER"
            add(sev, "D1", at(line), f"unknown frontmatter key '{key}' is silently ignored by Claude Code{hint}")
    cc_only = sorted(k for k in key_lines if k in KNOWN_KEYS and k not in PORTABLE_KEYS)
    if cc_only:
        add("CONSIDER", "D1", at(1), f"Claude Code-only keys {cc_only}: claude.ai/API upload rejects them (fine if the skill is Claude Code-only)")
    if "effort" in fields and fields["effort"] not in EFFORTS:
        add("SHOULD", "D1", at(key_lines["effort"]), f"effort {fields['effort']!r} not one of {sorted(EFFORTS)}")
    if "context" in fields and fields["context"] != "fork":
        add("SHOULD", "D1", at(key_lines["context"]), f"context {fields['context']!r}: the only accepted value is 'fork'")

    # D4 invocation control
    at_ = fields.get("allowed-tools")
    tools = at_ if isinstance(at_, list) else re.split(r"[,\s]+(?![^()]*\))", at_ or "")
    for t in tools:
        t = t.strip()
        if t in ("Bash", "Bash(*)", "Bash(* *)", "*"):
            add("SHOULD", "D4", at(key_lines.get("allowed-tools", 1)),
                f"allowed-tools grants '{t}' with no prompt. Scope it to the commands the skill runs")
    dmi = str(fields.get("disable-model-invocation", "false")).lower() in ("true", "yes", "on", "1")
    if not dmi:
        hits = sorted({m.group(0).lower() for m in SIDE_EFFECT_RE.finditer(body)})
        if hits:
            add("CONSIDER", "D4", at(body_start), f"side-effect actions {hits} without disable-model-invocation: "
                "confirm Claude should be able to start this skill on its own")
    if fields.get("context") == "fork":
        add("CONSIDER", "D4", at(key_lines["context"]), "context: fork: confirm the body is an explicit task, not only guidelines")

    # C1 / C3 size and front-loading
    body_lines = body.split("\n")
    n_lines = len(body_lines)
    tokens = est_tokens(body)
    if n_lines > BODY_LINES_MAX:
        add("SHOULD", "C1", at(body_start), f"body is {n_lines} lines (keep under {BODY_LINES_MAX}). Move reference material out")
    if tokens > BODY_TOKENS_MAX:
        running, cutoff = 0.0, None
        for idx, line in enumerate(body_lines):
            running += est_tokens(line + "\n")
            if running > BODY_TOKENS_MAX:
                cutoff = idx
                break
        cut_line = body_start + (cutoff or 0)
        add("SHOULD", "C1", at(body_start), f"body is ~{int(tokens):,} tokens (budget ~{BODY_TOKENS_MAX:,})")
        late = [body_start + i for i, l in enumerate(body_lines[cutoff:], cutoff) if EMPHATIC_RE.search(l)]
        if late:
            add("SHOULD", "C3", at(cut_line), f"content after ~line {cut_line} is dropped when the skill is re-attached after compaction; "
                f"it contains emphatic rules at lines {late[:8]}{' …' if len(late) > 8 else ''}")

    # P: reference graph
    files = skill_files(skill_dir)
    file_set = {p.resolve() for p in files}
    direct = {}
    me = skill_md.resolve()
    inside = lambda t: skill_dir.resolve() in t.parents  # noqa: E731
    for n, target, conf, raw in refs_in(body, skill_dir, skill_dir):
        ln = body_start + n - 1
        if target in file_set and target != me:
            direct.setdefault(target, ln)
        elif not target.exists() and inside(target):
            if conf in ("link", "anchored"):
                add("MUST", "P3", at(ln), f"references '{raw}', which does not exist in the skill")
            elif conf == "guess":
                add("SHOULD", "P3", at(ln), f"mentions '{raw}', which does not exist. Fix it, or mark it clearly as an example")
    nested = {}
    for src in [p for p in direct if p.suffix == ".md"]:
        for n, target, conf, raw in refs_in(read(src), src.parent, skill_dir):
            if target in file_set and target not in direct and target != me:
                nested.setdefault(target, (src, n))
            elif conf == "link" and not target.exists() and inside(target):
                add("MUST", "P3", f"{rel(src)}:{n}", f"links to '{raw}', which does not exist")
    for target, (src, n) in nested.items():
        add("SHOULD", "P1", f"{rel(src)}:{n}", f"'{rel(target)}' is reachable only through {src.name}, "
            "so Claude may preview it with head -100. Link it directly from SKILL.md")
    mentioned_dirs = {d.name for d in skill_dir.iterdir() if d.is_dir()
                      and re.search(rf"(?<![\w/]){re.escape(d.name)}/(?![\w.-])", body)}
    script_text = "\n".join(read(p) for p in files if p.suffix in SCRIPT_EXT)
    for p in files:
        rp = p.resolve()
        if rp == skill_md.resolve() or rp in direct or rp in nested:
            continue
        parts = p.relative_to(skill_dir).parts
        if p.name.lower().startswith(("license", "readme", "changelog")) or "evals" in parts or parts[0] in mentioned_dirs:
            continue
        if p.suffix in SCRIPT_EXT and (p.stem in script_text.replace(read(p), "")):
            continue  # helper module imported by another script
        add("CONSIDER", "P3", rel(p), "never referenced from SKILL.md: Claude won't know it exists. Link it with a 'when to use' or delete it")

    for p in files:
        if p.suffix == ".md" and p.resolve() != skill_md.resolve():
            lines = read(p).split("\n")
            if len(lines) > TOC_THRESHOLD_LINES and not has_toc(lines):
                add("SHOULD", "P2", rel(p), f"{len(lines)} lines with no table of contents in the first {TOC_SEARCH_LINES} lines: "
                    "a head -100 preview hides the file's full scope")
        if GENERIC_NAME_RE.match(p.name):
            add("CONSIDER", "P4", rel(p), "non-descriptive file name. Name it after its content")

    # Per-file text checks
    domains = {}
    for p in [skill_md] + [f for f in files if f.resolve() != skill_md.resolve()]:
        if p.suffix not in TEXT_EXT or p.resolve() == SELF:
            continue
        content = read(p)
        is_md = p.suffix == ".md"
        net_lines = []
        for n, line in enumerate(content.split("\n"), 1):
            w = f"{rel(p)}:{n}"
            if BACKSLASH_PATH_RE.search(line) and not p.suffix == ".py":
                add("CONSIDER", "P4", w, f"Windows-style path {BACKSLASH_PATH_RE.search(line).group(0)!r}. Use forward slashes")
            for rx in SECRET_RES:
                if rx.search(line):
                    add("MUST", "X1", w, "looks like a hardcoded credential. Use an environment variable")
                    break
            if ADVERSARIAL_RE.search(line):
                add("SHOULD", "X3", w, f"review: {ADVERSARIAL_RE.search(line).group(0)!r}. Must be harmless in context, or it is a Must")
            if NETWORK_RE.search(line):
                net_lines.append(n)
                for d in URL_RE.findall(line):
                    domains.setdefault(d.lower().rstrip(".,;:"), set()).add(rel(p))
            if OUTSIDE_PATH_RE.search(line) and not line.lstrip().startswith(("#", "//")):
                add("CONSIDER", "X4", w, f"path outside the skill/project: {OUTSIDE_PATH_RE.search(line).group(0)!r}")
            if is_md:
                m = RUN_REL_RE.search(line)
                if m and "${CLAUDE_SKILL_DIR}" not in line and "${CLAUDE_PLUGIN_ROOT}" not in line:
                    add("SHOULD", "S1", w, f"runs '{m.group(1)}' relative to the cwd, which is the user's project. "
                        "Use ${CLAUDE_SKILL_DIR}/" + m.group(1).lstrip("./"))
                m = INJECT_RE.search(DOUBLE_CODE_RE.sub("", line)) if p.resolve() == skill_md.resolve() else None
                if m and "|| true" not in m.group(1):
                    add("SHOULD", "S4", w, f"!`{m.group(1)}` is executed before the skill loads, and any non-zero exit aborts "
                        "the invocation. Add '|| true' if it can fail. If it is meant as documentation, rephrase it so '!' "
                        "is not directly followed by a backtick")
                if TIME_RE.search(line):
                    add("CONSIDER", "I3", w, f"time-sensitive wording: {TIME_RE.search(line).group(0)!r}")
        if net_lines and p.suffix in SCRIPT_EXT:
            add("SHOULD", "X2", f"{rel(p)}:{net_lines[0]}", f"network access in a script (lines {net_lines[:6]}). Confirm it matches the skill's purpose")
        if p.suffix == ".py":
            if BARE_EXCEPT_RE.search(content):
                add("CONSIDER", "S2", rel(p), "bare/silenced except: errors are swallowed instead of explained")
            mods = set(re.findall(r"^\s*(?:import|from)\s+([A-Za-z_]\w*)", content, re.M))
            local = {f.stem for f in files if f.suffix == ".py"}
            third = sorted(m for m in mods if m not in local and m != "__future__" and is_third_party_module(m))
            undocumented = [m for m in third if not re.search(rf"\b{re.escape(m)}\b", body)]
            if undocumented:
                add("SHOULD", "S3", rel(p), f"non-stdlib imports {undocumented} are not mentioned in SKILL.md. "
                    "List them with install steps")
    odd = sorted(d for d in domains if d not in HOME_DOMAINS)
    if odd:
        add("CONSIDER", "X2", rel(skill_dir), f"external domains referenced: {odd[:10]}. Confirm each is expected")

    # T1 evals
    roots = [skill_dir] + [p for p in skill_dir.parents if (p / ".claude-plugin").is_dir()][:1]
    if not any(any(r.glob(g)) for r in roots for g in ("evals", "evals/*", "*eval*.json", "tests/*skill*")):
        add("CONSIDER", "T1", rel(skill_dir), "no evals found (≥3 queries incl. should-NOT-trigger). "
            "See `claude plugin eval` or the skill-creator skill")

    F.sort(key=lambda f: (Finding.ORDER[f.sev], f.rule, f.where))
    stats = (f"body {n_lines} lines / ~{int(tokens):,} tokens · listing {combined}/{LISTING_MAX} chars · "
             f"files {len(files) - 1} ({len(direct)} linked, {len(nested)} nested)")
    return F, stats, name or skill_dir.name


def version_note():
    """Compare the Claude Code version the rules were verified against with the installed one."""
    base = f"rules verified against Claude Code {VERIFIED['claude_code']} ({VERIFIED['date']})"
    try:
        out = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return base + "; installed version unknown (`claude` not on PATH)"
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    if not m:
        return base + "; installed version unknown"
    installed = tuple(int(x) for x in m.groups())
    verified = tuple(int(x) for x in VERIFIED["claude_code"].split("."))
    if installed > verified:
        return (base + f"; installed {'.'.join(map(str, installed))} is NEWER, so some rules may be stale. "
                "Check the repo's open docs-drift issue, or run tools/check_docs_drift.py")
    return base + f"; installed {'.'.join(map(str, installed))}"


def find_skills(arg):
    p = Path(arg).expanduser()
    if p.is_file():
        return [p] if p.name == "SKILL.md" else []
    if (p / "SKILL.md").is_file():
        return [p / "SKILL.md"]
    return sorted(s for s in p.rglob("SKILL.md") if not any(part in IGNORED_PARTS for part in s.parts))


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 2
    root = Path.cwd()
    targets = [s for a in argv[1:] for s in find_skills(a)]
    if not targets:
        print(f"No SKILL.md found under: {' '.join(argv[1:])}", file=sys.stderr)
        return 2
    print(version_note())
    print()
    any_must = False
    for skill_md in targets:
        findings, stats, name = audit(skill_md.resolve(), root)
        counts = {s: sum(f.sev == s for f in findings) for s in Finding.ORDER}
        any_must |= counts["MUST"] > 0
        print(f"== {name}  ({os.path.relpath(skill_md, root)})")
        print(f"   {stats}")
        print(f"   {counts['MUST']} must · {counts['SHOULD']} should · {counts['CONSIDER']} consider")
        for f in findings:
            print(f"   {f}")
        print("   judgment rules not covered: D2 D4 C2 C3 P3(when) I1 I2 I3 I4 S1(run/read) S2 S5 X2 X3")
        print()
    return 1 if any_must else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
