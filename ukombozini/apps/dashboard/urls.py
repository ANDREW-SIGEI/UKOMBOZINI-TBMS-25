from django.urls import path
from . import views

urlpatterns = [
    # Dashboard Overview
    path('overview/', views.OfficerDashboardView.as_view(), name='dashboard-overview'),

    # Calendar & Scheduling
    path('meetings/', views.MeetingScheduleView.as_view(), name='meeting-list'),
    path('field-visits/', views.FieldVisitView.as_view(), name='field-visit-list'),
    path('events/', views.EventView.as_view(), name='event-list'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/<int:event_id>/attendance/', views.EventAttendanceView.as_view(), name='event-attendance'),
    path('events/<int:event_id>/attendance/bulk/', views.bulk_mark_attendance, name='bulk-mark-attendance'),
    path('calendar-events/', views.calendar_events, name='calendar-events'),

    # Financial Overviews
    path('loan-overview/', views.loan_overview, name='loan-overview'),
    path('savings-overview/', views.savings_overview, name='savings-overview'),

    # Performance Tracking
    path('performance-metrics/', views.performance_metrics, name='performance-metrics'),

    # Alerts
    path('alerts/', views.OfficerAlertView.as_view(), name='officer-alerts'),
    path('alerts/<int:alert_id>/read/', views.OfficerAlertView.mark_alert_read, name='mark-alert-read'),
    path('alerts/<int:alert_id>/dismiss/', views.OfficerAlertView.dismiss_alert, name='dismiss-alert'),
]
