# explain-diff

Turn a git branch or pull request into a **single self-contained HTML document that
explains the diff in prose** — the way a thoughtful author would explain it to a colleague
who hasn't read the code.

Not a diff viewer, not a code review. No findings, no severity ratings, no suggestions.
The deliverable is understanding.

## Why

A diff tells you *what* the characters changed. It doesn't tell you why the change exists,
which five files make up one logical change, or what the tests actually pin down. Reading
a 40-file branch to answer those questions costs an hour; this skill produces a document
that answers them in four minutes.

## What you get

A single HTML file — no CDN, no fonts, no remote images, renders from `file://` with the
network off — laid out as:

1. **Summary** — two to four sentences and a one-line takeaway.
2. **Major changes** — one card per *change* (not per file), each with prose that answers
   *what changed, why, and what it means*, plus a diagram or collapsed snippet where those
   earn their place.
3. **Minor changes** — a where / what / why table. Repetitive rows are merged.
4. **Test cases** — a case / verifies / kind table read from the test files themselves,
   followed by an honest sentence about coverage gaps.
5. **Excluded** — every file the triage dropped (lockfiles, generated code, snapshots),
   named with a reason, so nothing disappears silently.

Plus, where they help understanding:

- **Hand-authored inline SVG diagrams** — pipelines, before/after, state machines,
  sequences. Wired to CSS tokens, so they flip with light/dark mode.
- **Interactive walkthroughs** — a stepper for procedural logic with three or more ordered
  states, before/after tabs for rewritten algorithms. **CSS-only**, built on radio inputs
  and `:checked` selectors, so they still work in viewers that sandbox the page without
  `allow-scripts` — the Claude mobile app among them.

The document is theme-aware (light/dark, plus a manual toggle that reveals itself only
where scripts run), responsive, and prints with every step expanded.

## Invocation

**Explicit only**, enforced by `disable-model-invocation: true` in the skill's frontmatter.
It never self-triggers on an ordinary "review this PR" or "summarize this branch" — you
have to name it.

```
/explain-diff                       # current branch vs. merge base with the default branch
/explain-diff feature/rate-limits   # that branch vs. its merge base
/explain-diff main..feature/foo     # exactly that range
/explain-diff 42                    # PR #42 (gh CLI or GitHub MCP)
/explain-diff 42 --out ./report.html
```

Prose is written in the language of the conversation that invoked it; code identifiers,
paths, and API names stay in their original form. By default the report lands in a scratch
directory — not in your repo — and the skill prints the absolute path.

## How it works

1. **Resolve the target** — always diffs against the *merge base*, so commits that landed
   on the default branch don't leak into the explanation.
2. **Collect** the diff, the stat, and the commit log (commit messages carry the *why*).
3. **Triage** files into substantive / incidental / excluded.
4. **Read for understanding** — opens surrounding files, greps callers, asks what would
   break on revert, and groups scattered hunks into single logical changes.
5. **Plan** — decides major vs. minor, and where a diagram or interaction genuinely beats
   a paragraph.
6. **Write** from the bundled template, under a hard length discipline: three to five
   minutes of reading, summary under 120 words, each major change under 200.

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add kinchi22/claude-plugins

# Install
/plugin install explain-diff@kinchi22-claude-plugins
/reload-plugins
```

## Structure

```
explain-diff/
└── skills/explain-diff/
    ├── SKILL.md                      # workflow and quality bar
    ├── scripts/check-report.py       # static checker (stdlib only)
    ├── assets/report-template.html   # document skeleton: tokens, styles, CSS-only components
    └── references/
        ├── diagrams.md               # inline-SVG recipes + layout arithmetic
        └── interactive.md            # stepper, before/after tabs, snippet markup
```

## Checking a report

```bash
python3 skills/explain-diff/scripts/check-report.py report.html --repo /path/to/repo
```

Exit 1 on any failure. It verifies that **every quoted line appears verbatim in the file
its `<summary>` names**, indentation included — a doctored quotation looks exactly like a
quotation, so nothing but a mechanical comparison catches one. It also checks escaping
inside `<pre>`, that no external URL appears anywhere, that the interactive components are
radio-and-CSS rather than JavaScript, and that their radios, labels, and panels line up
with unique names and ids.

What it cannot judge stays on the human checklist in `SKILL.md`: whether the base is right,
whether each change answers *why*, whether a diagram shows a real mechanism — and whether
the interaction actually works, which needs a browser with JavaScript disabled.
