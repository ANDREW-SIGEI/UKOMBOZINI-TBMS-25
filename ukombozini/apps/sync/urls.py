from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sync', views.SyncViewSet, basename='sync')
router.register(r'conflicts', views.SyncConflictViewSet, basename='sync-conflicts')
router.register(r'sessions', views.SyncSessionViewSet, basename='sync-sessions')

urlpatterns = [
    path('', include(router.urls)),
]
