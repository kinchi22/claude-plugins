---
name: clarify-first
description: Drive every open question out of a user's request before any implementation begins. Use this skill whenever the user asks for a feature, refactor, bug fix, design change, migration, or any non-trivial change whose scope, inputs, outputs, edge cases, or success criteria are not fully specified — even when the user doesn't explicitly ask for clarification, and even when plan mode is active. Asks one focused question at a time via the AskUserQuestion tool, re-evaluating after every answer, until nothing important is ambiguous, then produces a final spec. Prefer this over jumping straight into a plan whenever a request has open questions.
---

# Clarify-First

## Why this skill exists

Plans built on guesswork get rewritten. The cheapest moment to fix a misunderstanding is *before* code is written, and the cheapest way to fix one is a short, specific question. This skill enforces a discipline: **no implementation, and no full plan, until the picture is clear.** It surfaces ambiguity, asks one focused question at a time, and only writes the final spec when every blocking unknown is resolved.

## When to use this skill

Use it when the user asks for any of:

- A new feature, page, component, endpoint, command, or skill
- A refactor, migration, or rewrite
- A bug fix where the symptom, repro, or scope is fuzzy
- A design change, UX tweak, or copy change with implied trade-offs
- Anything where you'd otherwise be guessing at scope, inputs/outputs, edge cases, constraints, or success criteria

## When to skip

Skip the full workflow for genuinely small or fully-specified work:

- Lookups and read-only questions ("where is X defined?", "what does Y do?")
- Single-file mechanical edits the user fully specified (typo fixes, simple renames with a target name)
- Tasks where the user has already given a complete spec, or has explicitly said "just do it" / "use your best judgment"

If you're unsure whether the work is trivial enough to skip, run the workflow — one question costs little, a wrong implementation costs more.

## The workflow

### Phase 1 — Restate the goal

In one short paragraph (2–4 sentences), write back what you understand the user wants, including *why* they want it where you can infer it. This is the cheapest miscommunication check available — the user can correct you in a single message before any question budget is spent.

Example: *"You want a dark-mode toggle in the dashboard so users on night shifts aren't blinded — visible from any page, persisting across sessions. Correct?"*

### Phase 2 — Inventory unknowns

Internally walk the **ambiguity checklist** (see below) and list every unknown that would change the implementation. Don't show this list to the user — it's a thinking aid that keeps you from missing categories.

### Phase 3 — Ask one question at a time

This is the heart of the skill. Loop:

1. **Investigate cheaply first.** Spend up to ~1 minute reading code, grepping, checking memory, or scanning docs so the question is grounded in the actual codebase and you don't ask about things you could have discovered. A specific, informed question ("I see `Settings.tsx` and `Preferences.tsx` — which one should the toggle live in?") earns more trust than a generic one ("Where should the toggle go?").

2. **Pick the single most blocking unknown.** The one whose answer would most change the plan. Answers near the top of the dependency chain (scope, motivation, where it lives) usually beat answers at the bottom (button color, animation length).

3. **Ask one question via the `AskUserQuestion` tool.**
   - 2–4 concrete options. Each option has a one-line description of its implication / trade-off.
   - If there's a sensible default, list it first and tag the label "(Recommended)".
   - "Other" is always available automatically — let the user type free text if none of your options fit.
   - One concept per question. If your question contains "and" or "or", split it into two questions and ask the more blocking one now.

4. **After the answer, re-inventory.** New unknowns may have appeared; previously important ones may now be moot. Repeat from step 1.

### Phase 4 — Confirm completeness

When the inventory is empty, summarize the final spec using the template below and explicitly ask: *"Anything missing or wrong before I start?"* — one last sanity check. If the user adds something, fold it in and ask again. If they say "looks good", proceed to Phase 5.

### Phase 5 — Hand off

- **In plan mode:** Write the spec into the plan file you were given, then call `ExitPlanMode` so the user can approve.
- **Outside plan mode:** Present the spec in chat. If the user has said "go", begin implementing; otherwise wait.
- Either way, the spec is the contract for what comes next.

## The ambiguity checklist

Walk this list during Phase 2 and after every answer. Skip categories that genuinely don't apply, but check them — missing a category is the most common failure mode.

- **Scope.** What is in. What is out. What is explicitly *not* being changed. Are there related-looking things the user does *not* want touched?
- **Motivation / why.** What problem is this solving, for whom, and how will the user know it worked? The why often disqualifies "obvious" solutions.
- **Inputs.** Data shapes, file formats, sources, sample values. For a CSV, what columns? For an API call, what shape?
- **Outputs / artifacts.** Return values, side effects, formats, where files land, what the user sees afterward.
- **User-facing behavior.** UX details, defaults, error messages, empty states, loading states, copy.
- **Edge cases.** Empty input, huge input, malformed input, concurrent calls, permission denied, network failure, timeouts.
- **Constraints.** Performance budgets, dependency choices, framework version, browser/OS support, security/compliance, accessibility.
- **Success criteria.** How will the user verify it works? Tests? Manual repro? A specific metric moving?
- **Stakeholders / approval.** Who needs to sign off? What's reversible vs. one-way? Any deadlines or freezes?

## Question-writing guidelines

The quality of each question determines whether the user feels helped or interrogated.

- **Prefer multiple-choice over open-ended.** Forced choices are faster to answer and reveal trade-offs you've already thought about. Open-ended is fine when the answer space is genuinely wide — but try to narrow it first.
- **Each option carries an implication.** "Store the preference in localStorage" vs "Store in the user record" — describe the consequence in one line so the user is choosing between trade-offs, not labels.
- **Recommend a default when one is real.** First option labeled "(Recommended)". Only when you actually have a preferred answer based on what you've read; otherwise it's noise.
- **Don't ask trivia you could grep.** "What's the test runner?" → look at `package.json` yourself.
- **One concept per question.** If you're tempted to ask "What's the input format, and where does it go?", split it. Ask the more blocking half first.
- **Phrase choices, not yes/no.** "Which storage layer?" beats "Should we use localStorage?". Yes/no questions burn a turn and a half of the answer space.

## Stop conditions

Stop asking questions when **any** of these is true:

- The ambiguity checklist comes up empty.
- The user says "just decide" / "you pick" / "stop asking" / "enough questions". When this happens, summarize the assumptions you're about to make and proceed — don't push back.
- The remaining unknowns are no longer blocking — their answers wouldn't change the plan in any meaningful way. Don't loop on details.
- You've asked ~10 questions without convergence. At that point, summarize what you've learned, list what's still open, and ask the user whether to keep digging or proceed with documented assumptions.

## Anti-patterns to avoid

Each comes with the *why* so you can judge edge cases instead of blindly avoiding the shape:

- **Bundling.** Asking three things in one turn defeats the one-at-a-time discipline — each answer is supposed to reshape what comes next. *Fix:* split, ask the most blocking one.
- **Trivia.** "What's the package manager?" annoys the user and signals you didn't look. *Fix:* spend the cheap minute reading the repo first.
- **Yes/no when a real choice exists.** Wastes a turn. *Fix:* present the real choices.
- **Aesthetic-bikeshed loops.** Asking about colors, naming, or wording before scope is locked. *Fix:* questions in dependency order — scope before surface.
- **Producing a plan while questions remain.** Defeats the entire point. *Fix:* if you're tempted to write the plan, that's the moment to ask the next question instead.
- **Treating the user's first message as fixed.** Their request was a starting point, not a specification. *Fix:* assume there *is* ambiguity, even if it isn't visible yet.

## Final-spec template

Fill this in during Phase 4. Use the same headings even if a section is short — consistency makes it scannable.

```markdown
## Goal
<one paragraph: what we're building and why>

## Scope
**In:** <bulleted list>
**Out:** <bulleted list — things explicitly not being changed>

## Inputs
<data shapes, formats, sources, sample values>

## Outputs / artifacts
<return values, side effects, files written, what the user sees>

## Behavior & edge cases
<UX details, error handling, edge cases the user has now told us how to handle>

## Constraints
<performance, deps, framework, compatibility, security, a11y>

## Success criteria
<how the user will verify it works>

## Files likely to change
<paths>

## Open assumptions (if any)
<assumptions made when the user told us to stop asking>
```

## Worked example (abridged)

User: *"Add a dark mode toggle to the dashboard."*

Restated goal: *"You want a dark-mode toggle in the dashboard so users on night shifts aren't blinded — visible somewhere persistent, sticking across sessions. Correct?"* → User: *"Yes."*

Q1 (scope, most blocking): "Which surface should the toggle live in?"
- Header (visible from every page) (Recommended)
- Settings page only
- A floating widget

→ "Header."

Q2 (persistence, next most blocking): "Where should the preference persist?"
- Per-user in the user record (syncs across devices) (Recommended)
- localStorage (per-device, no sync)

→ "User record."

Q3 (system preference): "Should we respect the OS `prefers-color-scheme` for first-time users?"
- Yes, default to OS (Recommended)
- No, default to light

→ "Yes."

Q4 (scope check): "Are non-dashboard pages (auth, marketing) in scope for this pass, or dashboard-only?"
- Dashboard-only (Recommended)
- Everything

→ "Dashboard-only."

Inventory empty — produce spec, confirm, hand off.

---

The discipline is small and the payoff is large: a few minutes of focused questions buys you a plan that doesn't need to be redone after the first wrong assumption hits a wall.
