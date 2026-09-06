# Plugins

This directory contains all plugins in the kinchi22-claude-plugins marketplace.

## Available Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [handoff](handoff/) | productivity | Writes a HANDOFF.md so the next agent with fresh context can continue this work (mirrored from ykdojo/claude-code-tips) |
| [prd](prd/) | engineering | Writes a milestone PRD: goal, user stories, and an ordered checklist of independently-shippable executable slices (each with an acceptance check); step 2 of the harness dev cycle |
| [harness-init](harness-init/) | engineering | Sets up or upgrades an agentic dev harness: thin CLAUDE.md, PRD → milestone → per-slice TDD → review → handoff cycle, authoritative docs/glossary.md, ADR template |
| [explain-diff](explain-diff/) | engineering | Explains a branch or PR diff as a self-contained prose HTML document, with inline-SVG diagrams and a test-case table |

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
