# usage-hud

A two-line HUD above the Claude Code prompt that shows what a status line usually
shows — plus the one thing a status line can't keep current: **how long the prompt
cache stays warm**.

```
━━━━━━━━━━━━━━━━━━━━━━━━━  23% of 1000k tokens
💸 $1.50 | 5h 12% (2h3m) | wk 41% (3d4h) | cache 42m
```

The first line shows the context window; the second shows cost,
rate limits and the cache countdown.

| Segment | Source | Colors |
|---------|--------|--------|
| Context bar and `N% of Wk tokens` | live context window (`~` before the first response) | accent, yellow from 20%, red from 50% |
| `💸 $x.xx` | session cost, as `/cost` totals it | gray |
| `5h N% (resets in)` | five-hour rate-limit window (subscription sessions only) | accent, yellow from 20%, red from 50% |
| `wk N% (resets in)` | seven-day rate-limit window (subscription sessions only) | accent, yellow from 20%, red from 50% |
| `cache 42m` | time since the last main-thread model response, against the cache TTL | accent, yellow under 25% left, red under 10%; seconds in the last minute, `cache cold` once lapsed |

## Installation

```bash
/plugin install usage-hud --marketplace kinchi22/claude-plugins
```

On Claude Code older than 2.1.275, add the marketplace first:

```bash
/plugin marketplace add kinchi22/claude-plugins
/plugin install usage-hud@kinchi22-claude-plugins
```

## Why a mod and not a status line script

A `statusLine` command is re-run only when the session emits an event, so a countdown
in it freezes while you are away from the keyboard — exactly when you need to know
whether the cache is about to go cold. This plugin is a function-hooks mod: it reads the
same figures from `session.measure`, stamps each main-thread `turn.step`, and ticks a
clock every 10 seconds, so the band keeps counting down while the session sits idle.

Subagent requests are ignored: they cache a different prefix, so they don't keep the
main conversation's cache warm.

## Options

| Option | Values | Default |
|--------|--------|---------|
| Prompt cache TTL (`cacheTtl`) | `5m`, `1h` | `1h` |

The engine does not tell plugins which TTL a session's requests use, so set it to match
yours. Change it from `/config`; the module reloads with the new value.

## Using it beside an existing status line

If your `statusLine` script already prints the context bar or rate limits, drop those
parts from the script to avoid showing them twice — the band covers them.

## Development

```bash
claude plugin validate plugins/usage-hud
claude plugin test plugins/usage-hud
claude --plugin-dir plugins/usage-hud     # run a session with the working copy
```

The engine writes the API typings into `.claude-plugin/types/` when it loads the
plugin (git-ignored); after that, `tsc -p plugins/usage-hud` type-checks it.
