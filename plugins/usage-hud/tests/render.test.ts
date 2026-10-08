import { expect, test } from 'claude-code/testing'

const PROPS = {
  hasSurvey: false,
  isWorking: false,
  maxRows: 10,
  bodyColumns: 140,
  scroll: { offset: 0, bodyRows: 10 },
  view: {},
}

for (const surface of ['terminal', 'desktop'] as const) {
  test(`draws usage figures on ${surface}`, async ($, on) => {
    on('session.measure', (_, e) => ({ changed: e.changed }))
    await $.session.measure({
      context: { tokens: 230_000, window: 1_000_000, percent: 23 },
      rateLimits: [
        { kind: 'five_hour', percentUsed: 12 },
        { kind: 'seven_day', percentUsed: 41 },
      ],
      cost: { usd: 1.5 },
      changed: ['context', 'rateLimits', 'cost'],
    })
    const ui = await $.ui.mount({ plugin: 'usage-hud', surface, component: 'AbovePrompt', props: PROPS })

    expect(await ui.find({ text: '☁ ' })).toBeDefined()
    expect(await ui.find({ text: '23% of 1000k tokens' })).toBeDefined()
    expect(await ui.find({ text: 'last turns' })).toBeUndefined()
    expect(await ui.find({ text: '5h 12%' })).toBeDefined()
    expect(await ui.find({ text: 'wk 41%' })).toBeDefined()
    expect(await ui.find({ text: '💸 $1.50' })).toBeDefined()
    expect(await ui.find({ text: 'cache –' })).toBeDefined()
  })
}
