#!/usr/bin/env python3
"""Detect when the docs that skill-audit's rules are based on have changed.

Reads skills/skill-audit/rules.json and, for each source page, checks:
  1. every pinned quote (limits and per-rule evidence) is still in the page;
  2. lists extracted from the page (frontmatter keys, keys allowed outside Claude
     Code, effort levels) still equal the values the audit script uses;
  3. the page's section headings match the snapshot in doc-snapshot.json, so new
     guidance (a new section) is noticed even though no quote covers it yet.

No model calls: it downloads four markdown pages and compares strings.

Usage:
    check_docs_drift.py [--report FILE] [--docs-dir DIR] [--update-snapshot]

  --report FILE       also write the markdown report to FILE
  --docs-dir DIR      read <DIR>/<basename of each source URL> instead of fetching
  --update-snapshot   after you have reviewed a change, rewrite doc-snapshot.json
                      with the current headings (quotes and lists are fixed by
                      editing rules.json by hand)

Exit codes: 0 no drift, 1 drift found, 2 a page could not be fetched or read.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = HERE.parent / "skills" / "skill-audit" / "rules.json"
SNAPSHOT = HERE / "doc-snapshot.json"
FETCH_TIMEOUT_S = 30  # the largest page is ~120 KB; 30 s tolerates a slow CDN edge
FETCH_ATTEMPTS = 3  # transient 5xx/timeouts usually clear on a retry; more just delays the report


def normalize(text):
    """Compare text, not markup: drop emphasis/code marks, unify quotes and whitespace."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[`*]|\\(?=[_*`])", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def fetch(url, docs_dir):
    if docs_dir:
        return (Path(docs_dir) / url.rsplit("/", 1)[-1]).read_text(encoding="utf-8")
    last = None
    for attempt in range(FETCH_ATTEMPTS):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "skill-audit-docs-drift/1.0"})
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_S) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"{url}: {last}")


def headings(md):
    out, fence = [], False
    for line in md.split("\n"):
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
            continue
        m = None if fence else re.match(r"^(#{1,6})\s+(.+?)\s*(\{#[^}]*\})?\s*$", line)
        if m:
            out.append(f"{m.group(1)} {m.group(2)}")
    return out


# --- extractors for structured lists ----------------------------------------------------

def extract_frontmatter_table(md):
    lines = md.split("\n")
    start = next((i for i, l in enumerate(lines) if re.match(r"^\|\s*Field\s*\|\s*Required\s*\|", l)), None)
    if start is None:
        return None
    keys = []
    for line in lines[start + 2:]:
        m = re.match(r"^\|\s*`([\w-]+)`\s*\|", line)
        if not m:
            break
        keys.append(m.group(1))
    return keys


def extract_allowed_properties(md):
    m = re.search(r"Allowed properties are:\s*([\w ,-]+)", md)
    return [k.strip() for k in m.group(1).split(",")] if m else None


def extract_effort_options(md):
    row = next((l for l in md.split("\n") if l.startswith("| `effort`")), None)
    m = re.search(r"Options:\s*(.*?)(?:;|\.\s|\|)", row or "")
    return re.findall(r"`([\w-]+)`", m.group(1)) if m else None


EXTRACTORS = {
    "frontmatter_table": extract_frontmatter_table,
    "allowed_properties": extract_allowed_properties,
    "effort_options": extract_effort_options,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report")
    ap.add_argument("--docs-dir")
    ap.add_argument("--update-snapshot", action="store_true")
    args = ap.parse_args()

    rules = json.loads(RULES.read_text(encoding="utf-8"))
    sources = rules["sources"]
    pages, errors = {}, []
    for name, url in sources.items():
        try:
            pages[name] = fetch(url, args.docs_dir)
        except (OSError, RuntimeError) as e:
            errors.append(f"- `{name}`: {e}")
    if errors:
        print("Could not read every source page, so nothing was compared:\n" + "\n".join(errors), file=sys.stderr)
        return 2

    if args.update_snapshot:
        snap = {name: headings(md) for name, md in pages.items()}
        SNAPSHOT.write_text(json.dumps(snap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {SNAPSHOT.name} ({sum(len(v) for v in snap.values())} headings).")
        return 0

    norm = {name: normalize(md) for name, md in pages.items()}
    sections = []

    # 1. pinned quotes
    missing = []
    for key, item in rules["limits"].items():
        if normalize(item["quote"]) not in norm[item["source"]]:
            missing.append(f"- **limit `{key}` = {item['value']}** ({item['source']}): \"{item['quote']}\"")
    for key, item in rules["lists"].items():
        if "quote" in item and normalize(item["quote"]) not in norm[item["source"]]:
            missing.append(f"- **list `{key}`** ({item['source']}): \"{item['quote']}\"")
    for rule_id, quotes in rules["rules"].items():
        for q in quotes:
            if normalize(q["quote"]) not in norm[q["source"]]:
                missing.append(f"- **rule {rule_id}** ({q['source']}): \"{q['quote']}\"")
    if missing:
        sections.append("## Pinned quotes no longer found\n\nThe wording changed or the guidance was removed. "
                        "Re-read the source and update the rule, `rules.json`, and the script if the substance changed.\n\n"
                        + "\n".join(missing))

    # 2. structured lists
    changed = []
    for key, item in rules["lists"].items():
        if "extract" not in item:
            continue
        got = EXTRACTORS[item["extract"]](pages[item["source"]])
        if got is None:
            changed.append(f"- **`{key}`**: could not find it in `{item['source']}` any more (the page layout changed)")
            continue
        added = sorted(set(got) - set(item["value"]))
        removed = sorted(set(item["value"]) - set(got))
        if added or removed:
            parts = ([f"added {added}"] if added else []) + ([f"removed {removed}"] if removed else [])
            changed.append(f"- **`{key}`** ({item['source']}): " + ", ".join(parts))
    if changed:
        sections.append("## Lists the audit script relies on changed\n\nUpdate the value in `rules.json`; "
                        "the audit script reads it from there.\n\n" + "\n".join(changed))

    # 3. headings
    if SNAPSHOT.exists():
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        diffs = []
        for name, md in pages.items():
            now, before = headings(md), snap.get(name, [])
            added = [h for h in now if h not in before]
            removed = [h for h in before if h not in now]
            if added or removed:
                diffs.append(f"### {name} ({sources[name]})\n"
                             + "".join(f"\n- added: `{h}`" for h in added)
                             + "".join(f"\n- removed: `{h}`" for h in removed))
        if diffs:
            sections.append("## Section headings changed\n\nA new section may carry new guidance that no rule covers yet. "
                            "After reviewing, run `check_docs_drift.py --update-snapshot`.\n\n" + "\n\n".join(diffs))
    else:
        sections.append("## No heading snapshot\n\nRun `check_docs_drift.py --update-snapshot` once to create `doc-snapshot.json`.")

    v = rules["verified"]
    if not sections:
        print(f"No drift: all pinned quotes, lists and headings match (rules verified against Claude Code {v['claude_code']}, {v['date']}).")
        return 0
    report = (f"# skill-audit: source docs changed\n\nThe rules were last verified against Claude Code "
              f"{v['claude_code']} on {v['date']}.\n\n" + "\n\n".join(sections)
              + "\n\n## When done\n\n1. Update `references/rules.md`, `rules.json`, and `scripts/audit_skill.py` as needed.\n"
              "2. Run `python3 plugins/skill-audit/tools/check_docs_drift.py --update-snapshot`.\n"
              "3. Set `verified` in `rules.json` to the current Claude Code version and date.\n"
              "4. Re-run the drift check: it should report no drift.\n")
    print(report)
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    return 1


if __name__ == "__main__":
    sys.exit(main())
