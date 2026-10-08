export type RateWindow = { kind: string; percentUsed: number; resetsAt?: string }

export type Usage = {
  context: { tokens?: number; window: number; percent?: number }
  rateLimits: RateWindow[]
  cost?: { usd: number }
}

declare module 'claude-code' {
  interface PluginState {
    'usage-hud': {
      usage: Usage | null
      lastResponseAt: number | null
      now: number
      turns: number[]
    }
  }
}
