from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DividendPeriodViewSet, MemberDividendViewSet, DividendViewSet

router = DefaultRouter()
router.register(r'periods', DividendPeriodViewSet)
router.register(r'member-dividends', MemberDividendViewSet)
router.register(r'dividends', DividendViewSet)  # Legacy endpoint

urlpatterns = [
    path('', include(router.urls)),
]
