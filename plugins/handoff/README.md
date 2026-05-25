# handoff

Write or update a `HANDOFF.md` so the next agent with fresh context can pick up exactly where this conversation left off.

## Credit

This skill is sourced from [ykdojo/claude-code-tips](https://github.com/ykdojo/claude-code-tips/blob/main/skills/handoff/SKILL.md) by **YK (ykdojo)**. The upstream repo bundles it together with five other DX skills under a single `dx` plugin; this entry republishes only the `handoff` skill for convenience.

All credit for the skill content goes to the original author. If you want the full set (clone, half-clone, gha, reddit-fetch, review-claudemd), install the upstream plugin directly from ykdojo's marketplace instead.

## What it does

When the conversation is getting long or you want to start fresh, this skill writes a `HANDOFF.md` at the project root capturing:

- **Goal** — what we're trying to accomplish
- **Current Progress** — what's been done
- **What Worked** — approaches that succeeded
- **What Didn't Work** — dead ends (so the next agent doesn't repeat them)
- **Next Steps** — concrete action items

Then you start a new conversation with just that file path as context.

## Installation

```bash
# Add the marketplace (if not already added)
/plugin marketplace add kinchi22/claude-plugins

# Install
/plugin install handoff@kinchi22-claude-plugins
/reload-plugins
```

## Usage

> "Write a handoff doc for this session."

Or just ask anything that implies wrapping up — the skill description triggers it automatically.
