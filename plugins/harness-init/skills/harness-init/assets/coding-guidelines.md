# Coding guidelines

Behavioral guidelines that bias toward caution over speed. For trivial tasks, use
judgment. Adapted from Andrej Karpathy's `CLAUDE.md`
(github.com/multica-ai/andrej-karpathy-skills).

## 1. Think before coding

Don't assume, don't hide confusion, surface tradeoffs.

- State assumptions explicitly; if uncertain, ask.
- If multiple interpretations exist, present them — don't silently pick one.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what's confusing, and ask.

When the answer depends on a domain term, check `docs/glossary.md` first — the word
may already have a settled meaning here.

## 2. Simplicity first

The minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or configurability that wasn't requested.
- No error handling for impossible scenarios.
- If you wrote 200 lines and it could be 50, rewrite it.

Ask: "Would a senior engineer call this overcomplicated?" If yes, simplify.

## 3. Surgical changes

Touch only what you must. Clean up only your own mess.

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match the existing style, even if you'd do it differently.
- Remove imports/variables/functions that *your* change made unused; leave
  pre-existing dead code alone (mention it instead of deleting it).

The test: every changed line should trace directly to the request.

## 4. Goal-driven execution

Define success criteria, then loop until verified.

Turn vague tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass."
- "Fix the bug" → "Write a test that reproduces it, then make it pass."
- "Refactor X" → "Ensure tests pass before and after."

For multi-step work, state a brief plan with a check per step:

```
1. [step] → verify: [check]
2. [step] → verify: [check]
```

Strong success criteria let you work independently; weak ones ("make it work")
force constant clarification. This is why slices in a PRD each carry their own
acceptance check — see `dev-cycle.md`.
