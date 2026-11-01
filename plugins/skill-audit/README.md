# skill-audit

Audits an Agent Skill against the current Claude Code and Agent Skills authoring guidance,
and proposes concrete fixes ranked by impact.

The rules are a curated core of four docs: the Agent Skills [overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview),
[best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices),
[enterprise guide](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise),
and Claude Code's [skills docs](https://code.claude.com/docs/en/skills). Each rule is tied to how
Claude Code actually loads a skill:

| Mechanic | What it means for the skill |
|---|---|
| Only `name` + `description` sit in the listing, cut at 1,536 chars | The description must say what + when, with the key use case first |
| SKILL.md is loaded once and never re-read; only the first ~5k tokens survive compaction | Keep it short, put the critical rules at the top, write them as standing instructions |
| References linked from other references may be previewed with `head -100` | One level deep, and a table of contents at the top of long files |
| Scripts run without being read | Use `${CLAUDE_SKILL_DIR}` paths, say run vs read, list dependencies |

## Usage

```
/skill-audit                              # every skill under the current directory
/skill-audit plugins/my-plugin            # a plugin, a skill directory, or a SKILL.md
/skill-audit ~/.claude/skills
```

The skill is manual-only (`disable-model-invocation: true`): Claude never starts it on its own,
so run it with `/skill-audit`.

## How it works

1. `scripts/audit_skill.py` checks the measurable rules: YAML that won't parse (e.g. an
   unquoted `: ` in the description, which silently disables auto-triggering), name and description
   limits, unknown keys, body line and token budgets, nested references, missing TOCs, broken or
   orphaned files, cwd-relative script paths, failing `!` command injection, undocumented
   dependencies, credentials, and network and adversarial patterns.
2. Claude reads every file and goes through the judgment rules in `references/rules.md`:
   conciseness, degrees of freedom, workflows and feedback loops, invocation control, front-loading.
3. The report lists at most 10 fixes, each with paste-ready replacement text.

The script works on its own too (Python 3.9+, stdlib only; exits 1 when there is a Must):

```bash
python3 plugins/skill-audit/skills/skill-audit/scripts/audit_skill.py <path>...
```

## Keeping the rules current

Claude Code and the Agent Skills docs change, so the rules are pinned to their sources and
checked for drift:

- **`skills/skill-audit/rules.json`** holds every limit and key list the audit script uses, each
  with the docs page and a verbatim quote it comes from, plus the evidence quotes for each rule
  and the Claude Code version the rules were last verified against.
- **`tools/check_docs_drift.py`** downloads the four source pages and reports quotes that
  disappeared, changes to the frontmatter keys, portable keys, and effort levels it extracts
  from the Claude Code docs, and section headings that were added or removed since
  `tools/doc-snapshot.json`. It makes no model calls.
- **`.github/workflows/skill-audit-docs-drift.yml`** runs the check every Monday and opens (or
  updates) an issue labelled `skill-audit-drift` when something changed.
- **The audit itself** prints the verified version next to the installed `claude --version`,
  and warns in the report when the installed version is newer.

When the drift issue opens:

1. Read the changed sections and update `references/rules.md`, `rules.json`, and
   `scripts/audit_skill.py` where the substance changed.
2. Run `python3 plugins/skill-audit/tools/check_docs_drift.py --update-snapshot`.
3. Set `verified` in `rules.json` to the current Claude Code version and date.
4. Run the check again: it should report no drift. Then close the issue.

## Installation

```bash
/plugin marketplace add kinchi22/claude-plugins
/plugin install skill-audit@kinchi22-claude-plugins
```
