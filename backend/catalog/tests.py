import json
from io import StringIO
from unittest import mock

import pytest
import requests
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from tracking.models import UserAchievement

from .models import Achievement, Game
from .services import CatalogImportError, export_game, fetch_steam_game, upsert_game

pytestmark = pytest.mark.django_db


def game_data(**overrides):
    data = {
        'title': 'Hollow Knight',
        'steam_app_id': 367520,
        'cover_url': 'https://example.com/cover.jpg',
        'achievements': [
            {'api_name': 'A', 'name': 'First', 'description': 'Do one thing'},
            {'api_name': 'B', 'name': 'Second', 'description': '', 'hidden': True},
        ],
    }
    data.update(overrides)
    return data


def make_user(email='player@example.com'):
    return get_user_model().objects.create_user(username=email, email=email, password='pw-12345678')


class TestUpsertGame:
    def test_creates_game_and_achievements_in_order(self):
        result = upsert_game(game_data())

        game = Game.objects.get()
        assert result.game_created
        assert game.slug == 'hollow-knight'
        assert list(game.achievements.values_list('api_name', 'sort_order', 'hidden')) == [
            ('A', 0, False),
            ('B', 1, True),
        ]

    def test_without_overwrite_keeps_hand_edits_and_adds_new(self):
        upsert_game(game_data())
        Achievement.objects.filter(api_name='A').update(name='Edited by hand')

        data = game_data()
        data['achievements'][0]['name'] = 'From Steam'
        data['achievements'].append({'api_name': 'C', 'name': 'Third'})
        result = upsert_game(data, overwrite=False)

        assert Achievement.objects.get(api_name='A').name == 'Edited by hand'
        assert result.created == ['C']
        assert result.updated == []

    def test_overwrite_updates_changed_fields_only(self):
        upsert_game(game_data())
        data = game_data(title='Hollow Knight (Switch)')
        data['achievements'][1]['description'] = 'Now revealed'

        result = upsert_game(data)

        assert Game.objects.get().title == 'Hollow Knight (Switch)'
        assert result.updated == ['B']
        assert Achievement.objects.get(api_name='B').description == 'Now revealed'

    def test_new_games_start_unreviewed_and_reimports_keep_the_flag(self):
        upsert_game(game_data())
        assert not Game.objects.get().is_reviewed

        Game.objects.update(is_reviewed=True)
        upsert_game(game_data(), overwrite=False)
        upsert_game(game_data(title='Changed'))
        assert Game.objects.get().is_reviewed

    def test_input_cannot_mark_a_game_reviewed(self):
        upsert_game(game_data(is_reviewed=True))
        game = Game.objects.get()
        assert not game.is_reviewed
        assert 'is_reviewed' not in export_game(game)

    def test_matches_existing_game_by_steam_app_id(self):
        upsert_game(game_data(slug='hk'))
        upsert_game(game_data(slug=None), overwrite=False)
        assert Game.objects.count() == 1

    def test_prune_keeps_achievements_with_progress(self):
        upsert_game(game_data())
        user = make_user()
        UserAchievement.objects.create(user=user, achievement=Achievement.objects.get(api_name='B'))

        result = upsert_game(game_data(achievements=[]), prune=True)

        assert result.deleted == ['A']
        assert result.kept_with_progress == ['B']
        assert list(Achievement.objects.values_list('api_name', flat=True)) == ['B']

    def test_no_prune_by_default(self):
        upsert_game(game_data())
        upsert_game(game_data(achievements=[]))
        assert Achievement.objects.count() == 2

    @pytest.mark.parametrize(
        'data',
        [
            {'achievements': []},
            game_data(achievements=[{'api_name': 'A'}]),
            game_data(achievements=[{'api_name': 'A', 'name': 'x'}, {'api_name': 'A', 'name': 'y'}]),
            game_data(slug='../../outside'),
            game_data(steam_app_id='not-a-number'),
            game_data(cover_url='javascript:alert(1)'),
            game_data(achievements=[{'api_name': 'A', 'name': 'x', 'icon_url': 'not a url'}]),
            game_data(achievements=[{'api_name': 'A', 'name': 'x' * 201}]),
        ],
    )
    def test_invalid_data_raises_and_writes_nothing(self, data):
        with pytest.raises(CatalogImportError):
            upsert_game(data)
        assert Game.objects.count() == 0

    def test_export_round_trips(self):
        upsert_game(game_data())
        exported = export_game(Game.objects.get())

        Game.objects.all().delete()
        upsert_game(exported)

        assert export_game(Game.objects.get()) == exported


def fake_steam_response(url, params=None, timeout=None):
    resp = mock.Mock(status_code=200)
    if 'GetSchemaForGame' in url:
        resp.json.return_value = {
            'game': {
                'gameName': 'ValveTestApp367520',
                'availableGameStats': {
                    'achievements': [
                        {
                            'name': 'ACH_1',
                            'displayName': 'Falsehood',
                            'hidden': 0,
                            'description': 'Defeat it',
                            'icon': 'https://cdn.example.com/1.jpg',
                            'icongray': 'https://cdn.example.com/1g.jpg',
                        },
                        {
                            'name': 'ACH_2',
                            'displayName': 'Secret',
                            'hidden': 1,
                            'icon': 'https://cdn.example.com/2.jpg',
                            'icongray': 'https://cdn.example.com/2g.jpg',
                        },
                    ]
                },
            }
        }
    else:
        resp.json.return_value = {
            '367520': {
                'success': True,
                'data': {'name': 'Hollow Knight', 'header_image': 'https://cdn.example.com/header.jpg'},
            }
        }
    return resp


@mock.patch('catalog.services.requests.get', side_effect=fake_steam_response)
class TestSteam:
    def test_fetch_converts_schema(self, _get):
        data = fetch_steam_game(367520, api_key='key')

        assert data['title'] == 'Hollow Knight'
        assert data['cover_url'] == 'https://cdn.example.com/header.jpg'
        assert data['achievements'][1] == {
            'api_name': 'ACH_2',
            'name': 'Secret',
            'description': '',
            'hidden': True,
            'icon_url': 'https://cdn.example.com/2.jpg',
            'icon_gray_url': 'https://cdn.example.com/2g.jpg',
        }

    def test_missing_api_key(self, _get, settings):
        settings.STEAM_API_KEY = ''
        with pytest.raises(CatalogImportError, match='STEAM_API_KEY'):
            fetch_steam_game(367520)

    def test_import_steam_command(self, _get, settings):
        settings.STEAM_API_KEY = 'key'
        out = StringIO()
        call_command('import_steam', '367520', stdout=out)

        game = Game.objects.get()
        assert (game.title, game.is_reviewed, game.achievements.count()) == ('Hollow Knight', False, 2)
        assert 'Created "Hollow Knight"' in out.getvalue()
        assert 'not reviewed yet' in out.getvalue()


@pytest.mark.parametrize(
    'error',
    [
        requests.HTTPError('500 Server Error for url: ...?key=SECRET', response=mock.Mock(status_code=500)),
        requests.ConnectionError('Max retries exceeded with url: ...?key=SECRET'),
    ],
)
def test_steam_errors_hide_api_key(error):
    with mock.patch('catalog.services.requests.get', side_effect=error):
        with pytest.raises(CatalogImportError) as exc_info:
            fetch_steam_game(367520, api_key='SECRET')

    assert 'SECRET' not in str(exc_info.value)
    assert exc_info.value.__suppress_context__


class TestJsonCommands:
    def test_export_then_import_with_edits(self, tmp_path):
        upsert_game(game_data())
        call_command('export_achievements', 'hollow-knight', '-o', str(tmp_path), stdout=StringIO())

        path = tmp_path / 'hollow-knight.json'
        data = json.loads(path.read_text())
        data['achievements'][0]['name'] = 'Renamed'
        path.write_text(json.dumps(data))
        call_command('import_achievements', str(path), stdout=StringIO())

        assert Achievement.objects.get(api_name='A').name == 'Renamed'

    def test_export_unknown_slug(self, tmp_path):
        with pytest.raises(CommandError, match='nope'):
            call_command('export_achievements', 'nope', '-o', str(tmp_path))

    def test_import_bad_json(self, tmp_path):
        path = tmp_path / 'bad.json'
        path.write_text('{not json')
        with pytest.raises(CommandError, match='bad.json'):
            call_command('import_achievements', str(path))
