---
name: jira-estimate-summarizer
description: Summarize estimate fields (original estimate, time spent) from JIRA child tickets to their parent ticket. This skill should be used when users want to aggregate or roll up time tracking data from child issues linked via "contains" relationship to update the parent ticket. Supports single ticket from chat input or batch processing from CSV file.
---

# JIRA Estimate Summarizer

## Overview

This skill aggregates time tracking fields (original estimate, time spent) from child JIRA tickets and updates the parent ticket with the summarized values. It uses the "contains" link relationship to identify child tickets.

## Workflow

### Step 1: Parse Input

Determine the input source and extract parent ticket keys.

**From chat message:**
- Extract ticket key(s) directly from user message (e.g., "PROJECT-123" or "PROJECT-123, PROJECT-456")

**From CSV file:**
- Read the CSV file using the Read tool
- Parse ticket keys from the single column (one key per row)
- Skip header row if present

### Step 2: Process Each Parent Ticket

For each parent ticket key, execute the following steps:

#### 2.1 Get Parent Ticket Details

Use `mcp__jira__jira_get_issue` to fetch the parent ticket:
- Set `fields` to include: `summary,timetracking,issuelinks`
- Check current `originalEstimate` and `timeSpent` values from timetracking field

#### 2.2 Find Child Tickets via "contains" Link

From the parent ticket's `issuelinks` field:
- Filter links where `type.name` is "contains" (or similar, check `type.outward` = "contains")
- Extract the `outwardIssue.key` for each child ticket

If no child tickets found, log and skip to next parent.

#### 2.3 Get Time Tracking from Each Child

For each child ticket key, use `mcp__jira__jira_get_issue`:
- Set `fields` to: `timetracking,summary`
- Extract `originalEstimateSeconds` and `timeSpentSeconds` from the `timetracking` field

#### 2.4 Calculate Totals

Sum up from all children:
- `totalOriginalEstimateSeconds` = sum of all children's `originalEstimateSeconds`
- `totalTimeSpentSeconds` = sum of all children's `timeSpentSeconds`

Convert seconds to JIRA time format for display:
- 1 week = 5 days = 40 hours
- 1 day = 8 hours
- Format example: "2w 3d 4h" or "1d 2h 30m"

#### 2.5 Update Parent Ticket

Use `mcp__jira__jira_update_issue` with conditional logic:

**Original Estimate:**
- Only update if parent's current `originalEstimate` is null/empty/0
- Set `originalEstimate` in the `fields` parameter

**Time Spent:**
- Always update by adding a worklog entry if totalTimeSpentSeconds > 0
- Note: Direct timeSpent update may not be supported; use `mcp__jira__jira_add_worklog` if needed

**Update format:**
```
fields: {
  "timetracking": {
    "originalEstimate": "2w 3d"  // only if parent has no estimate
  }
}
```

### Step 3: Generate Summary Report

After processing all tickets, provide a summary:

```
## JIRA Estimate Summarization Report

| Parent Ticket | Children | Original Estimate | Time Spent | Updated |
|---------------|----------|-------------------|------------|---------|
| PROJECT-123   | 5        | 2w 3d             | 1w 2d      | Yes     |
| PROJECT-456   | 3        | 1w                | 3d         | Partial (estimate existed) |
```

## Time Format Conversion Reference

**Seconds to JIRA format:**
- 60 seconds = 1 minute (1m)
- 3600 seconds = 1 hour (1h)
- 28800 seconds = 1 day (1d) [8 hours]
- 144000 seconds = 1 week (1w) [5 days]

**Conversion formula:**
```
weeks = floor(seconds / 144000)
remaining = seconds % 144000
days = floor(remaining / 28800)
remaining = remaining % 28800
hours = floor(remaining / 3600)
remaining = remaining % 3600
minutes = floor(remaining / 60)
```

## Error Handling

- If a ticket key is invalid, log the error and continue with next ticket
- If child tickets have no time tracking data, treat as 0
- If JIRA API rate limits are hit, pause and retry
- Report any tickets that failed to update in the summary

## Example Usage

**Single ticket from chat:**
> "Summarize estimates for PROJECT-123"

**Multiple tickets from chat:**
> "Roll up time tracking for PROJECT-123 and PROJECT-456"

**Batch from CSV:**
> "Process the tickets in /path/to/tickets.csv and summarize their child estimates"
