from rest_framework import serializers

from .models import Achievement, Game


class GameListSerializer(serializers.ModelSerializer):
    achievement_count = serializers.IntegerField(read_only=True)
    # Per-user fields; None for anonymous visitors.
    unlocked_count = serializers.IntegerField(read_only=True, default=None)
    in_library = serializers.BooleanField(read_only=True, default=None)

    class Meta:
        model = Game
        fields = [
            'slug',
            'title',
            'steam_app_id',
            'cover_url',
            'on_switch1',
            'on_switch2',
            'achievement_count',
            'unlocked_count',
            'in_library',
        ]


class AchievementSerializer(serializers.ModelSerializer):
    unlocked_at = serializers.SerializerMethodField()
    note = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = ['id', 'api_name', 'name', 'description', 'hidden', 'icon_url', 'icon_gray_url', 'unlocked_at', 'note']

    def _unlock(self, obj):
        unlocks = getattr(obj, 'my_unlocks', None)
        return unlocks[0] if unlocks else None

    def get_unlocked_at(self, obj):
        unlock = self._unlock(obj)
        return unlock.unlocked_at if unlock else None

    def get_note(self, obj):
        unlock = self._unlock(obj)
        return unlock.note if unlock else ''


class GameDetailSerializer(GameListSerializer):
    achievements = AchievementSerializer(many=True, read_only=True)

    class Meta(GameListSerializer.Meta):
        fields = GameListSerializer.Meta.fields + ['achievements']
