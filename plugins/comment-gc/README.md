# comment-gc

Collects the comment garbage that piles up during agentic coding.

Long sessions leave a sediment of comments: what changed and when, why the previous approach
was abandoned, restatements of the line below, notes addressed to whoever was in the chat.
After a while a file's comments describe its history instead of its present, and nobody
deletes them because deleting someone else's note feels risky.

`comment-gc` deletes what stopped being true or never earned its place, compresses the rest
to its point, and **changes no code** — a guarantee it proves mechanically rather than
asserts.

## Usage

```
/comment-gc                 # files changed on this branch vs. its merge base
/comment-gc src/checkout    # a path, glob, or directory
/comment-gc --staged        # what's in the index
/comment-gc main..HEAD      # any rev range
```

The skill also triggers on plain requests — "주석 좀 정리해줘", "these comments are longer
than the code", "strip the outdated comments from this file".

## What it does

| | |
|---|---|
| **Deletes** | Stale comments, change history and narration, commented-out code, restatements of the code below, conversational residue, duplicates |
| **Compresses** | Verbose "why" comments, over-written doc comments — keeping parameters, returns, errors, links, and TODO references |
| **Never touches** | Tool directives (`eslint-disable`, `# type: ignore`, `//go:build`, …), license headers, generated-file markers, and any code at all |
| **Asks about** | The handful of judgment calls a maintainer could reasonably disagree with — kept in place while it asks |

Architectural rationale is assumed to live in ADRs and other docs, not in comments, so a
comment re-telling a design decision is not treated as the only copy.

## The code-unchanged guarantee

`scripts/code_guard.py` snapshots every file before editing, then proves afterwards that the
code is identical once comments and whitespace are removed. Python is compared through its
AST — docstring edits are allowed, every other literal is compared exactly; HTML, Vue and
Svelte are split so that `<script>` and `<style>` blocks are read as JavaScript and CSS.

```bash
python3 scripts/code_guard.py save    <dir> <files...>   # before
python3 scripts/code_guard.py check   <dir>              # after: OK / LIMITED / CHANGED / SKIPPED
python3 scripts/code_guard.py restore <dir> [files...]   # undo a bad edit
python3 scripts/code_guard.py check --base HEAD          # if the tree was clean to begin with
```

It exits non-zero when any file's code changed, so it also works as a pre-commit or CI check
for comment-only pull requests.

## Installation

```bash
/plugin marketplace add kinchi22/claude-plugins
/plugin install comment-gc@kinchi22-claude-plugins
```
