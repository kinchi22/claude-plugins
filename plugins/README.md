# Plugins

This directory contains all plugins in the kinchi22-claude-plugins marketplace.

## Available Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [clarify-first](clarify-first/) | productivity | Replaces plan mode by asking one focused question at a time until every ambiguity is resolved, then produces a spec |

## Installation

```bash
# Add the marketplace
/plugin marketplace add github:kinchi22/claude-plugins

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
