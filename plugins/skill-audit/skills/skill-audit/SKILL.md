---
name: skill-audit
description: >-
  Audits an Agent Skill (SKILL.md plus its bundled references and scripts) against current
  Claude Code and Agent Skills authoring best practices, and proposes concrete, ranked fixes.
  Use when the user asks to review, audit, lint, or grade a skill, asks whether a SKILL.md
  follows best practices, or asks why a skill doesn't trigger, triggers too often, or stops
  being followed.
argument-hint: "[skill-dir | SKILL.md | plugin-dir]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/audit_skill.py *)
---

# Skill Audit

Judge a skill by how Claude Code actually loads it:

- **Listing**: only `name` + `description` are visible before invocation. The text is cut at 1,536 chars and can be dropped entirely when the listing is over budget.
- **Invocation**: the SKILL.md body enters context once and is **never re-read**. After compaction only its first ~5,000 tokens come back.
- **References**: read on demand. A file linked only from another reference may be previewed with `head -100`, not read in full.
- **Scripts**: run, not read. Only their output costs context.

Every finding must name the mechanic it breaks. That is what makes a finding actionable rather than a style opinion.

**Report only. Do not edit the audited skill** unless the user asks after reading the report.

## Rules

`references/rules.md` defines every rule below: severity, rationale, and fix shape. **Read it in
full before the judgment pass.** Auto rules are checked by the script, judge rules need you.
[rules.json](rules.json) holds the numeric limits and key lists the script uses, each pinned to a quote
from the docs, plus the Claude Code version the rules were last verified against. Read it only to
check where a limit comes from.

| Group | Rules |
|---|---|
| D: Discovery | D1 frontmatter valid · D2 description = what + when, third person · D3 key use case first, ≤1,536 chars · D4 invocation control (`disable-model-invocation` for side effects, scoped `allowed-tools`) |
| C: Context | C1 body < 500 lines / ~5k tokens · C2 only what Claude doesn't know · C3 critical rules near the top, written as standing instructions |
| P: Disclosure | P1 references one level deep · P2 TOC at the top of references > 100 lines · P3 every file linked, each link says *when* · P4 forward slashes, descriptive names |
| I: Instructions | I1 freedom matches fragility, one default + escape hatch · I2 checklists and validate→fix loops · I3 no time-sensitive info, one term per concept · I4 concrete examples |
| S: Scripts | S1 run vs read explicit, `${CLAUDE_SKILL_DIR}` paths · S2 handle errors, no magic numbers · S3 dependencies listed · S4 dynamic `!` command injection can't fail · S5 `mcp__server__tool` names |
| X: Security | X1 no credentials · X2 network and URLs justified · X3 no adversarial instructions · X4 tool and filesystem scope |
| T: Testing | T1 evals, including should-NOT-trigger cases |

Severity: **Must** means it breaks loading, triggering, or upload, or is a security risk. **Should** means it measurably
hurts triggering, context cost, or instruction following. **Consider** means polish.

## Workflow

Copy this checklist and keep it updated:

```
- [ ] 1. Resolve targets
- [ ] 2. Run the mechanical audit
- [ ] 3. Read every file in the skill
- [ ] 4. Judgment pass against references/rules.md
- [ ] 5. Write the report
```

**1. Resolve targets.** The argument (`$ARGUMENTS`; it may be empty) is a skill directory, a SKILL.md, or a
directory that contains skills (a plugin, a repo, `~/.claude/skills`). With no argument, use the current directory. If more than five
skills match, ask which ones to audit, or audit all of them and lead with a summary table.

**2. Run the mechanical audit:**

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/audit_skill.py <target>...
```

The first line says which Claude Code version the rules were verified against and compares it with the
installed one. Copy it into the report. If it says the installed version is newer, keep that warning
in the report. Then, for each skill, it prints a stats line (body lines and tokens, listing chars, linked and nested files) and findings as
`SEVERITY RULE file:line message`. Exit code 1 means at least one Must. The output is a list of **candidates**:
it pattern-matches, so confirm each one against the file before reporting it, and drop false positives.

**3. Read every file in full**: SKILL.md, all references, all scripts. Do not preview with `head`.
The audit exists to catch what a partial read misses.

**4. Judgment pass.** Read `references/rules.md` and go through every judge rule. For C2 and I1, quote
the passage you are judging. Look for the problems the script can't see: a description that matches
the wrong requests, a must-hold rule buried in the middle of the file, a step that should be a script, a
workflow with no validation loop.

**5. Write the report** in the user's language, using this structure:

```markdown
# Skill audit: <name>

<one-sentence verdict>. N must · N should · N consider

> <version line from the script, e.g. "Rules verified against Claude Code 2.1.316 (2026-11-02); installed 2.1.316">

| Group | Status |
|---|---|
| Discovery | ✅ / ⚠️ / ❌ (rule IDs) |
| … | … |

## Fixes, highest impact first

### 1. [Must] P3: `references/forms.md` is linked but missing (SKILL.md:42)
**Breaks:** <the loading mechanic, one line>
**Fix:**
<exact replacement text: rewritten description, moved section, TOC block, frontmatter diff>

## Not checked
<anything you couldn't verify, e.g. T1 triggering without running evals>
```

Report rules:
- Every fix is concrete: give the text to paste, never "consider improving X". For D2, give the
  full rewritten description. For P2, give the TOC block.
- Rank by impact and list at most 10 fixes. Fold repeats of the same rule into one fix.
- Don't invent rules beyond `references/rules.md`. Taste is not a finding.
- "No changes needed" is a valid verdict. Don't manufacture findings to look thorough.
- Once the report is delivered, offer to apply the fixes. If the user accepts, rerun the script afterwards to confirm the findings are gone.
