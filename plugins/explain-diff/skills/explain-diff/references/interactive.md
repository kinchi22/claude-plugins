# Interactive components

The template already ships the CSS and the vanilla JS for these. You only emit the
markup — no extra `<script>` block, no library.

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

Walks the reader through procedural logic one state at a time. Rail buttons jump; prev/next
walks. Step 1 is shown on load, and print mode expands every step.

```html
<div class="stepper">
  <div class="stepper-rail" role="tablist">
    <button type="button" role="tab">1. Acquire lock</button>
    <button type="button" role="tab">2. Compare version</button>
    <button type="button" role="tab">3. Commit or abort</button>
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
  <div class="stepper-nav">
    <button type="button" data-nav="prev">←</button>
    <span class="stepper-count"></span>
    <button type="button" data-nav="next">→</button>
  </div>
</div>
```

Requirements the JS depends on:

- `.stepper-rail button` count **must equal** `.step` count, in the same order.
- `data-nav="prev"` / `data-nav="next"` are optional; include both or neither.
- `.stepper-count` is filled in automatically — leave it empty.
- Do not add `is-active` yourself; the script sets it on load.

Keep each step to 1–3 sentences. A step that needs a paragraph is a sign the split is
wrong — regroup.

## Before / after tabs

Two panels the reader flips between, for when a diff is better understood as two whole
versions than as interleaved `+`/`−` lines.

```html
<div class="ba">
  <div class="ba-rail" role="tablist">
    <button type="button" role="tab" aria-selected="true">Before</button>
    <button type="button" role="tab" aria-selected="false">After</button>
  </div>
  <div class="ba-panel is-active">
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
```

Requirements: exactly as many `.ba-panel`s as rail buttons, in order; the first panel
carries `is-active` and its button `aria-selected="true"`.

## Code snippets

The default way to show code. Prose-first means the snippet is *evidence*, not the
explanation — the reader must already understand the change from the paragraph above it.

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
