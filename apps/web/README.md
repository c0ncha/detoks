# Detoks web

Next.js 16 (App Router, Tailwind 4). Mobile-first swipe feed that talks to the ranker API.

```bash
npm install
npm run dev          # http://localhost:3000 (start the ranker first: `make ranker` from the repo root)
```

| Route | What |
|---|---|
| `/` | pick a viewer (persona or dataset user), a ranker, and an optional daily limit |
| `/feed?user=bob&ranker=detoks&cap=10` | one feed |
| `/compare?user=bob` | Baseline and Detoks side by side |

Code map:

- `lib/api.ts`: typed client for the ranker API. Keep types in sync with `services/ranker/detoks/api.py`.
- `components/Feed.tsx`: session lifecycle, paging, break and end cards. New card types (e.g. a challenge prompt) go in its `Row` union.
- `components/VideoCard.tsx`: one clip; measures watch time and reports it when the user swipes away.

Next 16 differs from older versions; read `node_modules/next/dist/docs/` before using an unfamiliar API (see AGENTS.md).
Pages that read the URL are a server `page.tsx` that wraps a client component in `<Suspense>`.
