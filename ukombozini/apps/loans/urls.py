from django.urls import path
from . import views

urlpatterns = [
    # Loan Management
    path('', views.LoanListView.as_view(), name='loan-list'),
    path('<int:pk>/', views.LoanDetailView.as_view(), name='loan-detail'),

    # Loan Actions
    path('<int:loan_id>/verify-id/', views.verify_loan_id, name='verify-loan-id'),
    path('<int:loan_id>/disburse/', views.disburse_loan, name='disburse-loan'),
    path('<int:loan_id>/repayments/', views.LoanRepaymentListView.as_view(), name='loan-repayment-list'),

    # Guarantor Management
    path('guarantors/', views.GuarantorListView.as_view(), name='guarantor-list'),
    path('guarantors/<int:pk>/', views.GuarantorDetailView.as_view(), name='guarantor-detail'),
    path('<int:loan_id>/available-guarantors/', views.available_guarantors, name='available-guarantors'),
    path('<int:loan_id>/add-guarantor/', views.add_guarantor, name='add-guarantor'),
    path('guarantors/<int:guarantor_id>/approve/', views.approve_guarantor, name='approve-guarantor'),

    # Loan Applications
    path('applications/', views.LoanApplicationView.as_view(), name='loan-application-list'),
    path('<int:loan_id>/applications/', views.LoanApplicationView.as_view(), name='loan-specific-application-list'),
    path('applications/<int:application_id>/submit/', views.submit_loan_application, name='submit-loan-application'),

    # Top-up Loans
    path('top-ups/', views.LoanTopUpView.as_view(), name='loan-topup-list'),
    path('<int:loan_id>/top-ups/', views.LoanTopUpView.as_view(), name='loan-specific-topup-list'),

    # Statistics
    path('statistics/', views.loan_statistics, name='loan-statistics'),
]
