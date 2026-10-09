# PRD: <milestone name>

> Written with `/prd`. The centre of this document is the **slice checklist** — an
> ordered list of independently shippable, independently reviewable steps. Use the
> project's `docs/glossary.md` vocabulary throughout.

## Goal

The outcome this milestone delivers, phrased as a result for the user — not a task
list. One or two sentences.

## User stories

Who this is for and why they want it, one line each. Keep the role and the object in
`docs/glossary.md` vocabulary so the stories, slices, and tests all name things the
same way.

```
As a <role>, I want to <capability>, so that <benefit>.
```

- As a <role>, I want to <capability>, so that <benefit>.
- As a <role>, I want to <capability>, so that <benefit>.

## Context & constraints

Why now, what this depends on, what is explicitly out of scope. Link any relevant
ADRs (`docs/adr/`).

## Glossary touchpoints

Domain terms this milestone uses or introduces. New or changed terms must land in
`docs/glossary.md` as part of the slice that introduces them.

## Executable slices

Each slice is shippable on its own, reviewable in one PR, and has an acceptance check.
Mark `[impl]` for slices that go through the `/tdd` cycle and `[docs]`/`[chore]` for
slices the main session handles directly.

- [ ] **Slice 1 — <name>** `[impl]`
  - What: <the change>
  - Acceptance: <observable check that proves it works>
- [ ] **Slice 2 — <name>** `[docs]`
  - What: <the change>
  - Acceptance: <observable check>
- [ ] **Slice 3 — <name>** `[impl]`
  - What: <the change>
  - Acceptance: <observable check>

## Done when

The condition that marks the whole milestone complete (every slice checked and the
goal demonstrably met).
