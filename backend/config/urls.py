from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from catalog.views import GameViewSet
from tracking.views import LibraryGameView, StatsView, UnlockView

router = DefaultRouter()
router.register('games', GameViewSet, basename='game')

api_patterns = [
    path('', include(router.urls)),
    path('me/games/<slug:slug>/', LibraryGameView.as_view(), name='library-game'),
    path('me/achievements/<int:achievement_id>/', UnlockView.as_view(), name='unlock'),
    path('me/stats/', StatsView.as_view(), name='stats'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_patterns)),
    path('_allauth/', include('allauth.headless.urls')),
]
