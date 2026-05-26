# grill-me

Interview-style skill that grills you on every branch of a plan or design until shared understanding is reached.

## Credit

This skill is sourced from [mattpocock/skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) by **Matt Pocock**, licensed under MIT (see [LICENSE](LICENSE)). The upstream repo bundles 14 skills under a single `mattpocock-skills` plugin; this entry republishes only the `grill-me` skill.

If you want the full set, install Matt's plugin directly from his repo instead.

## What it does

Asks you one focused question at a time about a plan or design, recommending an answer for each, and walks the decision tree until every dependency between decisions is resolved. If a question can be answered by reading the codebase, the skill explores the code instead of asking.

Good for: stress-testing a half-formed plan, pressure-testing architectural choices, surfacing hidden assumptions.

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add kinchi22/claude-plugins

# Install
/plugin install grill-me@kinchi22-claude-plugins
/reload-plugins
```

## Usage

> "Grill me on this plan."

Or just describe a plan and the skill description (with its "grill me" trigger phrase) will pull it in.

## Related

- [`clarify-first`](../clarify-first/) — similar idea but optimized for resolving ambiguity *before* a plan is written. Use `clarify-first` for fresh requests; use `grill-me` to pressure-test an already-formed plan.
