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

// Icons, block bars and the trend line after token-weather
// (anthropics/claude-code-playground, Apache-2.0). Single-width symbols, not emoji.
const HISTORY = 12
const BARS = '▁▂▃▄▅▆▇█'

const usage = atom({ plugin: 'usage-hud', key: 'usage' } as const, null)
const lastResponseAt = atom({ plugin: 'usage-hud', key: 'lastResponseAt' } as const, null)
const now = atom({ plugin: 'usage-hud', key: 'now' } as const, 0)
const turns = atom({ plugin: 'usage-hud', key: 'turns' } as const, [])

const levelColor = (pct: number) => (pct >= 50 ? RED : pct >= 20 ? YELLOW : ACCENT)

// Same thresholds as levelColor, so the icon always matches the bar's color.
export const weatherIcon = (pct: number) => (pct >= 50 ? '☂' : pct >= 20 ? '☁' : '☀')

export const short = (n: number) => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(n % 1_000_000 === 0 ? 0 : 1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(n % 1_000 === 0 ? 0 : 1)}k`
  return String(n)
}

// Bars scale to the busiest turn shown, so growth shows at any fill level.
export const chart = (tokens: readonly number[]) => {
  const top = Math.max(...tokens, 1)
  return tokens
    .map(t => BARS[Math.min(BARS.length - 1, Math.floor((t / top) * (BARS.length - 1)))])
    .join('')
}

export const trend = (tokens: readonly number[]) => {
  const last = tokens[tokens.length - 1]
  const prev = tokens[tokens.length - 2]
  if (last === undefined || prev === undefined) return ''
  const delta = last - prev
  if (delta > 0) return `▲ +${short(delta)} last turn`
  if (delta < 0) return `▼ ${short(-delta)} last turn`
  return 'steady'
}

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

// Half-block bar: each cell is 2 points, ▄ marks an odd point.
export const bar = (pct: number, width: number) => {
  let filled = ''
  let empty = ''
  for (let i = 0; i < width; i++) {
    const progress = pct - (i * 100) / width
    const step = 100 / width
    if (progress >= step) filled += '█'
    else if (progress >= step / 2) filled += '▄'
    else empty += '░'
  }
  return { filled, empty }
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

  // One reading per main-loop turn; a reload keeps them ($.state), a /clear starts over.
  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (e.agentId !== undefined) return result
    const tokens = (await $.session.usage()).context.tokens ?? 0
    if (tokens > 0) await update($, turns, list => [...list, tokens].slice(-HISTORY))
    return result
  })

  on('session.end', async ($, e, next) => {
    if (e.reason === 'clear') await update($, turns, () => [])
    return next(e)
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
    const history = await read($, turns)
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

    const icon = `${weatherIcon(pct)}  `
    const label = ` ${hasFill ? '' : '~'}${pct}% of ${Math.round(window / 1000)}k tokens`
    const bars = chart(history)
    const delta = trend(history)
    const turnsText = bars ? `  last turns ${bars}${delta ? `  ${delta}` : ''}` : ''
    const fixed = icon.length + label.length + turnsText.length + 1
    const width = Math.max(10, Math.min(50, e.props.bodyColumns - fixed))
    const { filled, empty } = bar(pct, width)

    // Line 1: context and turn history; line 2, indented under the bar: cost, limits, cache.
    return (
      <Box flexDirection="column">
        <Text wrap="truncate-end">
          <Text color={ctxColor}>{icon}</Text>
          <Text color={ctxColor}>{filled}</Text>
          <Text color={EMPTY}>{empty}</Text>
          <Text color={ctxColor}>{label}</Text>
          {bars ? (
            <Text>
              <Text color={GRAY}>{'  last turns '}</Text>
              <Text color={ctxColor}>{bars}</Text>
              {delta ? <Text color={GRAY}>{`  ${delta}`}</Text> : null}
            </Text>
          ) : null}
        </Text>
        <Text wrap="truncate-end">
          {' '.repeat(icon.length)}
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
