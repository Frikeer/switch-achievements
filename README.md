# switch-achievements

Track achievements on the Nintendo Switch and Switch 2.

The Switch has no achievement system, but many Switch games have achievement lists on Steam. This site imports those lists so you can tick off achievements as you earn them on your Switch.

## Features

- Sign up with email and password (with email verification and password reset)
- Browse and search the game catalog, and keep your own "My games" list
- Tick off achievements, with an optional unlock date and note for each one
- Hidden achievements stay blurred until you choose to reveal them
- Dashboard with overall completion, progress per game and recent unlocks
- Admins add games from Steam or from JSON files, and edit them in the Django admin

## Tech stack

- **Backend:** Django 6.1, Django REST Framework, django-allauth, SQLite, managed with [uv](https://docs.astral.sh/uv/)
- **Frontend:** React 19, TypeScript, Vite, TanStack Query, Tailwind CSS v4, shadcn/ui

## Getting started

Requirements: Python 3.14+, [uv](https://docs.astral.sh/uv/getting-started/installation/) and Node.js 20.19+ or 22.12+.

### Backend

```sh
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser   # for the admin at /admin/
uv run python manage.py import_achievements sample_data/demo-quest.json   # optional demo game
uv run python manage.py runserver
```

Imported games start out unreviewed and hidden from the site, so tick "reviewed" for the demo game in the admin to see it.

### Frontend

In a second terminal:

```sh
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server forwards `/api`, `/_allauth` and `/admin` to Django on port 8000.

While developing, emails (signup verification and password reset) are printed in the Django terminal instead of being sent. Long links in them are split across two lines with a trailing `=`. Join the lines and drop the `=` before opening the link.

## Adding games

Games are added by admins. To import a game's achievement list from Steam, you need a free [Steam Web API key](https://steamcommunity.com/dev/apikey) and the game's Steam app ID (the number in its store URL). Put the key in `backend/.env`, which is gitignored, with an editor rather than on the command line so it stays out of your shell history:

```sh
STEAM_API_KEY=your-key
```

Then pass the file to `uv run`:

```sh
cd backend
uv run --env-file .env python manage.py import_steam 367520
```

New games are imported as **unreviewed** and stay hidden from the site until an admin ticks "reviewed" in the game list at http://localhost:8000/admin/catalog/game/. Check the achievement list against the Switch version first. Re-imports never change the flag.

The key belongs to your Steam account, so keep it private. If it leaks, revoke it at https://steamcommunity.com/dev/revokekey.

| Option | Effect |
| --- | --- |
| `--title "..."` | Use a different title than the Steam store name |
| `--overwrite` | Replace hand-edited fields with fresh Steam data |
| `--prune` | Delete achievements that are no longer on Steam |

Re-importing is safe. Without `--overwrite`, your edits are kept and only new achievements are added. Achievements that users have already ticked are never deleted.

To edit achievement lists, use the Django admin at http://localhost:8000/admin/, or round-trip them through JSON:

```sh
uv run python manage.py export_achievements hollow-knight      # or --all; writes exports/<slug>.json
uv run python manage.py import_achievements exports/hollow-knight.json
```

## Development

```sh
# backend/
uv run pytest
uv run ruff check . && uv run ruff format .

# frontend/
npm test
npm run lint
npm run build
```

## License

[GNU Affero General Public License v3.0](LICENSE)
