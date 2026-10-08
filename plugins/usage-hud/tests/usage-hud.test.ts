import { describe, expect, test } from 'claude-code/testing'

import { bar, cacheLabel, chart, formatRemaining, trend, weatherIcon } from '../hooks/register'

const HOUR = 60 * 60_000
const FIVE_MIN = 5 * 60_000

describe('cacheLabel', () => {
  test('shows a dash before any response', () => {
    expect(cacheLabel(null, 1_000, HOUR).text).toBe('cache –')
  })

  test('counts down minutes left on a 1h TTL', () => {
    const lastAt = 0
    expect(cacheLabel(lastAt, 18 * 60_000, HOUR).text).toBe('cache 42m')
  })

  test('switches to seconds in the last minute', () => {
    expect(cacheLabel(0, FIVE_MIN - 30_000, FIVE_MIN).text).toBe('cache 30s')
  })

  test('goes cold once the TTL has passed', () => {
    expect(cacheLabel(0, HOUR + 1, HOUR).text).toBe('cache cold')
  })

  test('warns as the window runs out', () => {
    const fresh = cacheLabel(0, 0, HOUR).color
    const late = cacheLabel(0, HOUR - 10 * 60_000, HOUR).color
    const last = cacheLabel(0, HOUR - 3 * 60_000, HOUR).color
    expect(new Set([fresh, late, last]).size).toBe(3)
  })
})

describe('formatRemaining', () => {
  test('formats like statusline.sh', () => {
    expect(formatRemaining(0)).toBe('now')
    expect(formatRemaining(90 * 60_000)).toBe('1h30m')
    expect(formatRemaining(2 * HOUR)).toBe('2h')
    expect(formatRemaining(3 * 24 * HOUR + 4 * HOUR)).toBe('3d4h')
  })
})

describe('bar', () => {
  test('fills proportionally with a half block', () => {
    const { filled, empty } = bar(23, 50)
    expect(filled).toBe('███████████▄')
    expect(filled.length + empty.length).toBe(50)
  })
})

describe('weatherIcon', () => {
  test('follows the bar color thresholds', () => {
    expect(weatherIcon(0)).toBe('☀')
    expect(weatherIcon(19)).toBe('☀')
    expect(weatherIcon(20)).toBe('☁')
    expect(weatherIcon(49)).toBe('☁')
    expect(weatherIcon(50)).toBe('☂')
    expect(weatherIcon(100)).toBe('☂')
  })
})

describe('turn history', () => {
  test('charts turns relative to the busiest one', () => {
    expect(chart([10_000, 30_000, 130_000])).toBe('▁▂█')
  })

  test('reports the last turn delta', () => {
    expect(trend([36_000])).toBe('')
    expect(trend([36_000, 134_300])).toBe('▲ +98.3k last turn')
    expect(trend([134_300, 36_000])).toBe('▼ 98.3k last turn')
    expect(trend([5, 5])).toBe('steady')
  })
})
