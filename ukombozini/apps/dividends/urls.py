from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DividendViewSet

router = DefaultRouter()
router.register(r'dividends', DividendViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
