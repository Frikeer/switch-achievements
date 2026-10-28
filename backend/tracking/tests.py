import datetime
import re
from urllib.parse import unquote

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import Achievement
from catalog.services import upsert_game

from .models import UserAchievement, UserGame

pytestmark = pytest.mark.django_db


def make_game(title, achievements, *, reviewed=True):
    game = upsert_game({'title': title, 'achievements': achievements}).game
    game.is_reviewed = reviewed
    game.save()
    return game


@pytest.fixture
def game():
    return make_game('Hollow Knight', [{'api_name': f'A{i}', 'name': f'Achievement {i}'} for i in range(4)])


@pytest.fixture
def other_game():
    return make_game('Celeste', [{'api_name': 'C', 'name': 'Summit'}])


@pytest.fixture
def unreviewed_game():
    return make_game('Hades', [{'api_name': 'H', 'name': 'Escape'}], reviewed=False)


def make_user(email):
    return get_user_model().objects.create_user(username=email, email=email, password='pw-12345678')


@pytest.fixture
def user():
    return make_user('player@example.com')


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def ach(game, n):
    return game.achievements.get(api_name=f'A{n}')


class TestCatalogApi:
    def test_anonymous_can_browse(self, game):
        resp = APIClient().get('/api/games/')
        assert resp.status_code == 200, resp.content
        assert resp.json()[0] | {} == {
            'slug': 'hollow-knight',
            'title': 'Hollow Knight',
            'steam_app_id': None,
            'cover_url': '',
            'achievement_count': 4,
            'unlocked_count': None,
            'in_library': None,
        }

    def test_unreviewed_games_are_hidden(self, client, game, unreviewed_game):
        assert [g['slug'] for g in client.get('/api/games/').json()] == ['hollow-knight']
        assert client.get('/api/games/hades/').status_code == 404

    def test_search(self, client, game, other_game):
        assert [g['slug'] for g in client.get('/api/games/?q=cele').json()] == ['celeste']

    def test_list_includes_user_progress(self, client, user, game, other_game):
        UserAchievement.objects.create(user=user, achievement=ach(game, 0))
        UserAchievement.objects.create(user=make_user('x@example.com'), achievement=ach(game, 1))
        UserGame.objects.create(user=user, game=game)

        games = {g['slug']: g for g in client.get('/api/games/').json()}
        assert (games['hollow-knight']['unlocked_count'], games['hollow-knight']['in_library']) == (1, True)
        assert (games['celeste']['unlocked_count'], games['celeste']['in_library']) == (0, False)

    def test_library_filter(self, client, user, game, other_game):
        UserGame.objects.create(user=user, game=other_game)
        assert [g['slug'] for g in client.get('/api/games/?library=1').json()] == ['celeste']

    def test_detail_shows_only_own_unlocks(self, client, user, game):
        UserAchievement.objects.create(user=user, achievement=ach(game, 2), note='mine')
        UserAchievement.objects.create(user=make_user('x@example.com'), achievement=ach(game, 3), note='theirs')

        achievements = client.get('/api/games/hollow-knight/').json()['achievements']
        assert [a['api_name'] for a in achievements] == ['A0', 'A1', 'A2', 'A3']
        assert [a['note'] for a in achievements] == ['', '', 'mine', '']
        assert achievements[2]['unlocked_at'] == timezone.localdate().isoformat()
        assert achievements[3]['unlocked_at'] is None


class TestUnlockApi:
    def test_requires_login(self, game):
        a = ach(game, 0)
        assert APIClient().put(f'/api/me/achievements/{a.id}/').status_code == 403

    def test_tick_defaults_to_today_and_adds_to_library(self, client, user, game):
        resp = client.put(f'/api/me/achievements/{ach(game, 0).id}/')

        assert resp.status_code == 201
        assert resp.json()['unlocked_at'] == timezone.localdate().isoformat()
        assert UserGame.objects.filter(user=user, game=game).exists()

    def test_edit_date_and_note(self, client, user, game):
        url = f'/api/me/achievements/{ach(game, 0).id}/'
        client.put(url)
        resp = client.put(url, {'unlocked_at': '2024-05-01', 'note': 'Finally!'}, format='json')

        assert resp.status_code == 200, resp.content
        unlock = UserAchievement.objects.get(user=user)
        assert (unlock.unlocked_at, unlock.note) == (datetime.date(2024, 5, 1), 'Finally!')

    def test_future_date_rejected(self, client, game):
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        resp = client.put(f'/api/me/achievements/{ach(game, 0).id}/', {'unlocked_at': str(tomorrow)}, format='json')
        assert resp.status_code == 400
        assert UserAchievement.objects.count() == 0

    def test_untick_only_affects_own_unlock(self, client, user, game):
        a = ach(game, 0)
        UserAchievement.objects.create(user=user, achievement=a)
        UserAchievement.objects.create(user=make_user('x@example.com'), achievement=a)

        assert client.delete(f'/api/me/achievements/{a.id}/').status_code == 204
        assert list(UserAchievement.objects.values_list('user__email', flat=True)) == ['x@example.com']

    def test_unknown_achievement(self, client):
        assert client.put('/api/me/achievements/9999/').status_code == 404

    def test_cannot_tick_unreviewed_game(self, client, unreviewed_game):
        assert client.put(f'/api/me/achievements/{unreviewed_game.achievements.get().id}/').status_code == 404
        assert not UserAchievement.objects.exists()
        assert not UserGame.objects.exists()


class TestLibraryApi:
    def test_add_and_remove_keeps_progress(self, client, user, game):
        assert client.put('/api/me/games/hollow-knight/').status_code == 201
        assert client.put('/api/me/games/hollow-knight/').status_code == 200
        UserAchievement.objects.create(user=user, achievement=ach(game, 0))

        assert client.delete('/api/me/games/hollow-knight/').status_code == 204
        assert not UserGame.objects.exists()
        assert UserAchievement.objects.count() == 1

    def test_cannot_add_unreviewed_game(self, client, unreviewed_game):
        assert client.put('/api/me/games/hades/').status_code == 404


class TestStatsApi:
    def test_stats(self, client, user, game, other_game):
        for game_ in (game, other_game):
            UserGame.objects.create(user=user, game=game_)
        UserAchievement.objects.create(user=user, achievement=ach(game, 0), unlocked_at=datetime.date(2024, 1, 1))
        UserAchievement.objects.create(user=user, achievement=ach(game, 1), unlocked_at=datetime.date(2024, 3, 1))
        UserAchievement.objects.create(user=user, achievement=other_game.achievements.get())
        # Another user's progress must not leak into the numbers.
        UserAchievement.objects.create(user=make_user('x@example.com'), achievement=ach(game, 2))

        data = client.get('/api/me/stats/').json()

        assert {k: data[k] for k in ('games', 'completed_games', 'unlocked', 'total', 'percent')} == {
            'games': 2,
            'completed_games': 1,
            'unlocked': 3,
            'total': 5,
            'percent': 60.0,
        }
        per_game = {g['slug']: (g['unlocked'], g['total'], g['percent']) for g in data['per_game']}
        assert per_game == {'hollow-knight': (2, 4, 50.0), 'celeste': (1, 1, 100.0)}
        assert [u['name'] for u in data['recent_unlocks']] == ['Summit', 'Achievement 1', 'Achievement 0']

    def test_excludes_games_that_are_no_longer_reviewed(self, client, user, game):
        UserGame.objects.create(user=user, game=game)
        UserAchievement.objects.create(user=user, achievement=ach(game, 0))
        game.is_reviewed = False
        game.save()

        data = client.get('/api/me/stats/').json()
        assert (data['games'], data['unlocked'], data['recent_unlocks']) == (0, 0, [])

    def test_empty(self, client):
        data = client.get('/api/me/stats/').json()
        assert (data['games'], data['percent'], data['recent_unlocks']) == (0, 0.0, [])


class TestAuthFlow:
    """Signup -> verify email -> session, via allauth's headless browser API."""

    def test_signup_verify_login(self, game):
        c = APIClient(enforce_csrf_checks=True)
        c.get('/_allauth/browser/v1/auth/session')
        csrf = {'HTTP_X_CSRFTOKEN': c.cookies['csrftoken'].value}

        resp = c.post(
            '/_allauth/browser/v1/auth/signup',
            {'email': 'new@example.com', 'password': 'a-strong-pass-123'},
            format='json',
            **csrf,
        )
        assert resp.status_code == 401  # pending email verification
        assert c.put(f'/api/me/achievements/{ach(game, 0).id}/', **csrf).status_code == 403

        # The link is the SPA route; the key is URL-encoded in it.
        key = unquote(re.search(r'/account/verify-email/(\S+)', mail.outbox[0].body).group(1))
        resp = c.post('/_allauth/browser/v1/auth/email/verify', {'key': key}, format='json', **csrf)
        assert resp.status_code == 200, resp.content
        assert resp.json()['data']['user']['email'] == 'new@example.com'

        csrf = {'HTTP_X_CSRFTOKEN': c.cookies['csrftoken'].value}  # rotated on login
        assert c.put(f'/api/me/achievements/{ach(game, 0).id}/', **csrf).status_code == 201
        assert Achievement.objects.get(api_name='A0').unlocks.get().user.email == 'new@example.com'

    def test_missing_csrf_rejected(self, game, user):
        c = APIClient(enforce_csrf_checks=True)
        c.force_login(user)
        assert c.put(f'/api/me/achievements/{ach(game, 0).id}/').status_code == 403
