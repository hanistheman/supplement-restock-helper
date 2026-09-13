# Supplement Tracker — Frontend

React (Vite) + Tailwind CSS frontend for the Supplement Restock Tracker.

## Setup

```bash
cd frontend
npm install
```

## Run

Make sure the backend is running first (see `../backend/README.md`), then:

```bash
npm run dev
```

Open http://localhost:5173. The app talks to the API at `http://127.0.0.1:8000`
(configured in `src/api.js` — change `BASE_URL` if your backend runs elsewhere).

## Structure

- `src/api.js` — fetch wrapper for all backend calls
- `src/App.jsx` — router shell (nav bar + routes)
- `src/pages/` — `ShelfPage` (main view), `AboutPage`, `HelpPage`
- `src/components/` — `SupplementList`, `SupplementCard`, `SupplementForm`,
  `SourceList`, `ShelfControls`, `NavBar`

## Styling: Tailwind CSS

Styling uses Tailwind CSS v4 (utility classes in JSX, no per-component
`.css` files). The design tokens (colors, fonts) are defined once in
`src/index.css` under `@theme`, and map to utility classes like `bg-accent`,
`text-ink-soft`, `font-display`:

```css
@theme {
  --color-accent: #2f6f62;
  --font-display: "Space Grotesk", sans-serif;
  /* ... */
}
```

Status-based styling (the `ok` / `low` / `critical` / `overdue` states on
each card) uses lookup objects mapping status to full Tailwind class
strings, rather than building class names with string interpolation —
Tailwind's compiler needs complete class names present in the source to
generate the corresponding CSS, so dynamically concatenated class names
(e.g. `` `text-${status}` ``) won't work.

## Design notes

Cards are color-coded by status (computed by the backend) via a left
border accent and badge. The capsule-shaped progress bar shows remaining
supply as a fraction of the original bottle size.