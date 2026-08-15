# Interactive components

The template ships the CSS for these. You only emit the markup.

**These components use no JavaScript, and you must not add any.** Embedded viewers — the
Claude mobile app among them — render the page in a sandbox without `allow-scripts`. A
JS-driven stepper looks perfect in your headless-browser check and is completely dead for
the person reading it on their phone. Radio inputs plus `:checked` sibling selectors work
in every sandbox, and the hidden-but-focusable radio group gives arrow-key navigation for
free. The one script in the template drives the theme toggle and nothing else; the toggle
hides itself when scripts are blocked so no dead button ships.

## When an interactive component earns its place

Use one only when a static paragraph genuinely loses information:

| Situation | Component |
|---|---|
| Procedural logic with ≥ 3 ordered steps, where each step changes state | **Stepper** |
| A rewritten algorithm, config, or data shape where the two versions are best read whole | **Before/after tabs** |
| A long supporting excerpt that only some readers need | **`<details class="snippet">`** (already the default for code) |

Anything else — a two-step flow, a single renamed function, a config bump — stays prose.
A report with four steppers is a worse report than one with none. **At most one or two
per document**, and only in the *major changes* section.

## Stepper

Walks the reader through procedural logic one state at a time.

```html
<div class="stepper">
  <input type="radio" name="st-lock" id="st-lock-1" checked>
  <input type="radio" name="st-lock" id="st-lock-2">
  <input type="radio" name="st-lock" id="st-lock-3">
  <div class="stepper-rail">
    <label for="st-lock-1">1. Acquire lock</label>
    <label for="st-lock-2">2. Compare version</label>
    <label for="st-lock-3">3. Commit or abort</label>
  </div>
  <div class="stepper-body">
    <div class="step">
      <h4>1. Acquire lock</h4>
      <p>The writer takes the row lock before reading the current version, which is the
         part that changed — previously the read happened outside the lock.</p>
    </div>
    <div class="step">
      <h4>2. Compare version</h4>
      <p>If the stored version differs from the one the caller sent, the write is a
         conflict and nothing is applied.</p>
      <details class="snippet">
        <summary>store.go:141</summary>
        <pre><code><span class="d-add">+ if row.Version != req.Version { return ErrConflict }</span></code></pre>
      </details>
    </div>
    <div class="step">
      <h4>3. Commit or abort</h4>
      <p>On a match the row is written and the version bumped in the same transaction, so
         two concurrent writers can no longer both succeed.</p>
    </div>
  </div>
  <div class="stepper-hint">단계를 눌러 이동 · 화살표 키로도 넘길 수 있습니다</div>
</div>
```

Structural rules the CSS depends on — break one and the component silently shows nothing:

- **All `<input>`s come first**, before the rail and the body. The selectors are sibling
  combinators; an input placed after a panel cannot reach it.
- **`name` is unique per stepper**, shared by that stepper's radios. Two steppers sharing
  a `name` become one radio group and fight each other.
- **`id`/`for` pairs are unique in the document.** `st-<topic>-<n>` is a good scheme.
- **`checked` on the first input.** Without it the stepper opens blank.
- **Rail label count == step count**, in the same order. Max 6 steps.
- The `.stepper-hint` line is optional but worth including — the rail is not obviously
  clickable on a touch screen.

Keep each step to 1–3 sentences. A step that needs a paragraph is a sign the split is
wrong — regroup.

## Before / after tabs

Two panels the reader flips between, for when a diff is better understood as two whole
versions than as interleaved `+`/`−` lines.

```html
<div class="ba">
  <input type="radio" name="ba-retry" id="ba-retry-1" checked>
  <input type="radio" name="ba-retry" id="ba-retry-2">
  <div class="ba-rail">
    <label for="ba-retry-1">Before</label>
    <label for="ba-retry-2">After</label>
  </div>
  <div class="ba-body">
    <div class="ba-panel">
      <p>Retries were unbounded and immediate, so a failing dependency got hammered.</p>
      <pre><code>for { if err := call(); err == nil { break } }</code></pre>
    </div>
    <div class="ba-panel">
      <p>Retries are capped at five with exponential backoff and jitter.</p>
      <pre><code>for i := 0; i &lt; maxRetries; i++ {
    if err := call(); err == nil { break }
    sleep(backoff(i))
}</code></pre>
    </div>
  </div>
</div>
```

Same rules as the stepper, plus: **panels live inside `.ba-body`** (the selectors count
`nth-child` within it), and there are at most 3.

## Code snippets

The default way to show code, and JS-free already — `<details>` is native HTML. Prose-first
means the snippet is *evidence*, not the explanation: the reader must already understand
the change from the paragraph above it.

```html
<details class="snippet">
  <summary>src/auth/session.ts:88–94</summary>
  <pre><code><span class="d-ctx">  const session = await load(id);</span><span class="d-del">- if (!session) return null;</span><span class="d-add">+ if (!session || session.expiresAt &lt; now()) return null;</span></code></pre>
</details>
```

- **≤ 12 lines.** Trim to the lines that carry the change plus one line of context.
- `<summary>` is `path:lineRange` — nothing else.
- Classes: `.d-add` (`+`), `.d-del` (`−`), `.d-ctx` (unchanged context).
- **Escape** `<`, `>`, `&` inside `<pre>`. This is the single most common way one of these
  reports comes out broken.
- No syntax highlighting. It costs markup and adds nothing at this length.

## Verifying it actually works

A headless-browser check with scripts enabled proves nothing about the environment that
broke first. Verify the way the reader will see it:

```js
// playwright
const ctx = await browser.newContext({ javaScriptEnabled: false });
```

Load the report in that context, click a rail label, and assert the visible step changed.
If it does, the component works in a sandboxed viewer too.
