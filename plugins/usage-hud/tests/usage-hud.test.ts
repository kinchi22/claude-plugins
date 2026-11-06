import { describe, expect, test } from 'claude-code/testing'

import { bar, cacheLabel, formatRemaining } from '../hooks/register'

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
  test('fills proportionally, rounding to the nearest cell', () => {
    const { filled, empty } = bar(23, 50)
    expect(filled).toBe('━'.repeat(12))
    expect(empty).toBe('━'.repeat(38))
  })

  test('clamps out-of-range percentages', () => {
    expect(bar(-5, 10)).toEqual({ filled: '', empty: '━'.repeat(10) })
    expect(bar(140, 10)).toEqual({ filled: '━'.repeat(10), empty: '' })
  })
})
