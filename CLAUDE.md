# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A website where users manually tick off achievements for Nintendo Switch / Switch 2 games. The consoles have no achievement system, so achievement lists are imported from Steam. Licensed AGPL-3.0, so any dependency must be AGPL-compatible.

- `backend/`: Django 6.1 + Django REST Framework + django-allauth (headless), SQLite, managed with **uv**
- `frontend/`: React 19 + Vite + TypeScript, React Router, TanStack Query, Tailwind v4 + shadcn/ui

## Commands

Backend (run from `backend/`):
```sh
uv run python manage.py migrate
uv run python manage.py runserver            # http://127.0.0.1:8000 (admin at /admin/)
uv run python manage.py createsuperuser
uv run pytest                                # all tests
uv run pytest tracking/tests.py::TestStatsApi::test_stats   # single test
uv run ruff check . && uv run ruff format .
```

Frontend (run from `frontend/`):
```sh
npm run dev      # http://localhost:5173 (proxies /api, /_allauth, /admin to Django)
npm run build    # tsc -b + vite build (the type check lives here)
npm run lint     # oxlint
npm test         # vitest run; single file: npx vitest run src/lib/api.test.ts
npx shadcn@latest add <component>   # adds to src/components/ui/
```

Catalog data (from `backend/`):
```sh
uv run --env-file .env python manage.py import_steam 367520 [--title ...] [--overwrite] [--prune]
uv run python manage.py export_achievements <slug...> | --all  [-o exports/]
uv run python manage.py import_achievements sample_data/demo-quest.json [--prune]
```

## Architecture

**Data flow for the catalog.** The database is the source of truth, and admins edit it in the Django admin. All imports and exports go through one JSON shape, documented at the top of `catalog/services.py`. `fetch_steam_game()` converts Steam's schema into that shape, and `upsert_game()` applies it. Achievements are matched on `api_name` (Steam's key), and list order becomes `sort_order`. `import_steam` defaults to `overwrite=False`, so hand edits survive re-imports. `import_achievements` overwrites because the JSON file *is* the edit. `prune` never deletes achievements that users have unlocked.

**Review flag.** `Game.is_reviewed` defaults to `False`, so every import creates a hidden game. It isn't part of the JSON shape, so imports can't set or reset it, and only the admin publishes a game. Every user-facing query filters on `is_reviewed=True`: `GameViewSet`, ticking, adding to the library, and stats. Keep that filter on any new endpoint that exposes games.

**Apps.**
- `catalog`: `Game`, `Achievement`, the read-only `GameViewSet`, and the import/export commands.
- `tracking`: `UserGame` (the user's library) and `UserAchievement` (one row per ticked achievement; unticking deletes the row; `unlocked_at` is a user-editable date). It also has the `/api/me/...` views.
- Ticking an achievement auto-adds its game to the library. Removing a game from the library keeps its unlocks, but stats only count library games.
- `GameViewSet` annotates per-user fields (`unlocked_count`, `in_library`, and on detail each achievement's `unlocked_at` / `note` via a `my_unlocks` prefetch). These fields are `null` for anonymous users.

**Auth.** django-allauth runs in headless mode (`HEADLESS_ONLY`). The React app renders every account page and calls `/_allauth/browser/v1/...`, and `HEADLESS_FRONTEND_URLS` points email links at SPA routes (`/account/verify-email/:key`, etc.). Auth uses session cookies, with no tokens. The SPA reads the `csrftoken` cookie and sends `X-CSRFToken` on unsafe requests (`frontend/src/lib/api.ts`). allauth's browser endpoints set that cookie, and the app fetches the session on load. allauth answers **401 for normal states** like "verification pending" or "logged out", so `frontend/src/lib/auth.ts` returns those bodies instead of throwing. Login is email only, verification is mandatory, and `ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION` logs the user in when the link is opened in the same session that signed up.

**Frontend state.** All server data lives in TanStack Query. Query keys don't include the user: `useAuthMutation` resets every non-session query when the auth state changes. Achievement toggles update `['game', slug]` optimistically, then invalidate `['games']` and `['stats']`. Shared UI helpers live in `src/components/common.tsx`. Non-component helpers go in `src/lib/`, because oxlint's fast-refresh rule rejects mixed exports outside `components/ui/`.

## Gotchas

- In dev, emails print to the Django console as quoted-printable text, so long verification and reset links are split by a trailing `=`. Join the two lines (drop the `=`) before opening the link.
- `STEAM_API_KEY` is only needed for `import_steam` (get one at https://steamcommunity.com/dev/apikey). It lives in the gitignored `backend/.env` and is loaded with `uv run --env-file .env`. Never read, print or commit that file, and never put the key inline in a command. The Steam schema's `gameName` is often an internal name, so the title and cover come from the Steam store API instead, and `--title` overrides both.
- `backend/sample_data/demo-quest.json` is a fictional game for local development. It isn't real Steam data.
