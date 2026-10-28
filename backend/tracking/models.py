from django.conf import settings
from django.db import models
from django.utils import timezone

from catalog.models import Achievement, Game


class UserGame(models.Model):
    """A game in a user's library."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='games')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='owners')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'game'], name='unique_user_game'),
        ]

    def __str__(self):
        return f'{self.user} - {self.game}'


class UserAchievement(models.Model):
    """An achievement a user has ticked off. Unticking deletes the row."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='unlocks')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='unlocks')
    unlocked_at = models.DateField(default=timezone.localdate)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-unlocked_at', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'achievement'], name='unique_user_achievement'),
        ]

    def __str__(self):
        return f'{self.user} - {self.achievement}'
