# Inline SVG diagram recipes

Every diagram in an explain-diff report is **hand-authored inline SVG**. No Mermaid, no
CDN, no build step — the report must render from a `file://` URL with the network off and
survive an Artifact CSP unchanged.

## Rules

1. **Never hardcode a colour.** Use the classes the template already defines:
   `.node`, `.node-accent`, `.node-add`, `.node-del`, `.edge`, `.edge-accent`,
   `.edge-dashed`, `.label`, `.label-sm`, `.arrowhead`, `.arrowhead-accent`.
   They are wired to CSS tokens, so the diagram flips with the theme for free.
2. **`viewBox` yes, `width`/`height` no.** The template sets `width:100%; height:auto`.
   Pick a viewBox whose aspect ratio is close to what you want on screen —
   roughly 2:1 for flows, 3:2 for state machines. **Trim the viewBox to the drawn content
   plus ~16px of padding**: the SVG is scaled up to the full column width, so empty space
   inside the viewBox is multiplied into a visible gap on the page.
3. **Accessible.** `role="img"` plus a `<title>` as the first child. Wrap in
   `<figure class="diagram">` with a `<figcaption>`.
4. **Text is `<text>`, not `<foreignObject>`.** Keep labels ≤ 4 words. If a box needs a
   sentence, the sentence belongs in the prose, not the picture.
   Centre with `text-anchor="middle"` and `dominant-baseline="middle"`.
5. **A diagram must show a mechanism.** Boxes that restate the section heading are noise.
   Draw it only when it answers *how does the data move* / *what changed in the shape* /
   *what are the states*. Two or three diagrams in a report is plenty; zero is fine for a
   small diff.
6. **Show the delta.** In a change diagram, mark what the PR added with `.node-add`, what
   it removed with `.node-del` (usually plus `opacity="0.55"`), and leave untouched parts
   in plain `.node`. The reader should see the change without reading a legend.

## Shared defs

Put arrowheads once, at the top of each `<svg>`:

```html
<defs>
  <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" class="arrowhead"/>
  </marker>
  <marker id="ahA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M0,0 L10,5 L0,10 z" class="arrowhead-accent"/>
  </marker>
</defs>
```

If a page has several diagrams, suffix the marker ids per diagram (`ah-auth`, `ahA-auth`)
so duplicate ids never collide.

## Recipe 1 — pipeline / data flow

For "the request now goes through one more step".

```html
<figure class="diagram">
<svg viewBox="0 0 720 116" role="img" xmlns="http://www.w3.org/2000/svg">
  <title>Request path after the change</title>
  <defs>
    <marker id="ah-p" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="arrowhead"/>
    </marker>
  </defs>

  <rect class="node" x="16"  y="16" width="140" height="56" rx="8"/>
  <text class="label" x="86"  y="44" text-anchor="middle" dominant-baseline="middle">Handler</text>

  <rect class="node-add" x="216" y="16" width="160" height="56" rx="8"/>
  <text class="label" x="296" y="38" text-anchor="middle" dominant-baseline="middle">RateLimiter</text>
  <text class="label-sm" x="296" y="56" text-anchor="middle" dominant-baseline="middle">new</text>

  <rect class="node" x="436" y="16" width="140" height="56" rx="8"/>
  <text class="label" x="506" y="44" text-anchor="middle" dominant-baseline="middle">Service</text>

  <line class="edge" x1="156" y1="44" x2="208" y2="44" marker-end="url(#ah-p)"/>
  <line class="edge" x1="376" y1="44" x2="428" y2="44" marker-end="url(#ah-p)"/>

  <text class="label-sm" x="296" y="98" text-anchor="middle">429 when the bucket is empty</text>
</svg>
<figcaption>Every call now passes the limiter before reaching the service.</figcaption>
</figure>
```

## Recipe 2 — before / after, side by side

For "the shape changed". Two columns, a divider, `.node-del` at 55% opacity on the left.

```html
<figure class="diagram">
<svg viewBox="0 0 720 210" role="img" xmlns="http://www.w3.org/2000/svg">
  <title>Cache lookup before and after</title>
  <text class="label-sm" x="170" y="20" text-anchor="middle">before</text>
  <text class="label-sm" x="550" y="20" text-anchor="middle">after</text>
  <line class="edge-dashed" x1="360" y1="8" x2="360" y2="200"/>

  <rect class="node-del" x="90" y="44" width="160" height="48" rx="8" opacity="0.55"/>
  <text class="label" x="170" y="68" text-anchor="middle" dominant-baseline="middle">read → DB</text>

  <rect class="node-add" x="470" y="44" width="160" height="48" rx="8"/>
  <text class="label" x="550" y="68" text-anchor="middle" dominant-baseline="middle">read → cache</text>
  <rect class="node" x="470" y="118" width="160" height="48" rx="8"/>
  <text class="label" x="550" y="142" text-anchor="middle" dominant-baseline="middle">miss → DB</text>
</svg>
<figcaption>Reads hit the cache first; the DB is now only the miss path.</figcaption>
</figure>
```

## Recipe 3 — state machine

For "a new state / a new transition". Circles, curved edges, transition labels on the arc.

```html
<figure class="diagram">
<svg viewBox="0 0 720 220" role="img" xmlns="http://www.w3.org/2000/svg">
  <title>Job states</title>
  <defs>
    <marker id="ah-s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="arrowhead"/>
    </marker>
    <marker id="ahA-s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="arrowhead-accent"/>
    </marker>
  </defs>

  <circle class="node" cx="110" cy="120" r="44"/>
  <text class="label" x="110" y="120" text-anchor="middle" dominant-baseline="middle">queued</text>

  <circle class="node" cx="330" cy="120" r="44"/>
  <text class="label" x="330" y="120" text-anchor="middle" dominant-baseline="middle">running</text>

  <circle class="node-add" cx="560" cy="120" r="44"/>
  <text class="label" x="560" y="114" text-anchor="middle" dominant-baseline="middle">retrying</text>
  <text class="label-sm" x="560" y="132" text-anchor="middle" dominant-baseline="middle">new</text>

  <line class="edge" x1="154" y1="120" x2="278" y2="120" marker-end="url(#ah-s)"/>
  <text class="label-sm" x="216" y="106" text-anchor="middle">pick up</text>

  <line class="edge-accent" x1="374" y1="120" x2="508" y2="120" marker-end="url(#ahA-s)"/>
  <text class="label-sm" x="441" y="106" text-anchor="middle">transient error</text>

  <path class="edge-accent" d="M545,80 C500,20 380,20 340,74" marker-end="url(#ahA-s)"/>
  <text class="label-sm" x="443" y="30" text-anchor="middle">backoff elapsed</text>
</svg>
<figcaption>Transient failures no longer terminate the job; they loop through <tspan>retrying</tspan>.</figcaption>
</figure>
```

## Recipe 4 — sequence

For "who calls whom, in what order". Lifelines down, messages across, ordered top to bottom.

```html
<figure class="diagram">
<svg viewBox="0 0 720 260" role="img" xmlns="http://www.w3.org/2000/svg">
  <title>Token refresh sequence</title>
  <defs>
    <marker id="ah-q" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="arrowhead"/>
    </marker>
  </defs>

  <rect class="node" x="40"  y="16" width="120" height="36" rx="6"/>
  <text class="label" x="100" y="34" text-anchor="middle" dominant-baseline="middle">Client</text>
  <rect class="node" x="300" y="16" width="120" height="36" rx="6"/>
  <text class="label" x="360" y="34" text-anchor="middle" dominant-baseline="middle">API</text>
  <rect class="node-add" x="560" y="16" width="120" height="36" rx="6"/>
  <text class="label" x="620" y="34" text-anchor="middle" dominant-baseline="middle">TokenStore</text>

  <line class="edge-dashed" x1="100" y1="52" x2="100" y2="240"/>
  <line class="edge-dashed" x1="360" y1="52" x2="360" y2="240"/>
  <line class="edge-dashed" x1="620" y1="52" x2="620" y2="240"/>

  <line class="edge" x1="100" y1="92"  x2="352" y2="92"  marker-end="url(#ah-q)"/>
  <text class="label-sm" x="226" y="82" text-anchor="middle">GET /data</text>

  <line class="edge-accent" x1="360" y1="140" x2="612" y2="140" marker-end="url(#ah-q)"/>
  <text class="label-sm" x="486" y="130" text-anchor="middle">refresh if expiring</text>

  <line class="edge" x1="360" y1="196" x2="108" y2="196" marker-end="url(#ah-q)"/>
  <text class="label-sm" x="234" y="186" text-anchor="middle">200 + fresh token</text>
</svg>
<figcaption>The API refreshes the token itself; the client no longer sees a 401 round trip.</figcaption>
</figure>
```

## Layout arithmetic

Boxes drift out of alignment fast when the coordinates are eyeballed. Fix a grid before
you write anything:

- viewBox `0 0 720 H`, left margin 16, right margin 16 → usable width 688.
- N columns: `w = (688 - (N-1)*gap) / N`, gap 52. For N=3 → w ≈ 195.
- A box's text baseline is `y + height/2` with `dominant-baseline="middle"`.
- An arrow between two boxes on the same row: `x1 = leftBox.x + leftBox.w + 8`,
  `x2 = rightBox.x - 8`, both at the shared centre `y`.

Compute the numbers once, reuse them across the diagram, and the result is aligned
without a single trial render.
