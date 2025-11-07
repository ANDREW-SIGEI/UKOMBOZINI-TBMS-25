from django.urls import path
from . import views

urlpatterns = [
    # Group Management
    path('', views.GroupListView.as_view(), name='group-list'),
    path('<int:pk>/', views.GroupDetailView.as_view(), name='group-detail'),

    # Financial Transactions - Cash In
    path('<int:group_id>/cash-in/', views.CashInTransactionListView.as_view(), name='cash-in-list'),

    # Financial Transactions - Cash Out
    path('<int:group_id>/cash-out/', views.CashOutTransactionListView.as_view(), name='cash-out-list'),

    # TRF Balance
    path('<int:group_id>/trf-balances/', views.TRFBalanceListView.as_view(), name='trf-balance-list'),

    # Financial Reports
    path('<int:group_id>/financial-summary/', views.financial_summary, name='financial-summary'),
    path('<int:group_id>/cash-in-summary/', views.cash_in_summary, name='cash-in-summary'),

    # Meetings
    path('<int:group_id>/meetings/', views.GroupMeetingListView.as_view(), name='group-meeting-list'),

    # Statistics
    path('statistics/', views.group_statistics, name='group-statistics'),
]
