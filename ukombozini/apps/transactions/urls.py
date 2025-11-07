from django.urls import path
from . import views

urlpatterns = [
    # Cash In Transactions
    path('cash-in/', views.CashInTransactionListView.as_view(), name='cash-in-list'),
    path('cash-in/<int:pk>/', views.CashInTransactionDetailView.as_view(), name='cash-in-detail'),
    path('cash-in/<int:transaction_id>/verify/', views.verify_cash_in_transaction, name='verify-cash-in'),

    # Cash Out Transactions
    path('cash-out/', views.CashOutTransactionListView.as_view(), name='cash-out-list'),
    path('cash-out/<int:pk>/', views.CashOutTransactionDetailView.as_view(), name='cash-out-detail'),
    path('cash-out/<int:transaction_id>/approve/', views.approve_cash_out_transaction, name='approve-cash-out'),
    path('cash-out/<int:transaction_id>/pay/', views.mark_cash_out_paid, name='mark-cash-out-paid'),

    # Reconciliations
    path('reconciliations/', views.TransactionReconciliationView.as_view(), name='reconciliation-list'),

    # Categories
    path('categories/', views.TransactionCategoryView.as_view(), name='transaction-categories'),

    # Financial Reports
    path('groups/<int:group_id>/financial-summary/', views.financial_summary, name='financial-summary'),
    path('dashboard-statistics/', views.dashboard_statistics, name='dashboard-statistics'),
]
