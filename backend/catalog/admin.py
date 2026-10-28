from django.contrib import admin

from .models import Achievement, Game


class AchievementInline(admin.TabularInline):
    model = Achievement
    extra = 0
    fields = ['sort_order', 'api_name', 'name', 'description', 'hidden', 'icon_url', 'icon_gray_url']


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'steam_app_id', 'is_reviewed', 'achievement_count', 'updated_at']
    list_editable = ['is_reviewed']
    list_filter = ['is_reviewed']
    search_fields = ['title', 'slug', 'steam_app_id']
    prepopulated_fields = {'slug': ['title']}
    inlines = [AchievementInline]

    @admin.display(description='achievements')
    def achievement_count(self, obj):
        return obj.achievements.count()


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'game', 'api_name', 'hidden', 'sort_order']
    list_filter = ['hidden', 'game']
    search_fields = ['name', 'api_name', 'description', 'game__title']
    list_select_related = ['game']
