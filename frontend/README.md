# Supplement Tracker — Frontend

React (Vite) frontend for the Supplement Restock Tracker.

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
- `src/App.jsx` — top-level state (loads the list, opens/closes the form)
- `src/components/SupplementList.jsx` — list + empty state
- `src/components/SupplementCard.jsx` — one supplement, with the capsule-shaped
  supply gauge and restock/edit/delete actions
- `src/components/SupplementForm.jsx` — modal used for both add and edit

## Design notes

Cards are color-coded by status (`ok` / `low` / `critical` / `overdue`, computed
by the backend) via a left border accent and badge. The capsule progress bar
shows remaining supply as a fraction of the original bottle size.