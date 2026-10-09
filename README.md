# kinchi22-claude-plugins

A personal Claude Code plugin marketplace: skills and mods I use for agentic coding.

## Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| [explain-diff](plugins/explain-diff/) | engineering | Explains a branch or PR diff as a self-contained prose HTML document, with inline-SVG diagrams and a test-case table |
| [comment-gc](plugins/comment-gc/) | engineering | Prunes stale, historical, and self-evident comments and compresses verbose ones, while changing zero lines of code |
| [usage-hud](plugins/usage-hud/) | productivity | A HUD above the prompt with the context bar, session cost, 5h/weekly rate limits, and a live prompt-cache countdown |

Retired plugins are kept for reference in [`archive/`](archive/) and are not installable.

## Installation

```bash
# Add the marketplace
/plugin marketplace add kinchi22/claude-plugins

# Install a plugin
/plugin install <plugin-name>@kinchi22-claude-plugins
```
