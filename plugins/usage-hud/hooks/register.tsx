import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { RateWindow, Usage } from '../types'

// Same palette as ~/.claude/statusline.sh (xterm-256 74 / 220 / 203 / 238 / 245).
const ACCENT = '#5fafd7'
const YELLOW = '#ffd700'
const RED = '#ff5f5f'
const EMPTY = '#444444'
const GRAY = '#8a8a8a'

const TTL_MS = { '5m': 5 * 60_000, '1h': 60 * 60_000 } as const
const TICK_MS = 10_000

const usage = atom({ plugin: 'usage-hud', key: 'usage' } as const, null)
const lastResponseAt = atom({ plugin: 'usage-hud', key: 'lastResponseAt' } as const, null)
const now = atom({ plugin: 'usage-hud', key: 'now' } as const, 0)

const levelColor = (pct: number) => (pct >= 50 ? RED : pct >= 20 ? YELLOW : ACCENT)

export const formatRemaining = (ms: number) => {
  const s = Math.floor(ms / 1000)
  if (s <= 0) return 'now'
  if (s < 3600) return `${Math.max(1, Math.floor(s / 60))}m`
  if (s < 86400) {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    return m === 0 ? `${h}h` : `${h}h${m}m`
  }
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  return h === 0 ? `${d}d` : `${d}d${h}h`
}

// One glyph for both parts, told apart only by color: block characters left gaps
// and mismatched heights in the desktop app's font.
export const bar = (pct: number, width: number) => {
  const cells = Math.max(0, Math.min(width, Math.round((pct / 100) * width)))
  return { filled: '━'.repeat(cells), empty: '━'.repeat(width - cells) }
}

export const cacheLabel = (lastAt: number | null, at: number, ttlMs: number) => {
  if (lastAt === null) return { text: 'cache –', color: GRAY }
  const left = lastAt + ttlMs - at
  if (left <= 0) return { text: 'cache cold', color: RED }
  const s = Math.floor(left / 1000)
  const text = s < 60 ? `cache ${s}s` : `cache ${formatRemaining(left)}`
  const color = left < ttlMs * 0.1 ? RED : left < ttlMs * 0.25 ? YELLOW : ACCENT
  return { text, color }
}

const windowLabel = (label: string, w: RateWindow | undefined, at: number) => {
  if (!w) return null
  const pct = Math.round(w.percentUsed)
  const resets = w.resetsAt ? ` (${formatRemaining(Date.parse(w.resetsAt) - at)})` : ''
  return { text: `${label} ${pct}%${resets}`, color: levelColor(pct) }
}

export const register: Register = (on, options) => {
  const ttlMs = TTL_MS[options.cacheTtl === '5m' ? '5m' : '1h']

  const toUsage = ({ context, rateLimits, cost }: Usage): Usage => ({
    context: { tokens: context.tokens, window: context.window, percent: context.percent },
    rateLimits,
    cost,
  })

  on('session.start', async ($, e, next) => {
    const result = await next(e)
    const current = toUsage(await $.session.usage())
    const at = await $.clock.now()
    await update($, usage, () => current)
    await update($, now, () => at)
    $.clock.every(TICK_MS, async () => {
      const tick = await $.clock.now()
      await update($, now, () => tick)
    })
    return result
  })

  on('session.measure', async ($, e, next) => {
    const current = toUsage(e)
    await update($, usage, () => current)
    return next(e)
  })

  // Every main-thread model response re-reads (and so refreshes) the prompt cache.
  on('turn.step', async function* ($, e, next) {
    const result = yield* next(e)
    if (e.agentId === undefined) {
      const at = await $.clock.now()
      await update($, lastResponseAt, () => at)
      await update($, now, () => at)
    }
    return result
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const u = await read($, usage)
    if (e.props.hasSurvey || u === null) return next(e)

    const at = await read($, now)
    const lastAt = await read($, lastResponseAt)
    const { Box, Text } = $.ui.resolve(e)

    const window = u.context.window
    const hasFill = u.context.percent !== undefined
    const pct = Math.min(100, Math.round(u.context.percent ?? (20_000 * 100) / window))
    const ctxColor = levelColor(pct)

    const sep = <Text color={GRAY}> | </Text>
    const parts: { text: string; color: string }[] = []
    if (u.cost && u.cost.usd > 0) {
      const usd = u.cost.usd < 1 ? u.cost.usd.toFixed(3) : u.cost.usd.toFixed(2)
      parts.push({ text: `💸 $${usd}`, color: GRAY })
    }
    const five = windowLabel('5h', u.rateLimits.find(w => w.kind === 'five_hour'), at)
    const week = windowLabel('wk', u.rateLimits.find(w => w.kind === 'seven_day'), at)
    if (five) parts.push(five)
    if (week) parts.push(week)
    parts.push(cacheLabel(lastAt, at, ttlMs))

    const label = ` ${hasFill ? '' : '~'}${pct}% of ${Math.round(window / 1000)}k tokens`
    const fixed = label.length + 1
    const width = Math.max(5, Math.min(25, Math.floor((e.props.bodyColumns - fixed) / 2)))
    const { filled, empty } = bar(pct, width)

    // Line 1: context; line 2: cost, limits, cache.
    return (
      <Box flexDirection="column">
        <Text wrap="truncate-end">
          <Text color={ctxColor}>{filled}</Text>
          <Text color={EMPTY}>{empty}</Text>
          <Text color={ctxColor}>{label}</Text>
        </Text>
        <Text wrap="truncate-end">
          {parts.map((p, i) => (
            <Text key={p.text}>
              {i > 0 ? sep : null}
              <Text color={p.color}>{p.text}</Text>
            </Text>
          ))}
        </Text>
      </Box>
    )
  })
}
