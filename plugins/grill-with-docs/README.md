# grill-with-docs

Interview-style skill that grills you on a plan while challenging it against your project's existing domain model, sharpens terminology, and updates documentation (`CONTEXT.md`, ADRs) inline as decisions crystallise.

## Credit

This skill is sourced from [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md) by **Matt Pocock**, licensed under MIT (see [LICENSE](LICENSE)). The upstream repo bundles many skills under a single `mattpocock-skills` plugin; this entry republishes only the `grill-with-docs` skill along with its `CONTEXT-FORMAT.md` and `ADR-FORMAT.md` supporting files.

If you want the full set, install Matt's plugin directly from his repo instead.

## What it does

Asks you one focused question at a time about a plan, recommending an answer for each, and walks the decision tree until every dependency between decisions is resolved. Beyond plain grilling, it:

- **Challenges your language against the glossary.** When a term conflicts with the existing definitions in `CONTEXT.md`, it calls it out.
- **Sharpens fuzzy terms.** Vague or overloaded words get pushed toward a precise canonical term.
- **Cross-references claims with code.** When you say "it works like X," it checks whether the code agrees and surfaces contradictions.
- **Captures decisions as they happen.** Resolved terms are written to `CONTEXT.md` inline; genuinely hard-to-reverse, surprising trade-offs are offered as ADRs in `docs/adr/`.

Files are created lazily — only when there's actually something to write.

Good for: stress-testing a plan against a project's established domain language, keeping a living glossary, and recording architectural decisions without ceremony.

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add kinchi22/claude-plugins

# Install
/plugin install grill-with-docs@kinchi22-claude-plugins
/reload-plugins
```

## Usage

> "Grill me on this plan and keep the docs updated."

Or describe a plan and the skill description (triggering on stress-testing against your project's language and documented decisions) will pull it in.

## Related

- [`grill-me`](../grill-me/) — the lighter sibling: same one-question-at-a-time grilling, but without the domain-model challenge or documentation updates. Use `grill-me` for a quick pressure-test; use `grill-with-docs` when you want the session to also sharpen terminology and write `CONTEXT.md`/ADRs.
- [`clarify-first`](../clarify-first/) — optimized for resolving ambiguity *before* a plan is written, rather than pressure-testing an already-formed one.
