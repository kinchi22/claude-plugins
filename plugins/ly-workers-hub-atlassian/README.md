# ly-workers-hub-atlassian

Atlassian integration for Workers Hub with Jira and Confluence MCP servers and related skills.

## MCP Servers

This plugin provides two MCP servers:

| Server | Description |
|--------|-------------|
| **jira** | Access Jira issues, projects, sprints, and time tracking |
| **confluence** | Access Confluence pages, spaces, and content |

Both servers use the LINE Corp Flava MCP Connector.

## Skills

### jira-estimate-summarizer

Summarize estimate fields (original estimate, time spent) from JIRA child tickets to their parent ticket via "contains" relationship.

**Usage:**
- Provide a single ticket key: `PROJECT-123`
- Provide multiple tickets: `PROJECT-123, PROJECT-456`
- Provide a CSV file with ticket keys

## Installation

Install this plugin to get:
- Jira and Confluence MCP server connections
- Skills for Atlassian-related workflows
