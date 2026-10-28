from django.utils import timezone
from rest_framework import serializers

from .models import UserAchievement


class UnlockSerializer(serializers.ModelSerializer):
    """Body for ticking an achievement; both fields are optional."""

    unlocked_at = serializers.DateField(required=False)

    class Meta:
        model = UserAchievement
        fields = ['unlocked_at', 'note']
        extra_kwargs = {'note': {'required': False}}

    def validate_unlocked_at(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('Unlock date cannot be in the future.')
        return value


class RecentUnlockSerializer(serializers.ModelSerializer):
    achievement_id = serializers.IntegerField(source='achievement.id')
    name = serializers.CharField(source='achievement.name')
    icon_url = serializers.CharField(source='achievement.icon_url')
    game_slug = serializers.CharField(source='achievement.game.slug')
    game_title = serializers.CharField(source='achievement.game.title')

    class Meta:
        model = UserAchievement
        fields = ['achievement_id', 'name', 'icon_url', 'game_slug', 'game_title', 'unlocked_at', 'note']
