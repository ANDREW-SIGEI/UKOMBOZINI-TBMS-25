from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User Management
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('update-location/', views.update_location, name='update-location'),

    # User Lists
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('officers/', views.OfficerListView.as_view(), name='officer-list'),

    # Activity Tracking
    path('activities/', views.UserActivityView.as_view(), name='user-activities'),
    path('officers/<int:officer_id>/activities/', views.OfficerActivityView.as_view(), name='officer-activities'),
]
