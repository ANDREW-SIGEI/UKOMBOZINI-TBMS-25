from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'members', views.MemberViewSet, basename='member')
router.register(r'next-of-kin', views.NextOfKinViewSet, basename='next-of-kin')
router.register(r'member-documents', views.MemberDocumentViewSet, basename='member-document')
router.register(r'member-savings', views.MemberSavingsViewSet, basename='member-savings')
router.register(r'member-activities', views.MemberActivityViewSet, basename='member-activity')
router.register(r'credit-score-history', views.CreditScoreHistoryViewSet, basename='credit-score-history')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.member_dashboard, name='member-dashboard'),
]
