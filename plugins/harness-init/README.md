# harness-init

Set up (or upgrade) an **agent development harness** in a project — the files that make
every future session follow the same coding discipline and development loop.

Because the harness is just version-controlled files, it's reviewable and loads
automatically: Claude Code reads `CLAUDE.md` and everything it `@import`s on every
session.

## What it creates

```
CLAUDE.md                          # thin; @imports the rule modules
.claude/rules/
  ├── coding-guidelines.md         # think-before-coding, simplicity, surgical, goal-driven
  └── dev-cycle.md                 # the development loop + branch/PR/glossary/ADR conventions
docs/
  ├── glossary.md                  # authoritative domain vocabulary
  └── adr/TEMPLATE.md              # ADR template
```

The PRD template (`docs/prd/TEMPLATE.md`) is **not** created here — it's owned by the
[`prd`](../prd/) skill, which seeds it on first run.

## The development cycle it establishes

```
decide goal (high-level)
   → /prd   (PRD with a checklist of executable slices)
      → commit PRD + cut milestone branch
         → per slice: branch off milestone → /tdd (if code) → review/PR → merge
            → /handoff  (clean starting point for the next session)
```

- **`docs/glossary.md` is authoritative** — code, tests, PRDs, and ADRs all speak its
  vocabulary, and it's updated in the same change that introduces a term.
- Each **slice** is independently shippable and reviewable; implementation slices go
  through the `/tdd` red-green-refactor loop, docs/chore slices don't.

## Idempotent

Safe to re-run. It detects existing files and merges: the `CLAUDE.md` harness block is
updated in place between markers, harness-managed rule files are updated with your
confirmation, and project-owned files (`glossary.md`, templates) are created only if
missing — never overwritten.

## Partner skills

The cycle calls these skills; install them from this marketplace:

| Skill | Role | Source |
|-------|------|--------|
| [`prd`](../prd/) | Write the PRD with its slice checklist | this marketplace |
| [`tdd`](../tdd/) | Red-green-refactor for implementation slices | this marketplace |
| [`handoff`](../handoff/) | Write HANDOFF.md for the next session | this marketplace |

## Installation

```bash
/plugin marketplace add kinchi22/claude-plugins
/plugin install harness-init@kinchi22-claude-plugins

# Then, inside a project you want to set up:
/harness-init
```
