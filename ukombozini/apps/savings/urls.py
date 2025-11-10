from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SavingsTransactionViewSet

router = DefaultRouter()
router.register(r'savings-transactions', SavingsTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
