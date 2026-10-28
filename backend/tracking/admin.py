from django.contrib import admin

from .models import UserAchievement, UserGame


@admin.register(UserGame)
class UserGameAdmin(admin.ModelAdmin):
    list_display = ['user', 'game', 'added_at']
    search_fields = ['user__email', 'game__title']
    list_select_related = ['user', 'game']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'unlocked_at']
    search_fields = ['user__email', 'achievement__name', 'achievement__game__title']
    list_select_related = ['user', 'achievement__game']
