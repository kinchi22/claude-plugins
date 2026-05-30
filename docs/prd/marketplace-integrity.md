# PRD: Marketplace integrity validation + CI

## Goal

Every change to the marketplace is automatically checked for structural integrity, so a
broken or out-of-sync `marketplace.json` / `plugins/` tree can never be merged to `main`.

## User stories

- As a marketplace maintainer, I want `marketplace.json` validated against the `plugins/`
  tree automatically, so that an out-of-sync or malformed marketplace never gets merged.
- As a contributor, I want one command (and CI) that confirms my new or edited plugin is
  correctly registered and well-formed, so that I get fast feedback before review.

## Context & constraints

- **Why now:** `marketplace.json` has been hand-edited several times while adding the
  `tdd`, `prd`, and `harness-init` plugins. There is no automated safety net catching
  drift between it and the `plugins/` tree.
- **Tooling:** Python 3 standard library only (zero dependencies); tests with `unittest`.
  The validator runs as a script and the suite as `python3 -m unittest discover`. The
  repo has no package manager.
- **CI:** GitHub Actions, triggered on push and PR to `main`; a failure blocks merge.
- **Out of scope:** validating the `plugins/README.md` table against the plugin set
  (check "D"); linting SKILL.md body content beyond frontmatter; version/semantic checks.
- No ADRs exist in the repo yet.

## Glossary touchpoints

This repo has no `docs/glossary.md` yet; if `harness-init` is run here, seed these terms.

- **registration sync** — a 1:1 correspondence between `plugins/<name>/` directories and
  `marketplace.json` entries.
- **orphan plugin** — a `plugins/<name>/` directory with no matching `marketplace.json`
  entry.
- **dangling entry** — a `marketplace.json` entry whose `source` points to a directory
  that does not exist.

## Executable slices

Each slice is independently shippable, reviewable in one PR, and leaves the validator
runnable and green on the current repo. Order widens coverage from a tracer bullet; CI
lands last as the safety net over everything built.

- [ ] **Slice 1 — Validator skeleton + check A (registration sync)** `[impl]` 🎯 tracer bullet
  - What: `scripts/validate_marketplace.py` loads `marketplace.json` and the `plugins/`
    tree, detects orphan plugins and dangling entries, prints each violation, and exits
    non-zero if any exist. `unittest` tests drive it.
  - Acceptance: running it on the current repo exits 0; tests that inject an orphan dir
    and a dangling entry each fail validation as expected.
- [ ] **Slice 2 — Check B (JSON validity + name/dir match + required files)** `[impl]`
  - What: extend the validator — every `marketplace.json`/`plugin.json` parses as JSON;
    each `plugin.json` `name` equals its directory name and its marketplace entry name;
    `plugin.json` and at least one `skills/*/SKILL.md` exist per plugin.
  - Acceptance: current repo passes; tests covering a name mismatch, a missing SKILL.md,
    and malformed JSON each fail validation.
- [ ] **Slice 3 — Check C (SKILL.md frontmatter)** `[impl]`
  - What: extend the validator — each `SKILL.md` has YAML frontmatter with a non-empty
    `name` and `description`.
  - Acceptance: current repo passes; a `SKILL.md` missing `description` fails validation.
- [ ] **Slice 4 — CI wiring (GitHub Actions)** `[chore]`
  - What: `.github/workflows/validate.yml` runs `python3 -m unittest discover` on push
    and PR to `main`; failure blocks merge.
  - Acceptance: the workflow YAML is valid and the job runs green on the current repo.

## Done when

The validator covers checks A + B + C and exits non-zero on any violation, exits 0 on the
current repo, the `unittest` suite is green, and GitHub Actions runs it on every push and
PR to `main`, blocking merge on failure.
