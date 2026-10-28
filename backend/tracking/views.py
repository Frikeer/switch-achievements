from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Achievement, Game

from .models import UserAchievement, UserGame
from .serializers import RecentUnlockSerializer, UnlockSerializer

RECENT_UNLOCKS = 10


def percent(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0


class LibraryGameView(APIView):
    """PUT adds a game to the user's library; DELETE removes it.

    Removing a game keeps its unlocks, so re-adding it restores progress.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, slug):
        game = get_object_or_404(Game, slug=slug)
        _, created = UserGame.objects.get_or_create(user=request.user, game=game)
        return Response({'in_library': True}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, slug):
        UserGame.objects.filter(user=request.user, game__slug=slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UnlockView(APIView):
    """PUT ticks an achievement (or edits its date/note); DELETE unticks it.

    Ticking an achievement also adds its game to the user's library.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, achievement_id):
        achievement = get_object_or_404(Achievement, pk=achievement_id)
        serializer = UnlockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        unlock, created = UserAchievement.objects.get_or_create(user=request.user, achievement=achievement)
        if serializer.validated_data:
            for field, value in serializer.validated_data.items():
                setattr(unlock, field, value)
            unlock.save()
        UserGame.objects.get_or_create(user=request.user, game_id=achievement.game_id)

        return Response(
            {'achievement_id': achievement.id, **UnlockSerializer(unlock).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, achievement_id):
        UserAchievement.objects.filter(user=request.user, achievement_id=achievement_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StatsView(APIView):
    """Dashboard numbers for the games in the user's library."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        games = (
            Game.objects.filter(owners__user=user)
            .annotate(
                total=Count('achievements', distinct=True),
                unlocked=Count('achievements__unlocks', filter=Q(achievements__unlocks__user=user), distinct=True),
            )
            .order_by('-owners__added_at')
        )
        per_game = [
            {
                'slug': g.slug,
                'title': g.title,
                'cover_url': g.cover_url,
                'unlocked': g.unlocked,
                'total': g.total,
                'percent': percent(g.unlocked, g.total),
            }
            for g in games
        ]
        unlocked = sum(g['unlocked'] for g in per_game)
        total = sum(g['total'] for g in per_game)
        recent = (
            UserAchievement.objects.filter(user=user, achievement__game__owners__user=user)
            .select_related('achievement__game')
            .order_by('-unlocked_at', '-created_at')[:RECENT_UNLOCKS]
        )

        return Response(
            {
                'games': len(per_game),
                'completed_games': sum(1 for g in per_game if g['total'] and g['unlocked'] == g['total']),
                'unlocked': unlocked,
                'total': total,
                'percent': percent(unlocked, total),
                'per_game': per_game,
                'recent_unlocks': RecentUnlockSerializer(recent, many=True).data,
            }
        )
