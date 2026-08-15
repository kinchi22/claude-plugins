---
name: explain-diff
description: Turn a git branch or pull request diff into a concise, prose HTML explainer — summary, major changes, minor changes, test cases — with hand-authored inline-SVG diagrams and interactive walkthroughs for procedural logic. EXPLICIT INVOCATION ONLY. Run this only when the user names it directly (e.g. "/explain-diff", "explain-diff on PR 42", "use the explain-diff skill on this branch"). Do NOT trigger it for ordinary requests to review, summarize, describe, or comment on a diff, branch, commit, or PR — those are not this skill.
---

# Explain Diff

Produce a **single self-contained HTML document that explains a diff in prose**, the way a
thoughtful author would explain it to a colleague who has not read the code: what the
change is for, what actually changed and why, and what the tests pin down.

This is not a diff viewer and not a code review. There are no findings, no severity
ratings, no suggestions. The deliverable is *understanding*.

## Invocation

Explicit only. The user typed `/explain-diff`, or named the skill. Never self-trigger.

Arguments the skill accepts, in the order you should try to resolve them:

| Input | Meaning |
|---|---|
| *(nothing)* | Current branch vs. its merge base with the default branch |
| `feature/foo` | That branch vs. its merge base with the default branch |
| `main..feature/foo` | Exactly that range |
| `42`, `#42`, a PR URL | That pull request |
| `--out <path>` | Write the report there instead of the default location |

## Workflow

### 1 — Resolve the target

Establish the base and head before reading a single line of diff. A diff against the wrong
base produces a confidently wrong document.

```bash
git rev-parse --abbrev-ref HEAD
git symbolic-ref --quiet --short refs/remotes/origin/HEAD   # default branch
git merge-base origin/<default> <head>                      # the base to diff against
```

Always diff against the **merge base**, not the branch tip — otherwise unrelated commits
that landed on the default branch show up as part of this change.

For a pull request, prefer the PR's own base and head. Use `gh pr view <n> --json ...` /
`gh pr diff <n>` when the `gh` CLI is available; otherwise use the GitHub MCP tools
(`pull_request_read` with the diff method). Fall back to plain `git` on local refs.

If nothing resolves — an unknown branch, a PR you cannot reach — stop and say so. Do not
substitute a different target.

### 2 — Collect the raw material

```bash
git diff --stat <base>...<head>
git diff <base>...<head>
git log --oneline --no-merges <base>..<head>
```

The commit log matters: commit messages often carry the *why* that the diff itself cannot.

**A detailed PR description is evidence, not a source.** A thorough author writes up the
change better than you would — which makes translating their description into your report
the single most tempting failure of this skill. The description tells you what the author
*believes* and *intends*; it cannot tell you what the merged code does. Read it for the
*why* and for the open questions the author flagged, then verify every factual claim
against the diff. Independent reading is what earns the report its keep: it finds the
things the description doesn't say — a new exported function with no production caller
yet, a helper whose "single chokepoint" claim is or isn't true in the call graph.

### 3 — Triage the file list

Split the changed files into three buckets and record the third one — it goes in the
report so nothing is silently dropped.

- **Substantive** — behavior, interfaces, data shapes, configuration that matters.
- **Incidental** — renames, import shuffles, formatting, comment fixes, version bumps.
- **Excluded** — lockfiles, generated code, vendored trees, snapshots, minified bundles,
  binary assets, files with hundreds of lines of pure mechanical churn.

Excluded files are named in the *Excluded* section with a one-line reason (e.g.
`pnpm-lock.yaml — dependency lockfile, 2,411 lines, regenerated`). Never expand an excluded
file into the narrative; never pretend it did not change.

### 4 — Read for understanding, not just for the diff

This is the step that separates a real explainer from a rephrased changelog. For each
substantive change:

- **Open the surrounding file**, not only the hunk. A hunk shows *what* changed; the file
  shows what it changed *from* and what now depends on it.
- **Find the callers** of anything whose signature or behavior moved (`grep` the symbol).
  A change is only explainable once you know who feels it.
- **Ask what breaks if this is reverted.** The answer is usually the one-sentence purpose
  of the change, which is exactly what the prose needs to open with.
- **Group related hunks into one change.** A single logical change is routinely spread
  across five files. The report is organized by *change*, never by file.

### 5 — Decide the shape of the document

Before writing, settle three things:

**Major vs. minor.** A change is *major* if a reader who skipped it would misunderstand
the branch: new or altered behavior, a new dependency or integration point, a changed
contract, a data migration, a performance or security-relevant shift. Everything else is
minor. Aim for **2–5 major changes**; more than six usually means related things should
have been grouped. Minor changes are table rows, never paragraphs.

**Where a diagram earns its place.** Draw one only when it shows a mechanism the prose
cannot: a changed control flow, a new hop in a pipeline, a new state or transition, a
restructured data shape. Two or three per report is plenty, zero is fine for a small diff.
See `references/diagrams.md` for the recipes and the layout arithmetic.

**Where interaction earns its place.** A stepper only for procedural logic with three or
more ordered steps where each step changes state; before/after tabs only when the two
versions are best read whole. At most one or two per report. See
`references/interactive.md`.

### 6 — Write the report

Copy `assets/report-template.html` and fill it in. The template is self-contained: tokens
for light/dark, a theme toggle, card/table/snippet/diagram styles, and the small vanilla
JS the stepper and tabs need. Do not add external scripts, fonts, or stylesheets — the
report must render from a `file://` URL with the network off.

**Language:** write the prose in the language of the conversation that invoked the skill.
Keep code identifiers, file paths, and API names in their original form.

The four sections, and the standard each one has to meet:

#### Summary
Two to four sentences of prose: what this branch is for, and the single most important
thing it changes. Then one `.takeaway` line — the sentence you would say if you had one
sentence. Optionally one orienting diagram if the change has a shape worth seeing up front.
No bullet lists here.

#### Major changes
One `.card` per change. Each card carries a title naming the *change* (not the file), the
files it touches, and **1–3 short paragraphs of prose** answering: what changed, why, and
what it means for the reader. Add a diagram or an interactive component only where step 5
said it earns its place, and at most one collapsed `<details class="snippet">` of ≤ 12
lines as evidence.

Write in the indicative, about the code: *"Reads now hit the cache first, and the DB is
only the miss path."* Not *"This PR adds a cache."* — that's about the PR, not the system.

#### Minor changes
A table: **where** (file or module) · **what** (one clause) · **why** (one clause, or `—`
when it's self-evident). Merge repetitive rows — twelve import reorders are one row
reading `12 files — import ordering`. If there are no minor changes, drop the section.

#### Test cases
Read the test files, not just their names, and list the cases as a table: **case** (the
test name, in code) · **verifies** (one plain-language clause describing the behavior it
pins down, not a restatement of the name) · **kind** (unit / integration / e2e / property /
regression). Group by test file when there are more than about ten.

**When the branch adds more than ~25 cases, change the unit of the row.** One row per
`it` stops being a table and becomes a dump — a 126-case branch would blow the whole
length budget on this section alone. Instead make each row a **contract block** (the
`describe`, or a coherent group of cases), with a **count** column, and keep the file
grouping as header rows. State the real totals in the intro sentence. Generated or
parameterized cases (`it.each`, property/fuzz runs) are one row that names the generator
and the size of the space it covers — never one row per generated case.

Then one honest sentence about coverage — a behavior in the diff that no test touches is
worth naming. If the branch adds **no** tests, keep the section, say so plainly in one
sentence, and note which of the major changes are therefore unverified.

#### Excluded
The bucket from step 3, as one short paragraph or a compact list. If nothing was excluded,
keep the section and say so in one sentence — that a file which normally gets dropped was
small enough to keep is itself worth a reader's second of attention, and a silent section
is indistinguishable from a triage that never ran.

### 7 — Length discipline

The whole document should read in **three to five minutes**. Concretely: summary under
120 words, each major change under 200, minor changes as table rows only. If a card is
growing past that, the change is either two changes or is carrying detail that belongs in
the snippet.

Cut on sight:
- Sentences that restate the section heading.
- "It is important to note that", "This change essentially", "In order to".
- Narration of the diff mechanics ("three lines were added to the constructor").
- Any diagram whose boxes only repeat the words next to it.

### 8 — Deliver

Write to `--out` if given. Otherwise write to a scratch/temp directory — not into the
user's repository — and give the absolute path plus a one-line "how to open it"
(`open <path>` / `xdg-open <path>`).

Then summarize in chat in two or three lines: the target that was resolved, how many major
and minor changes, and whether tests were found. If the environment supports Artifacts and
the report looks like something the user would share with a team, offer to publish it —
offer, don't publish unasked.

## Quality bar

Before handing the report over, check it against these. Each one is a real failure mode:

- [ ] The base is the **merge base**, and the header states the range it explains.
- [ ] Every major change answers **why**, not just what. If a card has no "why", either the
      commit log has one you skipped, or the change is minor.
- [ ] The report is organized by **change**, not by file.
- [ ] Excluded files are **named**, with reasons.
- [ ] Every diagram shows a mechanism; none is decorative.
- [ ] Any interactive component covers genuinely procedural logic.
- [ ] `<`, `>`, `&` inside every `<pre>` are escaped.
- [ ] Every `.stepper` has equal counts of rail buttons and `.step`s; every `.ba` has equal
      counts of rail buttons and `.ba-panel`s.
- [ ] No external URL appears anywhere in the file — no CDN, font, or remote image.
- [ ] It reads in under five minutes.

## Reference files

- `assets/report-template.html` — the document skeleton, all styles, all JS.
- `references/diagrams.md` — inline-SVG recipes (pipeline, before/after, state, sequence)
  and the class vocabulary wired to the theme tokens.
- `references/interactive.md` — stepper, before/after tabs, and snippet markup, with the
  structural rules the built-in JS depends on.
