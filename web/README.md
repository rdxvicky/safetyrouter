# SafetyRouter Website (Next.js)

Source for [safety-router.com](https://safety-router.com). Built with Next.js 16 App
Router and exported as a fully static site to `../docs/` for GitHub Pages.

## Develop

```bash
cd web
npm install
npm run dev          # http://localhost:3000
```

## Build

```bash
npm run build
```

This runs `next build` (static export to `out/`) then `scripts/sync-docs.mjs`, which
copies the export into `../docs/` while preserving non-build files (`CNAME`,
`design.md`, etc.).

## Architecture

- `app/layout.tsx` — root layout. Self-hosts Inter Tight, Inter, Instrument Serif, and
  JetBrains Mono via `next/font/google` (no Google Fonts CDN, no FOUT).
- `app/page.tsx` — composes all sections.
- `app/globals.css` — design tokens + all component styles.
- `app/components/*.tsx` — one component per section. Server components by default.
  Only `Documentation.tsx` and `InstallCTA.tsx` are `"use client"` (tabs + copy buttons).

## Performance

- **Static export** — pure HTML/CSS/JS, no server runtime.
- **`next/font`** — fonts preloaded from same origin, `font-display: swap`.
- **Server components** — most of the page ships zero JavaScript.
- **`content-visibility: auto`** on every section — browser skips off-screen layout/paint.
- **`contain: paint`** on heavy elements (terminal, data cards, mega wordmark).
- **GPU-only animations** — `transform` and `opacity` on the live-pulse dot.
- **`prefers-reduced-motion`** support.

## Design system

See [`../design.md`](../design.md) for the editorial cream design system reference.
