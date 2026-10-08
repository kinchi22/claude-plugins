# usage-hud

A one-line HUD above the Claude Code prompt that shows what a status line usually
shows — plus the one thing a status line can't keep current: **how long the prompt
cache stays warm**.

```
☁  ███████████▄░░░░░░░░░░  23% of 1000k tokens  last turns ▁▂█  ▲ +98.3k last turn | 💸 $1.50 | 5h 12% (2h3m) | wk 41% (3d4h) | cache 42m
```

| Segment | Source | Colors |
|---------|--------|--------|
| Weather icon `☀` / `☁` / `☂` | context fill: under 20%, 20–49%, 50% and up | same color as the bar |
| Context bar and `N% of Wk tokens` | live context window (`~` before the first response) | accent, yellow from 20%, red from 50% |
| `last turns ▁▂█  ▲ +98.3k last turn` | context tokens after each of the last 12 main-loop turns, bars relative to the busiest; the delta of the last turn (`▼` when it shrank, `steady` when unchanged) | bars in the bar's color, labels gray |
| `💸 $x.xx` | session cost, as `/cost` totals it | gray |
| `5h N% (resets in)` | five-hour rate-limit window (subscription sessions only) | accent, yellow from 20%, red from 50% |
| `wk N% (resets in)` | seven-day rate-limit window (subscription sessions only) | accent, yellow from 20%, red from 50% |
| `cache 42m` | time since the last main-thread model response, against the cache TTL | accent, yellow under 25% left, red under 10%; seconds in the last minute, `cache cold` once lapsed |

## Why a mod and not a status line script

A `statusLine` command is re-run only when the session emits an event, so a countdown
in it freezes while you are away from the keyboard — exactly when you need to know
whether the cache is about to go cold. This plugin is a function-hooks mod: it reads the
same figures from `session.measure`, stamps each main-thread `turn.step`, and ticks a
clock every 10 seconds, so the band keeps counting down while the session sits idle.

Subagent requests are ignored: they cache a different prefix, so they don't keep the
main conversation's cache warm.

The turn history survives a mod reload and starts over on `/clear`.

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

## Credits

The weather icons, the block-character turn chart and the `last turn` trend are adapted
from the [token-weather](https://github.com/anthropics/claude-code-playground/tree/main/claude-code/mods/token-weather)
mod in anthropics/claude-code-playground (Copyright 2026 Anthropic PBC, Apache-2.0).
