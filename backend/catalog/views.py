from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from rest_framework import viewsets

from tracking.models import UserAchievement, UserGame

from .models import Achievement, Game
from .serializers import GameDetailSerializer, GameListSerializer


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    """The reviewed games. Readable by anyone; includes the user's progress when logged in."""

    lookup_field = 'slug'

    def get_serializer_class(self):
        return GameDetailSerializer if self.action == 'retrieve' else GameListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Game.objects.filter(is_reviewed=True).annotate(achievement_count=Count('achievements', distinct=True))

        if q := self.request.query_params.get('q', '').strip():
            qs = qs.filter(title__icontains=q)
        if self.request.query_params.get('library') and user.is_authenticated:
            qs = qs.filter(owners__user=user)

        if user.is_authenticated:
            qs = qs.annotate(
                unlocked_count=Count(
                    'achievements__unlocks', filter=Q(achievements__unlocks__user=user), distinct=True
                ),
                in_library=Exists(UserGame.objects.filter(user=user, game=OuterRef('pk'))),
            )

        if self.action == 'retrieve':
            achievements = Achievement.objects.all()
            if user.is_authenticated:
                achievements = achievements.prefetch_related(
                    Prefetch('unlocks', queryset=UserAchievement.objects.filter(user=user), to_attr='my_unlocks')
                )
            qs = qs.prefetch_related(Prefetch('achievements', queryset=achievements))
        return qs
