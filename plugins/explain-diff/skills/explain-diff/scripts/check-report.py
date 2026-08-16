#!/usr/bin/env python3
"""Static checks for an explain-diff report. Standard library only.

    python3 check-report.py <report.html> [--repo <root>] [--quiet]

Verifies the mechanically checkable half of the skill's quality bar:

  quotes    every line inside a `<details class="snippet">` appears verbatim —
            indentation included — in the file its <summary> names
  escaping   `<`, `>`, `&` inside every <pre> are escaped
  offline    no external URL anywhere in the document
  css-only   steppers and before/after tabs do not depend on JavaScript
  structure  radios / labels / panels line up, names and ids are unique

Exit status is 0 when everything passes, 1 otherwise. The `quotes` check is
the reason this script exists: a doctored quotation looks exactly like a
quotation, so nothing but a mechanical comparison catches one.
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

# A summary reads "<path>:<lines>" with an optional " — note" after it.
SUMMARY_RE = re.compile(r"<summary>\s*([^\s<]+?)(?::[\d–—,\s\-]+)?\s*(?:[—–-]\s*[^<]*)?</summary>")
SNIPPET_RE = re.compile(
    r'<details class="snippet">\s*<summary>(.*?)</summary>\s*<pre><code>(.*?)</code></pre>',
    re.S,
)
SPAN_RE = re.compile(r'<span class="d-(add|del|ctx)">(.*?)</span>', re.S)
PRE_RE = re.compile(r"<pre>(.*?)</pre>", re.S)
URL_RE = re.compile(r"""(?:https?:)?//[a-zA-Z0-9._-]+""")
ELISION = re.compile(r"^\s*(?://\s*)?[.…]{1,3}\s*(?:\(.*\)\s*)?[.…]{0,3}\s*$")

ALLOWED_HOSTS = {"www.w3.org"}  # SVG xmlns, declarative only — never fetched


class Report:
    def __init__(self, text: str) -> None:
        self.text = text
        self.failures: list[tuple[str, str]] = []

    def fail(self, check: str, msg: str) -> None:
        self.failures.append((check, msg))


def resolve_source(name: str, repo: Path, cache: dict[str, Path | None]) -> Path | None:
    """Map a <summary> path to a real file. Exact path first, then basename."""
    if name in cache:
        return cache[name]
    direct = repo / name
    if direct.is_file():
        cache[name] = direct
        return direct
    matches = [p for p in repo.rglob(Path(name).name) if p.is_file() and ".git" not in p.parts]
    cache[name] = matches[0] if len(matches) == 1 else None
    if len(matches) > 1:
        cache[name] = None
    return cache[name]


def check_quotes(r: Report, repo: Path) -> tuple[int, int, int]:
    """Every kept line of every snippet must exist verbatim in its source file."""
    verified = elided = unresolved = 0
    cache: dict[str, Path | None] = {}
    source_lines: dict[Path, set[str]] = {}

    for m in SNIPPET_RE.finditer(r.text):
        summary_raw, body = m.group(1), m.group(2)
        name_match = SUMMARY_RE.search(f"<summary>{summary_raw}</summary>")
        name = name_match.group(1) if name_match else None
        path = resolve_source(name, repo, cache) if name else None
        if path is None:
            unresolved += 1
            r.fail("quotes", f"summary does not name a resolvable file: {summary_raw.strip()!r}")
            continue
        if path not in source_lines:
            source_lines[path] = set(path.read_text(encoding="utf-8").split("\n"))

        for kind, raw in SPAN_RE.findall(body):
            line = html.unescape(raw)
            text = line[2:] if line[:2] in ("+ ", "- ") else line
            if kind == "del":
                elided += 1  # removed code: not in the working tree by definition
                continue
            if not text.strip() or ELISION.match(text):
                elided += 1
                continue
            if text in source_lines[path]:
                verified += 1
            else:
                r.fail("quotes", f"{path.name}: quoted line is not in the file — {text!r}")
    return verified, elided, unresolved


def check_escaping(r: Report) -> None:
    for m in PRE_RE.finditer(r.text):
        inner = re.sub(r"</?(?:span|code)[^>]*>", "", m.group(1))
        if "<" in inner:
            r.fail("escaping", f"unescaped '<' inside <pre>: {inner.strip()[:70]!r}")
        for amp in re.finditer(r"&(?!(?:amp|lt|gt|quot|#\d+|#x[0-9a-fA-F]+);)", inner):
            r.fail("escaping", f"bare '&' inside <pre> at offset {amp.start()}")


def check_offline(r: Report) -> None:
    for m in URL_RE.finditer(r.text):
        url = m.group(0)
        host = url.split("//", 1)[1]
        if host not in ALLOWED_HOSTS:
            r.fail("offline", f"external URL in a self-contained report: {url}")


def check_css_only(r: Report) -> None:
    scripts = re.findall(r"<script[^>]*>", r.text)
    if len(scripts) > 1:
        r.fail("css-only", f"{len(scripts)} <script> tags; the template ships exactly one")
    for kind, block in iter_components(r.text):
        if "<button" in block:
            r.fail("css-only", f"{kind} uses <button> — interaction must be radio + CSS")
        if 'aria-selected="true"' in block and "<input" not in block:
            r.fail("css-only", f"{kind} looks JS-driven (aria-selected without radios)")


def iter_components(text: str):
    """Yield each component's full inner HTML, matching <div> nesting.

    A non-greedy `.*?</div>` stops at the rail's closing tag and silently
    hands every later check an empty body, so the depth counting is the
    point of this function.
    """
    tag = re.compile(r"<(/?)div\b[^>]*>")
    for kind, cls in (("stepper", "stepper"), ("before/after", "ba")):
        for m in re.finditer(rf'<div class="{cls}">', text):
            depth, pos = 1, m.end()
            for t in tag.finditer(text, m.end()):
                depth += -1 if t.group(1) else 1
                if depth == 0:
                    pos = t.start()
                    break
            else:
                continue  # unbalanced; the structure check reports it
            yield kind, text[m.end():pos]


def check_structure(r: Report) -> None:
    for tag in ("details", "pre", "code", "span"):
        opens = len(re.findall(rf"<{tag}[\s>]", r.text))
        closes = len(re.findall(rf"</{tag}>", r.text))
        if opens != closes:
            r.fail("structure", f"<{tag}> unbalanced: {opens} open, {closes} close")

    seen_names: set[str] = set()
    for kind, block in iter_components(r.text):
        radios = re.findall(r'<input[^>]*type="radio"[^>]*>', block)
        labels = re.findall(r"<label[^>]*>", block)
        panel_cls = "step" if kind == "stepper" else "ba-panel"
        panels = len(re.findall(rf'class="{panel_cls}"', block))
        if not radios:
            r.fail("structure", f"{kind} has no radio inputs")
            continue
        if not (len(radios) == len(labels) == panels):
            r.fail("structure", f"{kind}: {len(radios)} radios / {len(labels)} labels / {panels} panels")
        if sum("checked" in x for x in radios) != 1:
            r.fail("structure", f"{kind}: exactly one radio must carry `checked`")
        if "checked" not in radios[0]:
            r.fail("structure", f"{kind}: the first radio must be the checked one")
        names = {n for x in radios for n in re.findall(r'name="([^"]+)"', x)}
        if len(names) != 1:
            r.fail("structure", f"{kind}: radios must share one name, found {sorted(names)}")
        elif names & seen_names:
            r.fail("structure", f"{kind}: name {names.pop()!r} is reused by another component")
        else:
            seen_names |= names

    ids = re.findall(r'\sid="([^"]+)"', r.text)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        r.fail("structure", f"duplicate id attributes: {sorted(dupes)}")


def default_repo() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def main() -> int:
    ap = argparse.ArgumentParser(description="Static checks for an explain-diff report.")
    ap.add_argument("report", type=Path)
    ap.add_argument("--repo", type=Path, default=None,
                    help="root of the repo the snippets quote (default: git toplevel)")
    ap.add_argument("--quiet", action="store_true", help="print only failures")
    args = ap.parse_args()

    if not args.report.is_file():
        print(f"no such report: {args.report}", file=sys.stderr)
        return 2
    repo = args.repo or default_repo()

    r = Report(args.report.read_text(encoding="utf-8"))
    verified, elided, unresolved = check_quotes(r, repo)
    check_escaping(r)
    check_offline(r)
    check_css_only(r)
    check_structure(r)

    if not args.quiet:
        print(f"repo:    {repo}")
        print(f"quotes:  {verified} lines verified verbatim, "
              f"{elided} elided/removed, {unresolved} snippets unresolved")

    if not r.failures:
        if not args.quiet:
            print("PASS — all static checks clean.")
            print("Still to do by hand: load the report with JavaScript disabled and click "
                  "a rail label (see references/interactive.md).")
        return 0

    by_check: dict[str, list[str]] = {}
    for check, msg in r.failures:
        by_check.setdefault(check, []).append(msg)
    print()
    for check, msgs in by_check.items():
        print(f"FAIL [{check}] {len(msgs)}")
        for msg in msgs:
            print(f"  - {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
