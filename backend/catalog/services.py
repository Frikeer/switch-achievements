"""Import/export of games and achievements.

Everything goes through one JSON shape (see ``export_game``), so a Steam import,
a hand-edited JSON file and an export all round-trip through ``upsert_game``:

    {
      "title": "Hollow Knight",
      "slug": "hollow-knight",
      "steam_app_id": 367520,
      "cover_url": "https://...",
      "on_switch1": true,
      "on_switch2": false,
      "achievements": [
        {"api_name": "ACH_1", "name": "...", "description": "...", "hidden": false,
         "icon_url": "https://...", "icon_gray_url": "https://..."}
      ]
    }

Achievement order in the list becomes ``sort_order``.
"""

from dataclasses import dataclass, field

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify

from .models import Achievement, Game

GAME_FIELDS = ['title', 'steam_app_id', 'cover_url', 'on_switch1', 'on_switch2']
ACHIEVEMENT_FIELDS = ['name', 'description', 'hidden', 'icon_url', 'icon_gray_url']

STEAM_SCHEMA_URL = 'https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/'
STEAM_STORE_URL = 'https://store.steampowered.com/api/appdetails'


class CatalogImportError(Exception):
    pass


@dataclass
class UpsertResult:
    game: Game
    game_created: bool = False
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    # Missing from the input but kept because users have unlocked them.
    kept_with_progress: list[str] = field(default_factory=list)


def export_game(game: Game) -> dict:
    data = {'title': game.title, 'slug': game.slug}
    data.update({f: getattr(game, f) for f in GAME_FIELDS if f != 'title'})
    data['achievements'] = [
        {'api_name': a.api_name, **{f: getattr(a, f) for f in ACHIEVEMENT_FIELDS}} for a in game.achievements.all()
    ]
    return data


def validate(obj):
    """Run model validation, since imported data skips forms (e.g. a slug like "../x")."""
    try:
        obj.full_clean()
    except ValidationError as e:
        errors = '; '.join(f'{f}: {" ".join(msgs)}' for f, msgs in e.message_dict.items())
        raise CatalogImportError(f'{obj}: {errors}') from e


@transaction.atomic
def upsert_game(data: dict, *, overwrite: bool = True, prune: bool = False) -> UpsertResult:
    """Create or update a game and its achievements from the JSON shape above.

    overwrite: update fields of existing game/achievements. When False, only new
        achievements are added and existing (possibly hand-edited) data is kept.
    prune: delete achievements missing from ``data``, except ones with user progress.
    """
    if not data.get('title'):
        raise CatalogImportError('"title" is required')
    slug = data.get('slug') or slugify(data['title'])
    app_id = data.get('steam_app_id')
    if app_id is not None and type(app_id) is not int:
        raise CatalogImportError('"steam_app_id" must be a number')

    game = Game.objects.filter(slug=slug).first()
    if game is None and app_id:
        game = Game.objects.filter(steam_app_id=app_id).first()

    result = UpsertResult(game=game)
    if game is None:
        game = Game(slug=slug)
        result.game, result.game_created = game, True
    if result.game_created or overwrite:
        for f in GAME_FIELDS:
            if f in data:
                setattr(game, f, data[f])
        game.cover_url = game.cover_url or ''
        game.slug = slug
        validate(game)
        game.save()

    existing = {a.api_name: a for a in game.achievements.all()}
    seen = set()
    for order, item in enumerate(data.get('achievements', [])):
        api_name = item.get('api_name')
        if not api_name or not item.get('name'):
            raise CatalogImportError(f'achievement #{order + 1} needs "api_name" and "name"')
        if api_name in seen:
            raise CatalogImportError(f'duplicate api_name "{api_name}"')
        seen.add(api_name)

        values = {f: item.get(f) or '' for f in ACHIEVEMENT_FIELDS}
        values['hidden'] = bool(item.get('hidden'))
        values['sort_order'] = order
        achievement = existing.get(api_name)
        if achievement is None:
            achievement = Achievement(game=game, api_name=api_name, **values)
            validate(achievement)
            achievement.save()
            result.created.append(api_name)
        elif overwrite:
            changed = [f for f, v in values.items() if getattr(achievement, f) != v]
            if changed:
                for f in changed:
                    setattr(achievement, f, values[f])
                validate(achievement)
                achievement.save(update_fields=changed)
                result.updated.append(api_name)

    if prune:
        missing = game.achievements.exclude(api_name__in=seen).annotate(n_unlocks=Count('unlocks'))
        for achievement in missing:
            if achievement.n_unlocks:
                result.kept_with_progress.append(achievement.api_name)
            else:
                achievement.delete()
                result.deleted.append(achievement.api_name)

    return result


def fetch_steam_game(app_id: int, *, api_key: str | None = None, timeout: int = 20) -> dict:
    """Fetch a game's achievement schema from Steam, returned in the JSON shape above."""
    api_key = api_key or settings.STEAM_API_KEY
    if not api_key:
        raise CatalogImportError('STEAM_API_KEY is not set (get one at https://steamcommunity.com/dev/apikey)')

    try:
        resp = requests.get(STEAM_SCHEMA_URL, params={'key': api_key, 'appid': app_id, 'l': 'english'}, timeout=timeout)
        if resp.status_code == 403:
            raise CatalogImportError('Steam rejected the API key (HTTP 403)')
        resp.raise_for_status()
        schema = resp.json().get('game') or {}
    except requests.RequestException as e:
        # requests' messages include the URL, which contains the API key, so drop them.
        reason = f'HTTP {e.response.status_code}' if e.response is not None else type(e).__name__
        raise CatalogImportError(f'Steam schema request failed ({reason})') from None
    steam_achievements = schema.get('availableGameStats', {}).get('achievements', [])
    if not steam_achievements:
        raise CatalogImportError(f'Steam has no achievements for app {app_id}')

    # The schema's gameName is often an internal name, so prefer the store's.
    title, cover_url = schema.get('gameName', ''), ''
    try:
        store = requests.get(STEAM_STORE_URL, params={'appids': app_id}, timeout=timeout).json()
        details = store.get(str(app_id), {})
        if details.get('success'):
            title = details['data'].get('name') or title
            cover_url = details['data'].get('header_image', '')
    except requests.RequestException, ValueError:
        pass

    return {
        'title': title,
        'steam_app_id': app_id,
        'cover_url': cover_url,
        'achievements': [
            {
                'api_name': a['name'],
                'name': a.get('displayName') or a['name'],
                'description': a.get('description', ''),
                'hidden': bool(a.get('hidden')),
                'icon_url': a.get('icon', ''),
                'icon_gray_url': a.get('icongray', ''),
            }
            for a in steam_achievements
        ],
    }
