---
name: prd
description: Write a milestone PRD by grilling the user first. Like /grill-me, it interrogates one question at a time — each with a recommended answer, exploring the codebase and docs/glossary.md instead of asking when it can — walking the decision tree (goal → users → scope → terms → slice boundaries → acceptance checks) until you reach shared understanding, then writes docs/prd/<slug>.md whose centre is an ordered checklist of independently-shippable executable slices. Use whenever the user wants to plan or spec a milestone or feature, write a PRD, or break work into slices before implementation. Step 2 of the harness dev cycle: after deciding a high-level goal, before cutting the milestone branch.
---

# PRD

Turn a high-level goal into a milestone PRD whose centre is an **ordered checklist of
executable slices**. The slices are the unit the rest of the cycle runs on: each becomes
a branch off the milestone branch, goes through `/tdd` if it's code, and is reviewed and
merged on its own. A good PRD makes that loop almost mechanical; a vague one forces
constant re-planning mid-implementation — which is exactly why this skill **grills you
before it writes anything**.

This skill produces `docs/prd/<milestone-slug>.md`. It does **not** commit or branch —
that's the next step in the cycle (see the project's `dev-cycle.md`).

## How this works: grill first, write second

Follow the `/grill-me` concept. Don't draft a PRD from a one-line goal and hand it over —
interrogate the plan until you and the user reach genuine shared understanding, then
write it down.

- **One question at a time.** Don't dump a questionnaire. Ask, hear the answer, let it
  shape the next question. A PRD is a tree of decisions where later branches depend on
  earlier ones — walk it in order.
- **Always recommend an answer.** For every question, give your recommended answer and a
  one-line why, so the user can just confirm or push back rather than start from blank.
- **Explore instead of asking when you can.** If a question is answerable from the
  codebase, `docs/glossary.md`, existing PRDs, or ADRs — go look, don't make the user
  recite what's already written. Spend their attention only on genuine decisions.
- **Resolve each branch before moving on.** When an answer opens a sub-decision, finish
  that branch before backing out. Keep going until nothing important is unresolved —
  that convergence is the signal you're ready to write.

## The decision tree to walk

Roughly in dependency order. Skip what's already settled; dig in where it's fuzzy.

1. **Goal / outcome.** What result does this milestone deliver, for whom? Phrased as an
   outcome, not a task list. Pin down what "done" looks like from the outside.
2. **Users & stories.** Which roles benefit, and why? Drive each toward
   `As a <role>, I want <capability>, so that <benefit>` — roles and objects in
   `docs/glossary.md` vocabulary.
3. **Scope boundaries.** What's explicitly *out* of scope for this milestone? Ambiguous
   scope is the most common source of bloated slices later — make the user say no to
   things now.
4. **Glossary touchpoints.** Which domain terms does this use? Does it introduce or
   change any? New/changed terms become a slice that updates `docs/glossary.md` alongside
   the code.
5. **Constraints & dependencies.** What must this respect — existing ADRs, other
   in-flight work, external deadlines, tech constraints? What has to exist first?
6. **Slice decomposition.** The hard part — see below. Grill the boundaries, the order,
   and the acceptance check of each slice.
7. **Done-when.** The single condition that means the whole milestone is complete.

## The hard part: decomposing into slices

This is where the skill earns its keep, and where the grilling gets most concrete.

A slice is **vertical, not horizontal** — a thin end-to-end thread that delivers a sliver
of the outcome, not a layer (don't make "the database", "the API", "the UI" separate
slices). This mirrors the tracer-bullet idea in `/tdd`: the first slice proves the whole
path works on the narrowest possible case; later slices widen it.

Grill each candidate slice against three tests, and split or merge until it passes:

- **Independently shippable** — could it merge to the milestone branch on its own without
  leaving the project broken?
- **Reviewable in one PR** — small enough that a reviewer holds it in their head? If it'd
  be a sprawling diff, it's more than one slice.
- **Backed by an acceptance check** — one observable thing that proves it works ("a user
  with an expired token gets a 401", not "auth is implemented"). For `[impl]` slices this
  check is exactly what `/tdd` drives toward.

Tag each slice by how it's executed:

- `[impl]` — code; goes through the `/tdd` red-green-refactor loop.
- `[docs]` / `[chore]` — docs, config, scaffolding; the main session handles it directly.

Order by dependency and risk: the tracer bullet first (riskiest end-to-end path, narrowest
case), then widen. Push back hard when a slice isn't independently shippable, has no
observable acceptance check, or is several slices wearing a trenchcoat.

## PRD structure

The canonical PRD shape is bundled with this skill at **`assets/prd-template.md`**:
Goal, User stories, Context & constraints, Glossary touchpoints, Executable slices,
Done when.

Precedence: if the project has its own `docs/prd/TEMPLATE.md`, that is authoritative —
follow it. Otherwise seed the project's copy from `assets/prd-template.md` (see the
workflow) and follow that. Either way there is one shape per project, and this skill owns
the default.

## Workflow

1. **Orient.** Read `docs/glossary.md` and skim relevant code / ADRs. If the project has
   no `docs/prd/TEMPLATE.md`, seed it from this skill's `assets/prd-template.md` so the
   project gets a customizable copy; then follow whichever template the project now has.
   Gather what you can before asking anything.
2. **Grill.** Walk the decision tree above, one recommended-answer question at a time,
   exploring instead of asking where possible, until the plan converges.
3. **Confirm the slug.** Settle a kebab-case milestone slug (e.g. `password-reset`).
4. **Write** the PRD to `docs/prd/<milestone-slug>.md`.
5. **Stop there.** Don't commit or branch. Point the user to the next step: commit the
   PRD and cut the `milestone/<slug>` branch (or branch-first per the project's rule),
   then work the slices one at a time.
