# Editorial Cream Design System

A design language for developer/product sites — warm, editorial, premium, calm.
Inspired by Bella Health, Linear's restraint, and old-school print typography.

The mood is **"premium magazine spread, not SaaS landing page"**: cream paper,
massive display type, italic serif accents, floating UI pills, dark terminal cards.

---

## 1 · Principles

1. **Big type does the work.** One enormous headline beats five small headers.
2. **Italic serif on coral is the only emphasis.** No underlines, no bold, no color highlighting — italics in `Instrument Serif` colored coral are the entire emphasis system.
3. **Cream background, dark accents.** Light theme with deep contrast, never gray-on-gray.
4. **Float, don't frame.** Hero pills overlap the terminal. Wordmark almost touches the stage. Avoid cards inside cards.
5. **Numbered editorial layouts.** "— 01", "— 02" lockups feel printed, not dashboard.
6. **One coral, one ink.** Two colors carry the entire brand. Greens/ambers/roses appear only for status (success, warning, error).

---

## 2 · Color Palette

### Surface (cream family)
```css
--cream:   #ede8da;  /* primary background */
--cream-2: #e3ddcb;  /* darker accent surface */
--paper:   #f4efe2;  /* lighter card surface */
--white:   #ffffff;  /* pop surface — pills, hover states */
```

### Ink (text family)
```css
--ink:    #0e0e0b;  /* headlines, body */
--ink-2:  #2a2520;  /* secondary text */
--ink-3:  #6b6555;  /* labels, captions */
--ink-4:  #9a9385;  /* muted */
```

### Brand accent (coral — single use)
```css
--coral:      #c85a3a;
--coral-soft: #f0d4c8;
```
Rule: if you use coral more than ~5 times above the fold, you're using it wrong.

### Semantic (status only — never decorative)
```css
--green:  #3d8a52;  --green-soft: #d8e4d6;
--amber:  #c89030;  --amber-soft: #efe0c2;
--rose:   #c44550;  --rose-soft:  #efd0d3;
```

### Lines (alpha — keeps lines warm)
```css
--line:   rgba(14,14,11,0.10);
--line-2: rgba(14,14,11,0.18);
```

---

## 3 · Typography

Three families, distinct jobs. Never mix within a single text run.

```css
--font-display: 'Inter Tight',     sans-serif; /* headlines, wordmarks */
--font-sans:    'Inter',           sans-serif; /* body, UI */
--font-mono:    'JetBrains Mono',  monospace;  /* code, env vars */
--font-serif:   'Instrument Serif', serif;     /* italic emphasis ONLY */
```

### The signature emphasis pattern
Inside any heading, wrap one or two emphasis words in `<em>`:

```css
h1 em, h2 em, h3 em {
  font-style: italic;
  font-weight: 500;
  color: var(--coral);
  font-family: var(--font-serif);
}
```

```html
<h1>Route every prompt to the<br/><em>safest</em> possible answer.</h1>
<h2>Built for<br/><em>responsible</em> AI.</h2>
```

One or two emphasis words per headline. More breaks the rhythm.

### Type scale
```css
/* Hero */
font-family: var(--font-display);
font-weight: 800;
font-size: clamp(2.6rem, 7vw, 5.5rem);
line-height: 0.95;
letter-spacing: -0.045em;

/* h2 */
font-size: clamp(2rem, 5vw, 3.5rem);
font-weight: 800;
letter-spacing: -0.04em;

/* Mega wordmark — one per page */
font-weight: 900;
font-size: clamp(4rem, 17vw, 13rem);
letter-spacing: -0.06em;
line-height: 0.85;

/* Section eyebrow label */
font-size: 0.72rem;
font-weight: 600;
letter-spacing: 0.14em;
text-transform: uppercase;
color: var(--ink-3);
```

### The eyebrow lockup (signature)
```css
.section-label {
  font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--ink-3);
  display: flex; align-items: center; gap: 0.6rem;
}
.section-label::before {
  content: ""; width: 24px; height: 1px;
  background: var(--ink-3);
}
```

### Editorial item numbering
```css
.step-num {
  font-family: var(--font-display);
  font-size: 0.78rem; font-weight: 700;
  color: var(--coral);
  letter-spacing: 0.05em;
}
```
```html
<div class="step-num">— 01</div>
```

---

## 4 · Layout

- `max-width: 1200px` for sections
- `max-width: 920px` for hero terminal stage
- `max-width: 880px` for h2 (lets headlines breathe)
- `max-width: 560px` for section intro paragraphs
- Section padding: `6rem 1.5rem`. First section after a related one: drop top to `3rem`.

### Step grid (editorial vertical dividers, no card backgrounds)
```css
.steps-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  border-top: 1px solid var(--line);
}
.step {
  padding: 2.25rem 1.5rem 2rem 0;
  border-right: 1px solid var(--line);
}
.step:last-child  { border-right: none; }
.step:not(:first-child) { padding-left: 1.5rem; }
```

### Feature grid (1px-border trick)
```css
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--line);              /* this becomes the divider */
  border: 1px solid var(--line);
  border-radius: 18px;
  overflow: hidden;
}
.feature {
  padding: 2.25rem 2rem;
  background: var(--paper);
  transition: background 0.2s;
}
.feature:hover { background: var(--white); }
```

---

## 5 · Components

### Floating pill (signature)
White pill with soft shadow. Inline (eyebrow) or absolute around a stage.

```css
.float-pill {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.55rem 1rem;
  background: var(--white);
  border-radius: 99px;
  box-shadow: 0 8px 20px -8px rgba(14,14,11,0.18);
  font-size: 0.84rem; font-weight: 500;
  white-space: nowrap;
}
.pill-icon {
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem;
}
.pill-icon.green { background: var(--green-soft); color: var(--green-2); }
.pill-icon.coral { background: var(--coral-soft); color: var(--coral); }
.pill-icon.amber { background: var(--amber-soft); color: var(--amber); }
```

### Live dot (signature pulse)
**Always** use `transform` + `opacity`. Animating `box-shadow` paints every frame and tanks scroll perf.

```css
.dot-live {
  position: relative;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--green);
}
.dot-live::after {
  content: ""; position: absolute; inset: -3px;
  border-radius: 50%;
  background: var(--green);
  opacity: 0.4;
  animation: livepulse 2.4s ease-out infinite;
  will-change: transform, opacity;
}
@keyframes livepulse {
  0%   { transform: scale(1);   opacity: 0.4; }
  100% { transform: scale(2.6); opacity: 0;   }
}
```

### Buttons
```css
.btn-primary { background: var(--ink); color: var(--cream); border-radius: 99px; }
.btn-primary:hover { background: var(--coral); transform: translateY(-1px); }

.btn-ghost { border: 1px solid var(--line-2); border-radius: 99px; background: transparent; }
.btn-ghost:hover { border-color: var(--ink); background: rgba(255,255,255,0.5); }

.btn-cream { background: var(--cream); color: var(--ink); }  /* for use ON dark sections */
```

No coral-filled or coral-outlined buttons. Coral stays for typography.

### Inline code
```css
code {
  font-family: var(--font-mono);
  font-size: 0.86em;
  background: rgba(14,14,11,0.06);
  padding: 0.12em 0.4em;
  border-radius: 4px;
  color: var(--ink-2);
}
```

### Terminal / code block (the dark card)
```css
.terminal {
  background: #15140f;
  border-radius: 18px;
  box-shadow: 0 18px 40px -18px rgba(14,14,11,0.30); /* single shadow, lighter */
  contain: paint;
}
.terminal-bar { background: #1c1a14; padding: 0.7rem 1rem; }
.term-dot:nth-child(1) { background: #ff5f57; }
.term-dot:nth-child(2) { background: #febc2e; }
.term-dot:nth-child(3) { background: #28c840; }

/* Token colors — warm, never neon */
.term .prompt { color: #c85a3a; }
.term .key    { color: #8ecf9e; }
.term .num    { color: #d8a86a; }
.term .str    { color: #b6c596; }
.term .punct  { color: #6b6558; }
```

### Two-tone tier cards (signature)
```css
.tier-1 { background: var(--ink); color: var(--cream); padding: 2.5rem 2rem; border-radius: 18px; }
.tier-2 { background: var(--white); border: 1px solid var(--line); padding: 2.5rem 2rem; border-radius: 18px; }
```

### Mega wordmark
```css
.mega-wordmark {
  font-family: var(--font-display);
  font-weight: 900;
  font-size: clamp(4rem, 17vw, 13rem);
  line-height: 0.85;
  letter-spacing: -0.06em;
  text-align: center;
  margin: -1rem auto 0;     /* negative top pulls into the stage above */
  contain: layout paint;
}
```

---

## 6 · Sizing tokens

```css
--radius-sm: 8px;     /* small UI */
--radius:    12px;    /* command boxes, code blocks */
--radius-lg: 18px;    /* cards, terminals, surfaces */
--radius-pill: 99px;  /* buttons, pills, tags */
```

Card padding: `2.25rem 2rem` (features) or `2.5rem 2rem` (tier cards).

---

## 7 · What NOT to do

- **No gradients.**
- **No drop shadows on text.**
- **No coral buttons or coral text outside `<em>`.** Coral is for italic emphasis and one hover state only.
- **No gray-on-gray.** Use `--ink-3 / --ink-4` warm grays, never `#666`.
- **No card-inside-card.**
- **No `backdrop-filter: blur()` on sticky headers.** Recomposites every scroll frame.
- **No `box-shadow` keyframes.** Use `transform` + `opacity` on a pseudo-element.
- **No emoji as decoration.** Country flags or status icons only.
- **No more than two italic-coral emphasis words per headline.**

---

## 8 · Performance rules

1. **Animate only `transform` and `opacity`** (GPU-composited).
2. **Avoid `backdrop-filter` on scroll-sticky elements** — use solid color.
3. **Static `box-shadow` is fine; animated `box-shadow` is not.**
4. **`will-change: transform, opacity`** on actively animating elements only.
5. **`content-visibility: auto`** on every below-fold section — biggest single win:
   ```css
   .section, footer { content-visibility: auto; contain-intrinsic-size: auto 700px; }
   ```
6. **`contain: paint`** on self-contained heavy elements (terminal, data cards, mega wordmark).
7. **Always include `prefers-reduced-motion`:**
   ```css
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.001ms !important;
       animation-iteration-count: 1 !important;
       transition-duration: 0.001ms !important;
     }
     html { scroll-behavior: auto; }
   }
   ```
8. **`overflow-x: clip`** instead of `hidden` on body when floating pills overflow.

---

## 9 · Responsive breakpoints

```css
@media (max-width: 1024px) {
  .features-grid { grid-template-columns: 1fr; }
  .docs-grid     { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .nav-links a:not(.nav-cta) { display: none; }
  .steps-grid { grid-template-columns: 1fr; }
  .changelog-row { grid-template-columns: 1fr; }
}
```

The mega wordmark scales beautifully via `clamp()` — no breakpoint needed.

---

## 10 · Quick-start skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;700;800;900&family=Inter:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --cream: #ede8da; --paper: #f4efe2; --white: #fff;
      --ink: #0e0e0b; --ink-2: #2a2520; --ink-3: #6b6555;
      --coral: #c85a3a;
      --line: rgba(14,14,11,0.10);
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--cream); color: var(--ink); line-height: 1.55;
    }
    h1, h2, h3 {
      font-family: 'Inter Tight', sans-serif;
      letter-spacing: -0.04em; line-height: 1.05;
    }
    h1 em, h2 em, h3 em {
      font-style: italic; font-weight: 500;
      color: var(--coral);
      font-family: 'Instrument Serif', serif;
    }
  </style>
</head>
<body>
  <h1 style="font-size:5rem; font-weight:800;">
    A bold idea<br>delivered with <em>style</em>.
  </h1>
</body>
</html>
```

That's the system in one snippet. The rest is consistent application of these tokens.

---

## 11 · Production setup (Next.js)

For real projects, use the Next.js 16 + App Router setup in `web/` of this repo:

- **`next/font/google`** self-hosts Inter Tight, Inter, Instrument Serif, JetBrains Mono — no Google Fonts CDN, no FOUT
- **Server components by default** — interactive bits (tabs, copy buttons) are the only `"use client"` files
- **Static export** (`output: 'export'`) — deploys to any static host
- **`content-visibility: auto`** + **`contain: paint`** baked into globals.css
