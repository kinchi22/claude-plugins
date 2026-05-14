# clarify-first

A skill that replaces plan mode by **driving every ambiguity out of a request before any code is written.** It asks one focused multiple-choice question at a time via `AskUserQuestion`, re-evaluating after every answer, until nothing important is unclear. Only then does it produce a final spec.

## Why

Plan mode produces a plan even when the request still has open questions. The plan then gets rewritten when reality intrudes. `clarify-first` flips this: questions first, plan last, no guesswork in between.

## When it triggers

Use cases:

- New features, components, endpoints, commands, skills
- Refactors, migrations, rewrites
- Bug fixes where the repro/scope/symptom is fuzzy
- Anything where scope, inputs/outputs, edge cases, constraints, or success criteria aren't fully nailed down

It deliberately skips trivial work — typo fixes, fully-specified single-file renames, read-only lookups, and "just do it" requests.

## How it works

1. **Restate the goal** in 2–4 sentences.
2. **Internally inventory unknowns** using a checklist covering scope, motivation, inputs, outputs, behavior, edge cases, constraints, success criteria, and stakeholders.
3. **Ask one focused question at a time** via `AskUserQuestion`, with 2–4 multiple-choice options and an implication on each. Investigates the codebase cheaply (~1 min) before each question so the question is grounded.
4. **Re-inventory after each answer.**
5. **Confirm and hand off** a final spec when the inventory is empty — written to the plan file in plan mode, or presented in chat otherwise.

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add github:kinchi22/claude-plugins

# Install
/plugin install clarify-first@kinchi22-claude-plugins
/reload-plugins
```

## Usage

Once installed, the skill triggers automatically on non-trivial requests. You can also invoke it explicitly:

> "Use clarify-first on this: I want to add comment threading to the article page."

The skill will ask one question at a time. You can short-circuit it at any point with "just decide" or "you pick" — it will summarize its assumptions and proceed.
