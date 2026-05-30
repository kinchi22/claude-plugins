# Development cycle

How work flows in this project. The cycle exists so that each session has a small,
reviewable scope and the next session can pick up cleanly. Follow it for any change
larger than a one-off fix; for trivial edits, use judgment.

The loop, end to end:

```
decide goal (high-level)
   → /prd  (detailed PRD with a checklist of executable slices)
      → commit PRD + cut milestone branch
         → per slice:  branch off milestone → /tdd (if code) → review/PR → merge
            → /handoff  (hand the next session a clean starting point)
```

## 1. Decide the next goal

Pick the next outcome worth a milestone — phrased as a result, not a task list.
"Users can reset their password by email," not "add a token table." Keep it small
enough that its slices fit in a few sessions.

## 2. Write the PRD with `/prd`

Use the `/prd` skill to write `docs/prd/<milestone-slug>.md`. A PRD here is not a
wall of prose — its centre is an **ordered checklist of executable slices**, where
each slice is independently shippable and reviewable, and carries its own acceptance
check. The `/prd` skill writes the PRD and seeds `docs/prd/TEMPLATE.md`, which is the
shape to follow.

Write the PRD in the project's own vocabulary — consult `docs/glossary.md` and reuse
its terms so the PRD, the tests, and the code all speak the same language.

## 3. Commit the PRD and cut the milestone branch

```
git checkout -b milestone/<milestone-slug>
git add docs/prd/<milestone-slug>.md && git commit -m "docs(prd): <milestone-slug>"
```

Order can flip: if the team's rule is branch-first, cut the branch before writing the
PRD. The invariant is that the PRD is committed on the milestone branch before slices
begin.

## 4. Execute slices, one at a time

For each slice in the PRD checklist:

- Cut a slice branch **from the milestone branch**:
  `git checkout milestone/<milestone-slug> && git checkout -b slice/<milestone-slug>/<slice-slug>`
- **Implementation slice** → use `/tdd`. Red-green-refactor in vertical slices: one
  test → minimal code → repeat. Tests verify behavior through public interfaces and
  speak the glossary's language.
- **Non-implementation slice** (docs, config, scaffolding) → no TDD needed; the main
  session handles it directly.
- Tick the slice off in the PRD checklist when its acceptance check passes.

One slice at a time keeps each diff small enough to review well and easy to revert.

## 5. Review the slice, then merge

Open a PR from the slice branch into the milestone branch (or get direct review if
the project doesn't use PRs). Address feedback, then merge. The milestone branch
accumulates reviewed slices; it merges to the default branch once the PRD's checklist
is complete and the milestone outcome is met.

## 6. Hand off with `/handoff`

When you pause, finish a slice, or finish the milestone, run `/handoff` to write
`HANDOFF.md` — goal, progress, what worked, what didn't, next steps. Start the next
piece of work in a fresh session pointed at that handoff, so context stays lean.

---

## Cross-cutting rules

**The glossary is authoritative.** `docs/glossary.md` is the single source of truth
for domain terms. Consult it before naming types, functions, tests, or PRD sections.
When you introduce or rename a domain concept, update the glossary in the *same*
change — code and glossary never drift apart.

**Record decisions as ADRs.** For significant or hard-to-reverse choices, add an ADR
under `docs/adr/` (see `docs/adr/TEMPLATE.md`). Respect existing ADRs in any area you
touch; if you contradict one, supersede it explicitly rather than silently diverging.

**Branch & commit hygiene.** Milestone branches: `milestone/<slug>`. Slice branches:
`slice/<milestone-slug>/<slice-slug>`, always cut from the milestone branch. Keep
commits scoped to one logical change.

**Verification command.** Run the project's checks before calling a slice done:

<!-- harness-init: set this to the project's real test/lint command, e.g. `npm test`, `pytest`, `go test ./...` -->
```
<TEST_COMMAND>
```
