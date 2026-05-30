# prd

Write a milestone **PRD** whose centre is an ordered checklist of **executable slices** —
by **grilling you first**.

Following the [`/grill-me`](../grill-me/) concept, the skill interrogates the plan one
question at a time (each with a recommended answer, exploring the codebase and
`docs/glossary.md` instead of asking when it can) and walks the decision tree until you
reach shared understanding — *then* it writes the PRD. A vague PRD forces constant
re-planning mid-implementation; grilling up front is how it avoids that.

This is **step 2** of the `harness-init` development cycle: after you decide a high-level
goal and before you cut the milestone branch. The slices it produces are the unit the
rest of the cycle runs on — each becomes a branch off the milestone branch, goes through
`/tdd` if it's code, and is reviewed and merged on its own.

## What a PRD here contains

- **Goal** — the outcome, as a result for the user.
- **User stories** — `As a <role>, I want <capability>, so that <benefit>.`
- **Context & constraints** — dependencies, out-of-scope, linked ADRs.
- **Glossary touchpoints** — domain terms used or introduced (new terms land in
  `docs/glossary.md` as part of the slice that introduces them).
- **Executable slices** — an ordered checklist; each slice is independently shippable,
  reviewable in one PR, tagged `[impl]` / `[docs]` / `[chore]`, and carries an
  observable acceptance check. `[impl]` slices' checks are what `/tdd` drives toward.
- **Done when** — the milestone-complete condition.

## Design notes

- **Vertical slices, not horizontal layers.** The first slice is a tracer bullet that
  proves the whole path on the narrowest case; later slices widen it. (Same philosophy
  as `/tdd`.)
- **Owns the PRD shape, respects the project.** The canonical template ships with this
  skill (`assets/prd-template.md`); on first run it seeds the project's
  `docs/prd/TEMPLATE.md`, and once that exists it is authoritative and the skill follows
  it. PRDs are written in `docs/glossary.md` vocabulary.
- **Plans, doesn't commit.** It writes `docs/prd/<slug>.md` and stops — committing the
  PRD and cutting `milestone/<slug>` is the next step in the cycle.

## Installation

```bash
/plugin marketplace add kinchi22/claude-plugins
/plugin install prd@kinchi22-claude-plugins

# Then, inside a project:
/prd
```

## Related

- [`grill-me`](../grill-me/) — the relentless-interview concept this skill applies to PRD writing
- [`harness-init`](../harness-init/) — establishes the dev cycle and the `docs/prd/TEMPLATE.md` this skill follows
- [`tdd`](../tdd/) — drives each `[impl]` slice's acceptance check
- [`handoff`](../handoff/) — hands the next session a clean starting point
