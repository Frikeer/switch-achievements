from django.core.management.base import BaseCommand, CommandError

from catalog.services import CatalogImportError, fetch_steam_game, upsert_game

from ._output import report


class Command(BaseCommand):
    help = 'Import a game and its achievement list from the Steam Web API (needs STEAM_API_KEY).'

    def add_arguments(self, parser):
        parser.add_argument('app_id', type=int, help='Steam app ID, e.g. 367520 for Hollow Knight')
        parser.add_argument('--title', help='Override the game title (and the slug derived from it)')
        parser.add_argument('--slug', help='Override the slug')
        parser.add_argument('--switch2', action='store_true', help='Mark the game as available on Switch 2')
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Replace existing game/achievement fields with Steam data (discards hand edits)',
        )
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Delete achievements no longer on Steam (ones users have unlocked are kept)',
        )

    def handle(self, *args, app_id, title, slug, switch2, overwrite, prune, **options):
        try:
            data = fetch_steam_game(app_id)
            if title:
                data['title'] = title
            if slug:
                data['slug'] = slug
            if switch2:
                data['on_switch2'] = True
            result = upsert_game(data, overwrite=overwrite, prune=prune)
        except CatalogImportError as e:
            raise CommandError(str(e)) from e
        report(self, result)
