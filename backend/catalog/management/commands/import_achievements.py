import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog.services import CatalogImportError, upsert_game

from ._output import report


class Command(BaseCommand):
    help = 'Create or update games from JSON files in the format written by export_achievements.'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', help='JSON files to import')
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Delete achievements missing from the file (ones users have unlocked are kept)',
        )

    def handle(self, *args, files, prune, **options):
        for file in files:
            try:
                data = json.loads(Path(file).read_text())
                result = upsert_game(data, overwrite=True, prune=prune)
            except (OSError, json.JSONDecodeError, CatalogImportError) as e:
                raise CommandError(f'{file}: {e}') from e
            report(self, result)
