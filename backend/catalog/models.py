from django.db import models


class Game(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    steam_app_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    cover_url = models.URLField(blank=True)
    # Imports create unreviewed games; only reviewed ones are shown on the site.
    is_reviewed = models.BooleanField('reviewed', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Achievement(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='achievements')
    # Steam's internal achievement key; matches achievements across re-imports.
    api_name = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    hidden = models.BooleanField(default=False)
    icon_url = models.URLField(blank=True)
    icon_gray_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['game', 'sort_order', 'id']
        constraints = [
            models.UniqueConstraint(fields=['game', 'api_name'], name='unique_achievement_per_game'),
        ]

    def __str__(self):
        return f'{self.game}: {self.name}'
