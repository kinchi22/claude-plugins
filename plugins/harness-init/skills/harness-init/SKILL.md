---
name: harness-init
description: Set up or upgrade a project's agentic development harness — a thin CLAUDE.md that @imports coding guidelines, a PRD → milestone-branch → per-slice TDD → review → handoff development cycle, an authoritative docs/glossary.md, and an ADR template. This is a one-time project bootstrap that the user invokes explicitly (e.g. /harness-init, or "set up the harness / set up the dev process / bootstrap the agent workflow"). It is NOT for everyday coding and should not trigger on routine mentions of TDD, branching, PRDs, or CLAUDE.md edits — only when the user clearly asks to establish or upgrade the harness itself. Idempotent: safe to re-run to upgrade an existing harness.
---

# Harness Init

Establish a consistent **agent development harness** in the current project so every
future session follows the same coding discipline and development loop. The harness is
just files in the repo — a thin `CLAUDE.md` that `@import`s rule modules, an
authoritative domain glossary, and an ADR template — so it is version-controlled,
reviewable, and loaded automatically by every session.

This skill is **idempotent**: run it on a greenfield repo to bootstrap, or on a project
that already has a harness to upgrade it. It detects existing files and merges rather
than overwriting.

## What it sets up

| Path | Role | On re-run |
|------|------|-----------|
| `CLAUDE.md` | Thin root file; `@import`s the rule modules between `harness-init` markers | Merge: update only the marked block, keep the rest |
| `.claude/rules/coding-guidelines.md` | Behavioral guidelines (think-before-coding, simplicity, surgical changes, goal-driven) | Harness-managed: offer to update if changed |
| `.claude/rules/dev-cycle.md` | The development loop + branch/PR/glossary/ADR conventions | Harness-managed: offer to update; preserve customizations |
| `docs/glossary.md` | **Authoritative** domain vocabulary | Project-owned: create only if missing, never overwrite |
| `docs/adr/TEMPLATE.md` | ADR template | Project-owned: create only if missing |

Why `.claude/rules/` + `@import` instead of one big `CLAUDE.md`: Claude Code auto-loads
`CLAUDE.md` and anything it `@import`s, so the rules still load every session, but each
concern lives in its own readable file. (`.claude/rules/` on its own is *not*
auto-loaded — the `@import` lines in `CLAUDE.md` are what pull them in.)

## Workflow

### 1. Survey the project

Before writing anything, understand what's already here. Check:

- Is this a git repo? What's the default branch name?
- Does `CLAUDE.md` already exist? If so, read it — you'll merge, not replace.
- Do any harness files already exist (`.claude/rules/`, `docs/glossary.md`,
  `docs/prd/`, `docs/adr/`)? Note which, so you know what to skip vs. update.
- What's the stack? Detect from `package.json`, `pyproject.toml`/`setup.cfg`, `go.mod`,
  `Cargo.toml`, `pom.xml`, etc. — you need this to fill the verification command.

### 2. Interview — only the gaps

Ask only what the survey didn't answer, and offer detected defaults so the user can
just confirm:

- **Verification command** — the real test/lint command (e.g. `npm test`, `pytest`,
  `go test ./...`). Infer a default from the detected stack.
- **Branch conventions** — default to `milestone/<slug>` and
  `slice/<milestone-slug>/<slice-slug>`; confirm or adjust.
- **PRD-vs-branch order** — does the team cut the milestone branch before or after
  committing the PRD? (Step 3 of the cycle notes both are valid.)
- **Review style** — PRs, or direct review? This only tunes the wording in
  `dev-cycle.md`.

If an existing harness is detected, confirm before changing any harness-managed file.

### 3. Scaffold — idempotent

Copy the templates from this skill's `assets/` directory into the project, applying the
interview answers, following these merge rules:

**`CLAUDE.md`**
- If absent: create from `assets/CLAUDE.md.template`, filling the project name.
- If present *with* the `harness-init` markers: replace only the block between
  `<!-- harness-init:begin -->` and `<!-- harness-init:end -->`.
- If present *without* markers: append a `## Agent harness` section containing the
  marker block and the two `@import` lines. Never touch the user's existing content.

**Rule files** (`.claude/rules/coding-guidelines.md`, `dev-cycle.md`) — harness-managed
- If absent: copy from `assets/`. In `dev-cycle.md`, replace the `<TEST_COMMAND>`
  placeholder and adjust branch names to the confirmed conventions.
- If present: diff against the template. If it changed, show the user what's new and
  ask before overwriting — they may have customized it.

**Project-owned seeds** (`docs/glossary.md`, `docs/adr/TEMPLATE.md`)
- Create from `assets/` **only if missing**. Never overwrite — these belong to the
  project once seeded. If `docs/glossary.md` already exists, leave it; it is already
  the authoritative source.
- The PRD template (`docs/prd/TEMPLATE.md`) is **not** created here — the `/prd` skill
  owns it and seeds it on first run. Don't scaffold a competing copy.

### 4. Report and point to next steps

Print the tree of files created/updated/skipped, then summarize the established loop in
a few lines:

```
decide goal → /prd → commit PRD + cut milestone branch
   → per slice: branch off milestone → /tdd (if code) → review/PR → merge
      → /handoff
```

Tell the user which **partner skills** the cycle relies on and where to get them:

- `/prd`, `/tdd`, and `/handoff` — all available in this marketplace
  (`/plugin install prd@kinchi22-claude-plugins`, `tdd@…`, `handoff@…`).
- The PRD template is not scaffolded here: `/prd` owns it and seeds
  `docs/prd/TEMPLATE.md` on first run.

Finally, suggest the first move: decide the next high-level goal and write its PRD.

## Notes

- **Don't auto-commit.** Leave the new files staged or unstaged for the user to review;
  creating the harness is itself a reviewable change. Mention they may want it on its
  own branch/commit.
- **Respect the glossary's authority.** If the project already has a glossary under a
  different name (e.g. `GLOSSARY.md`, `docs/domain.md`), don't create a competing one —
  point the `dev-cycle.md` reference at the existing file instead.
- **Keep it lean.** Don't add files the project didn't ask for. ADR scaffolding is
  included because the cycle and `/tdd` both reference ADRs; if the user doesn't want
  it, skip `docs/adr/`.
