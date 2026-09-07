#!/usr/bin/env python3
"""Prove that an edit touched comments only, never code.

    code_guard.py save    <snapshot-dir> <file>...      # before editing
    code_guard.py check   <snapshot-dir> [<file>...]    # after editing
    code_guard.py restore <snapshot-dir> [<file>...]    # undo a bad edit
    code_guard.py check --base HEAD [<file>...]         # if the tree was clean

`check` strips comments and collapses whitespace outside string literals, then
compares what is left. Python goes through `ast` instead, so docstring edits are
allowed while every other string literal is still compared exactly.

Per-file verdicts:

    OK        code is identical once comments and whitespace are removed
    CHANGED   code differs - revert the file and redo the edit
    LIMITED   verified, but this language is only partly understood - read the diff
    SKIPPED   unknown language or unreadable - not verified at all

Exit status: 0 all clear, 1 some file CHANGED, 2 nothing changed but something
could not be verified.

Known limits (all of them make the checker noisier, not blinder, except where
noted): nested block comments, JS regex literals containing `//`, heredocs in
shell and Ruby, and HTML-family files, where an unquoted attribute holding `//`
can hide a same-line code edit - those report LIMITED, so read the diff.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import difflib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tokenize

C_QUOTES = [('"', "\\", False), ("'", "\\", False)]

PROFILES = {
    "c": {"line": ["//"], "block": [("/*", "*/")], "quotes": C_QUOTES},
    "cs": {"line": ["//"], "block": [("/*", "*/")], "quotes": C_QUOTES, "cs_verbatim": True},
    "rust": {"line": ["//"], "block": [("/*", "*/")], "quotes": C_QUOTES, "rust_raw": True},
    "js": {
        "line": ["//"],
        "block": [("/*", "*/")],
        "quotes": C_QUOTES + [("`", "\\", True)],
    },
    "go": {
        "line": ["//"],
        "block": [("/*", "*/")],
        "quotes": C_QUOTES + [("`", None, True)],
    },
    "php": {"line": ["//", "#"], "block": [("/*", "*/")], "quotes": C_QUOTES},
    "css": {"line": ["//"], "block": [("/*", "*/")], "quotes": C_QUOTES},
    "hash": {"line": ["#"], "block": [], "quotes": C_QUOTES},
    "ruby": {"line": ["#"], "block": [("=begin", "=end")], "quotes": C_QUOTES},
    "sql": {"line": ["--"], "block": [("/*", "*/")], "quotes": C_QUOTES},
    "lua": {"line": ["--"], "block": [("--[[", "]]")], "quotes": C_QUOTES},
    "haskell": {"line": ["--"], "block": [("{-", "-}")], "quotes": C_QUOTES},
    "lisp": {"line": [";"], "block": [], "quotes": [('"', "\\", True)]},
    "erlang": {"line": ["%"], "block": [], "quotes": [('"', "\\", False)]},
    "markup": {
        "line": [],
        "block": [("<!--", "-->")],
        "quotes": C_QUOTES,
        "limited": True,
    },
    "python-fallback": {
        "line": ["#"],
        "block": [],
        "quotes": [('"""', "\\", True), ("'''", "\\", True)] + C_QUOTES,
    },
}

EXTENSIONS = {
    "c": ".c .h .cpp .cxx .cc .hpp .hh .hxx .java .kt .kts .scala .swift .dart"
         " .m .mm .proto .gradle .groovy .sol .zig .glsl .frag .vert",
    "cs": ".cs",
    "rust": ".rs",
    "js": ".js .jsx .mjs .cjs .ts .tsx .mts .cts",
    "go": ".go",
    "php": ".php",
    "css": ".css .scss .less .sass",
    "hash": ".sh .bash .zsh .ksh .pl .pm .r .yml .yaml .toml .tf .tfvars .cmake .mk .nix .jl .ex .exs",
    "ruby": ".rb .rake .gemspec",
    "sql": ".sql",
    "lua": ".lua",
    "haskell": ".hs",
    "lisp": ".el .lisp .clj .cljs .cljc .edn .scm",
    "erlang": ".erl .hrl",
    "markup": ".html .htm .xhtml .vue .svelte .xml .svg .astro",
}

BY_EXT = {ext: name for name, exts in EXTENSIONS.items() for ext in exts.split()}
BY_NAME = {
    "Makefile": "hash", "makefile": "hash", "Dockerfile": "hash",
    "Rakefile": "ruby", "Gemfile": "ruby", "CMakeLists.txt": "hash",
}
PYTHON_EXT = {".py", ".pyi"}
RUST_RAW = re.compile(r'r(#*)"')
SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script\s*>", re.S | re.I)
STYLE_RE = re.compile(r"<style\b[^>]*>(.*?)</style\s*>", re.S | re.I)

# Elixir and Julia keep their API docs in string literals, not comments, so an
# edit there reads as a code change. Flag them rather than pretend otherwise.
LIMITED_EXT = {".ex", ".exs", ".jl"}


def profile_for(path):
    base = os.path.basename(path)
    ext = os.path.splitext(base)[1].lower()
    if ext in PYTHON_EXT:
        return "python", None
    name = BY_NAME.get(base) or BY_EXT.get(ext)
    if not name:
        return None, None
    prof = dict(PROFILES[name])
    if ext in LIMITED_EXT:
        prof["limited"] = True
    return name, prof


def scan(src, prof, line_offset=0):
    """Return (code with comments and redundant whitespace gone, comment line numbers)."""
    line_c, block_c = prof.get("line", []), prof.get("block", [])
    quotes = prof.get("quotes", [])
    n = len(src)
    out, comment_lines = [], set()
    starts = [0] + [i + 1 for i, ch in enumerate(src) if ch == "\n"]

    def lineno(pos):
        return bisect.bisect_right(starts, min(pos, n))

    def mark(a, b):
        for ln in range(lineno(a), lineno(max(a, b - 1)) + 1):
            comment_lines.add(ln + line_offset)

    def space():
        if out and out[-1] != " ":
            out.append(" ")

    i = 0
    while i < n:
        if prof.get("rust_raw") and src[i] == "r":
            m = RUST_RAW.match(src, i)
            if m:
                close = '"' + "#" * len(m.group(1))
                k = src.find(close, m.end())
                j = n if k < 0 else k + len(close)
                out.append(src[i:j])
                i = j
                continue
        if prof.get("cs_verbatim") and src.startswith('@"', i):
            j = i + 2
            while j < n:
                if src[j] == '"':
                    if j + 1 < n and src[j + 1] == '"':
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            out.append(src[i:j])
            i = j
            continue
        hit = False
        for delim, esc, multiline in quotes:
            if src.startswith(delim, i):
                j = i + len(delim)
                while j < n:
                    if esc and src[j] == esc:
                        j += 2
                        continue
                    if src.startswith(delim, j):
                        j += len(delim)
                        break
                    if src[j] == "\n" and not multiline:
                        break
                    j += 1
                out.append(src[i:j])
                i, hit = j, True
                break
        if hit:
            continue
        for token in line_c:
            if src.startswith(token, i):
                k = src.find("\n", i)
                j = n if k < 0 else k
                mark(i, j)
                space()
                i, hit = j, True
                break
        if hit:
            continue
        for open_t, close_t in block_c:
            if src.startswith(open_t, i):
                k = src.find(close_t, i + len(open_t))
                j = n if k < 0 else k + len(close_t)
                mark(i, j)
                space()
                i, hit = j, True
                break
        if hit:
            continue
        if src[i].isspace():
            space()
            i += 1
            continue
        out.append(src[i])
        i += 1
    return "".join(out).strip(), comment_lines


def scan_markup(src):
    """Markup outside <script>/<style>, JS and CSS inside them, line numbers preserved."""
    spans = []
    for pattern, name in ((SCRIPT_RE, "js"), (STYLE_RE, "css")):
        for match in pattern.finditer(src):
            spans.append((match.start(1), match.end(1), PROFILES[name]))
    spans.sort()
    pieces, comment_lines, pos = [], set(), 0
    for start, end, prof in spans:
        for seg_start, seg_end, seg_prof in (
            (pos, start, PROFILES["markup"]),
            (start, end, prof),
        ):
            code, lines = scan(
                src[seg_start:seg_end], seg_prof, src.count("\n", 0, seg_start)
            )
            pieces.append(code)
            comment_lines |= lines
        pos = end
    code, lines = scan(src[pos:], PROFILES["markup"], src.count("\n", 0, pos))
    pieces.append(code)
    return " ".join(piece for piece in pieces if piece), comment_lines | lines


def python_scan(src):
    """AST shape with docstrings blanked, plus the lines holding comments or docstrings."""
    tree = ast.parse(src)
    lines = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not body or not isinstance(body[0], ast.Expr):
            continue
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            for ln in range(value.lineno, (value.end_lineno or value.lineno) + 1):
                lines.add(ln)
            value.value = "<docstring>"
            value.kind = None
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                lines.add(tok.start[0])
    except (tokenize.TokenError, IndentationError, SyntaxError):
        for idx, line in enumerate(src.splitlines(), 1):
            if "#" in line:
                lines.add(idx)
    return ast.dump(tree), lines


def analyse(path, before, after):
    """Return (verdict, note, suspicious lines)."""
    kind, prof = profile_for(path)
    if kind is None:
        return "SKIPPED", "unknown language", []
    if kind == "python":
        try:
            before_code, before_lines = python_scan(before)
        except SyntaxError as exc:
            prof = PROFILES["python-fallback"]
            note = f"original does not parse ({exc.msg}); fell back to text comparison"
            before_code, before_lines = scan(before, prof)
            after_code, after_lines = scan(after, prof)
            verdict = "OK" if before_code == after_code else "CHANGED"
            return verdict, note, audit(before, after, before_lines, after_lines)
        try:
            after_code, after_lines = python_scan(after)
        except SyntaxError as exc:
            return "CHANGED", f"the edit broke Python syntax: line {exc.lineno}: {exc.msg}", []
    elif kind == "markup":
        before_code, before_lines = scan_markup(before)
        after_code, after_lines = scan_markup(after)
    else:
        before_code, before_lines = scan(before, prof)
        after_code, after_lines = scan(after, prof)
    suspicious = audit(before, after, before_lines, after_lines)
    if before_code != after_code:
        return "CHANGED", first_difference(before_code, after_code), suspicious
    limited = bool(prof and prof.get("limited"))
    return ("LIMITED" if limited else "OK"), "", suspicious


def audit(before, after, before_lines, after_lines):
    """Changed lines with no comment anywhere in them - a second, independent signal.

    Deliberately per-hunk rather than per-line: dropping a trailing comment leaves
    a line that no longer looks like a comment, and flagging that would bury the
    real signal in noise.
    """
    b, a = before.splitlines(), after.splitlines()
    found = []
    matcher = difflib.SequenceMatcher(None, b, a, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        touches_comment = any((k + 1) in before_lines for k in range(i1, i2)) or any(
            (k + 1) in after_lines for k in range(j1, j2)
        )
        if touches_comment:
            continue
        for k in range(i1, i2):
            if b[k].strip():
                found.append(f"  - line {k + 1}: {b[k].strip()[:90]}")
        for k in range(j1, j2):
            if a[k].strip():
                found.append(f"  + line {k + 1}: {a[k].strip()[:90]}")
    return found


def first_difference(before_code, after_code):
    limit = min(len(before_code), len(after_code))
    pos = next((i for i in range(limit) if before_code[i] != after_code[i]), limit)
    start = max(0, pos - 45)
    return (
        "code differs around:\n"
        f"    before: ...{before_code[start:pos + 45]}...\n"
        f"    after : ...{after_code[start:pos + 45]}..."
    )


def repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.getcwd()


def read(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    return raw.decode("utf-8", errors="replace")


def manifest_path(snapshot):
    return os.path.join(snapshot, "manifest.json")


def cmd_save(args):
    root = repo_root()
    files = sorted({os.path.relpath(os.path.abspath(f), root) for f in args.files})
    for rel in files:
        src = os.path.join(root, rel)
        dst = os.path.join(args.snapshot, "files", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    os.makedirs(args.snapshot, exist_ok=True)
    with open(manifest_path(args.snapshot), "w") as handle:
        json.dump({"root": root, "files": files}, handle, indent=2)
    print(f"saved {len(files)} file(s) to {args.snapshot}")
    return 0


def load_manifest(snapshot):
    with open(manifest_path(snapshot)) as handle:
        return json.load(handle)


def selected(manifest, root, files):
    if not files:
        return manifest["files"]
    wanted = {os.path.relpath(os.path.abspath(f), root) for f in files}
    return [rel for rel in manifest["files"] if rel in wanted]


def cmd_check(args):
    if args.base:
        root = repo_root()
        rels = args.files or subprocess.run(
            ["git", "diff", "--name-only", args.base],
            capture_output=True, text=True, check=True,
        ).stdout.split()
        rels = sorted({os.path.relpath(os.path.abspath(f), root) for f in rels})
        pairs = []
        for rel in rels:
            blob = subprocess.run(
                ["git", "show", f"{args.base}:{rel}"],
                capture_output=True, text=True,
            )
            if blob.returncode != 0:
                continue
            pairs.append((rel, blob.stdout))
    else:
        manifest = load_manifest(args.snapshot)
        root = manifest["root"]
        pairs = [
            (rel, read(os.path.join(args.snapshot, "files", rel)))
            for rel in selected(manifest, root, args.files)
        ]

    counts = {"OK": 0, "LIMITED": 0, "CHANGED": 0, "SKIPPED": 0}
    for rel, before in pairs:
        current = os.path.join(root, rel)
        if not os.path.exists(current):
            print(f"CHANGED   {rel}\n  file is gone")
            counts["CHANGED"] += 1
            continue
        verdict, note, suspicious = analyse(rel, before, read(current))
        counts[verdict] += 1
        print(f"{verdict:9} {rel}")
        if note:
            print("  " + note.replace("\n", "\n  "))
        if suspicious and verdict != "CHANGED":
            print("  changed lines outside any comment - confirm these are intended:")
            print("\n".join(suspicious[:6]))
        elif suspicious and verdict == "CHANGED":
            print("\n".join(suspicious[:6]))

    print(
        f"\n{counts['OK'] + counts['LIMITED']} verified"
        f" ({counts['LIMITED']} partly), {counts['CHANGED']} changed,"
        f" {counts['SKIPPED']} unverified"
    )
    if counts["CHANGED"]:
        return 1
    return 2 if counts["SKIPPED"] else 0


def cmd_restore(args):
    manifest = load_manifest(args.snapshot)
    root = manifest["root"]
    rels = selected(manifest, root, args.files)
    for rel in rels:
        shutil.copy2(os.path.join(args.snapshot, "files", rel), os.path.join(root, rel))
    print(f"restored {len(rels)} file(s)")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subs = parser.add_subparsers(dest="command", required=True)

    save = subs.add_parser("save", help="copy files aside before editing")
    save.add_argument("snapshot")
    save.add_argument("files", nargs="+")
    save.set_defaults(func=cmd_save)

    check = subs.add_parser("check", help="compare the edited files against the snapshot")
    check.add_argument("snapshot", nargs="?", default="")
    check.add_argument("--base", help="compare against a git revision instead of a snapshot")
    check.add_argument("files", nargs="*")
    check.set_defaults(func=cmd_check)

    restore = subs.add_parser("restore", help="put the snapshot back")
    restore.add_argument("snapshot")
    restore.add_argument("files", nargs="*")
    restore.set_defaults(func=cmd_restore)

    args = parser.parse_args(argv)
    if args.command == "check" and not args.base and not args.snapshot:
        parser.error("check needs a snapshot directory or --base <rev>")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
