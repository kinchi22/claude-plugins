# Plugins

This directory contains all plugins in the kinchi22-claude-plugins marketplace.

## Available Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [clarify-first](clarify-first/) | productivity | Replaces plan mode by asking one focused question at a time until every ambiguity is resolved, then produces a spec |
| [handoff](handoff/) | productivity | Writes a HANDOFF.md so the next agent with fresh context can continue this work (mirrored from ykdojo/claude-code-tips) |
| [grill-me](grill-me/) | productivity | Interviews you relentlessly about a plan or design until shared understanding is reached (mirrored from mattpocock/skills, MIT) |
| [grill-with-docs](grill-with-docs/) | productivity | Grilling session that challenges your plan against the domain model and updates docs (CONTEXT.md, ADRs) inline (mirrored from mattpocock/skills, MIT) |
| [tdd](tdd/) | engineering | Test-driven development with the red-green-refactor loop, vertical slices, and behavior-focused tests (mirrored from mattpocock/skills, MIT) |
| [prd](prd/) | engineering | Writes a milestone PRD: goal, user stories, and an ordered checklist of independently-shippable executable slices (each with an acceptance check); step 2 of the harness dev cycle |
| [harness-init](harness-init/) | engineering | Sets up or upgrades an agentic dev harness: thin CLAUDE.md, PRD → milestone → per-slice TDD → review → handoff cycle, authoritative docs/glossary.md, ADR template |

## Installation

```bash
# Add the marketplace
/plugin marketplace add kinchi22/claude-plugins

# Install a specific plugin
/plugin install <plugin-name>@kinchi22-claude-plugins
```

## Plugin Structure

Each plugin follows the standard Claude Code plugin structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── commands/                # Slash commands (optional)
├── agents/                  # Specialized agents (optional)
├── skills/                  # Agent Skills (optional)
│   └── skill-name/
│       └── SKILL.md
├── hooks/                   # Event handlers (optional)
├── .mcp.json                # External tool configuration (optional)
└── README.md                # Plugin documentation
```
