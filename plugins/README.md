# Plugins

This directory contains all plugins in the kinchi22-claude-plugins marketplace.

## Available Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [explain-diff](explain-diff/) | engineering | Explains a branch or PR diff as a self-contained prose HTML document, with inline-SVG diagrams and a test-case table |
| [comment-gc](comment-gc/) | engineering | Collects accumulated comment garbage - stale/historical/self-evident comments deleted, verbose ones compressed - while changing zero lines of code, proven by a bundled guard script |
| [usage-hud](usage-hud/) | productivity | A one-line HUD above the prompt with the context bar, session cost, 5h/weekly rate limits, and a live prompt-cache countdown (a function-hooks mod) |

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
