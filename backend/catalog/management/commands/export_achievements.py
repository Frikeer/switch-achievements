import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Game
from catalog.services import export_game


class Command(BaseCommand):
    help = 'Export games and their achievements to JSON files (one file per game) for editing.'

    def add_arguments(self, parser):
        parser.add_argument('slugs', nargs='*', help='Game slugs to export')
        parser.add_argument('--all', action='store_true', dest='export_all', help='Export every game')
        parser.add_argument('-o', '--output', default='exports', help='Output directory (default: exports/)')

    def handle(self, *args, slugs, export_all, output, **options):
        if export_all:
            games = Game.objects.all()
        elif slugs:
            games = Game.objects.filter(slug__in=slugs)
            missing = set(slugs) - set(games.values_list('slug', flat=True))
            if missing:
                raise CommandError(f'Unknown game slug(s): {", ".join(sorted(missing))}')
        else:
            raise CommandError('Pass one or more game slugs, or --all')

        out_dir = Path(output)
        out_dir.mkdir(parents=True, exist_ok=True)
        for game in games.prefetch_related('achievements'):
            path = out_dir / f'{game.slug}.json'
            path.write_text(json.dumps(export_game(game), indent=2, ensure_ascii=False) + '\n')
            self.stdout.write(f'Wrote {path}')
