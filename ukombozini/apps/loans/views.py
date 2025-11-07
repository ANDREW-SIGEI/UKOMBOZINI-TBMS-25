from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from .models import Loan, LoanRepayment, IDVerification, LoanTopUp, Guarantor, LoanApplication
from .serializers import (
    LoanSerializer, LoanCreateSerializer, LoanRepaymentSerializer,
    IDVerificationSerializer, LoanTopUpSerializer, GuarantorSerializer,
    AvailableGuarantorSerializer, LoanApplicationSerializer
)
from ukombozini.apps.users.views import log_user_activity

class LoanListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LoanCreateSerializer
        return LoanSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Loan.objects.select_related('member', 'group', 'created_by')

        # Filter based on user type
        if user.user_type == 'admin':
            return queryset.all()
        elif user.user_type == 'field_officer':
            return queryset.filter(
                Q(group__field_officer=user) | Q(group__created_by=user)
            )
        else:
            # Members can only see their own loans
            return queryset.filter(member__user=user)

    def perform_create(self, serializer):
        loan = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Created {loan.get_loan_type_display()} application for {loan.member.get_full_name()}',
            request=self.request,
            content_type='loan',
            object_id=str(loan.id)
        )

class LoanDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'admin':
            return Loan.objects.all()
        elif user.user_type == 'field_officer':
            return Loan.objects.filter(
                Q(group__field_officer=user) | Q(group__created_by=user)
            )
        else:
            return Loan.objects.filter(member__user=user)

class LoanRepaymentListView(generics.ListCreateAPIView):
    serializer_class = LoanRepaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        loan_id = self.kwargs['loan_id']
        return LoanRepayment.objects.filter(loan_id=loan_id)

    def perform_create(self, serializer):
        repayment = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Recorded repayment of KES {repayment.amount_paid} for loan {repayment.loan.loan_number}',
            request=self.request,
            content_type='loan_repayment',
            object_id=str(repayment.id)
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_loan_id(request, loan_id):
    """Verify member ID for loan approval"""
    try:
        loan = Loan.objects.get(id=loan_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only admins and field officers can verify IDs'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = IDVerificationSerializer(data=request.data)
        if serializer.is_valid():
            verification = serializer.save(
                loan=loan,
                member=loan.member,
                verified_by=user,
                verified_at=timezone.now(),
                status='verified'
            )

            # Update loan verification status
            loan.id_verified = True
            loan.id_verification_method = verification.verification_method
            loan.id_verification_date = verification.verified_at
            loan.verified_by = user
            loan.save()

            # Log activity
            log_user_activity(
                user=user,
                action='update',
                description=f'Verified ID for loan {loan.loan_number}',
                request=request,
                content_type='loan',
                object_id=str(loan.id)
            )

            return Response({
                'message': 'ID verified successfully',
                'loan': LoanSerializer(loan).data
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def disburse_loan(request, loan_id):
    """Disburse an approved loan"""
    try:
        loan = Loan.objects.get(id=loan_id)

        # Check if loan can be disbursed
        if not loan.can_disburse():
            return Response(
                {'error': 'Loan cannot be disbursed. Check approval and verification status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update loan status
        loan.disbursement_date = date.today()
        loan.status = 'disbursed'
        loan.save()

        # Log activity
        log_user_activity(
            user=request.user,
            action='update',
            description=f'Disbursed loan {loan.loan_number} - KES {loan.principal_amount}',
            request=request,
            content_type='loan',
            object_id=str(loan.id)
        )

        return Response({
            'message': 'Loan disbursed successfully',
            'loan': LoanSerializer(loan).data
        })

    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def loan_statistics(request):
    """Get loan portfolio statistics"""
    user = request.user

    # Base queryset based on user type
    if user.user_type == 'admin':
        loans = Loan.objects.all()
    elif user.user_type == 'field_officer':
        loans = Loan.objects.filter(
            Q(group__field_officer=user) | Q(group__created_by=user)
        )
    else:
        loans = Loan.objects.filter(member__user=user)

    # Calculate statistics
    total_loans = loans.count()
    active_loans = loans.filter(status__in=['active', 'disbursed']).count()
    completed_loans = loans.filter(status='completed').count()
    defaulted_loans = loans.filter(status='defaulted').count()

    # Amount statistics
    total_portfolio = loans.aggregate(total=Sum('principal_amount'))['total'] or 0
    active_portfolio = loans.filter(status__in=['active', 'disbursed']).aggregate(
        total=Sum('current_balance')
    )['total'] or 0
    total_repaid = loans.aggregate(total=Sum('total_paid'))['total'] or 0

    # Loan type breakdown
    loan_type_breakdown = loans.values('loan_type').annotate(
        count=Count('id'),
        amount=Sum('principal_amount')
    )

    statistics = {
        'total_loans': total_loans,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'defaulted_loans': defaulted_loans,
        'total_portfolio': total_portfolio,
        'active_portfolio': active_portfolio,
        'total_repaid': total_repaid,
        'repayment_rate': (total_repaid / total_portfolio * 100) if total_portfolio > 0 else 0,
        'loan_type_breakdown': loan_type_breakdown,
    }

    return Response(statistics)

class LoanTopUpView(generics.ListCreateAPIView):
    serializer_class = LoanTopUpSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        loan_id = self.kwargs.get('loan_id')
        if loan_id:
            return LoanTopUp.objects.filter(original_loan_id=loan_id)
        return LoanTopUp.objects.all()

    def perform_create(self, serializer):
        top_up = serializer.save(created_by=self.request.user)

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Requested top-up of KES {top_up.top_up_amount} for loan {top_up.original_loan.loan_number}',
            request=self.request,
            content_type='loan_topup',
            object_id=str(top_up.id)
        )

class GuarantorListView(generics.ListCreateAPIView):
    serializer_class = GuarantorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        loan_id = self.kwargs.get('loan_id')
        if loan_id:
            return Guarantor.objects.filter(loan_id=loan_id).select_related('member', 'loan', 'approved_by')
        return Guarantor.objects.all().select_related('member', 'loan', 'approved_by')

    def perform_create(self, serializer):
        guarantor = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Added guarantor {guarantor.member.get_full_name()} for loan {guarantor.loan.loan_number}',
            request=self.request,
            content_type='guarantor',
            object_id=str(guarantor.id)
        )

class GuarantorDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GuarantorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Guarantor.objects.all().select_related('member', 'loan', 'approved_by')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_guarantors(request, loan_id):
    """Get list of available group members who can be guarantors"""
    try:
        loan = Loan.objects.get(id=loan_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only admins and field officers can view available guarantors'},
                status=status.HTTP_403_FORBIDDEN
            )

        available_guarantors = loan.get_available_guarantors()
        serializer = AvailableGuarantorSerializer(available_guarantors, many=True)

        return Response(serializer.data)

    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_guarantor(request, loan_id):
    """Add a guarantor to a loan"""
    try:
        loan = Loan.objects.get(id=loan_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only admins and field officers can add guarantors'},
                status=status.HTTP_403_FORBIDDEN
            )

        member_id = request.data.get('member_id')
        guarantee_amount = request.data.get('guarantee_amount')
        relationship = request.data.get('relationship', 'group_member')

        success, guarantor, message = loan.add_guarantor(
            member_id=member_id,
            guarantee_amount=guarantee_amount,
            relationship=relationship
        )

        if success:
            serializer = GuarantorSerializer(guarantor)
            return Response({
                'message': message,
                'guarantor': serializer.data
            })
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_guarantor(request, guarantor_id):
    """Approve or reject a guarantor"""
    try:
        guarantor = Guarantor.objects.get(id=guarantor_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only admins and field officers can approve guarantors'},
                status=status.HTTP_403_FORBIDDEN
            )

        action = request.data.get('action')  # 'approve' or 'reject'
        notes = request.data.get('notes', '')

        if action == 'approve':
            guarantor.status = 'approved'
            guarantor.approved_date = timezone.now()
            guarantor.approved_by = user
            guarantor.notes = notes
            guarantor.save()

            # Log activity
            log_user_activity(
                user=user,
                action='update',
                description=f'Approved guarantor {guarantor.member.get_full_name()} for loan {guarantor.loan.loan_number}',
                request=request,
                content_type='guarantor',
                object_id=str(guarantor.id)
            )

            return Response({
                'message': 'Guarantor approved successfully',
                'guarantor': GuarantorSerializer(guarantor).data
            })

        elif action == 'reject':
            rejection_reason = request.data.get('rejection_reason', 'Rejected by admin')
            guarantor.status = 'rejected'
            guarantor.rejection_reason = rejection_reason
            guarantor.notes = notes
            guarantor.save()

            # Log activity
            log_user_activity(
                user=user,
                action='update',
                description=f'Rejected guarantor {guarantor.member.get_full_name()} for loan {guarantor.loan.loan_number}',
                request=request,
                content_type='guarantor',
                object_id=str(guarantor.id)
            )

            return Response({
                'message': 'Guarantor rejected',
                'guarantor': GuarantorSerializer(guarantor).data
            })

        else:
            return Response(
                {'error': 'Invalid action. Use "approve" or "reject"'},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Guarantor.DoesNotExist:
        return Response(
            {'error': 'Guarantor not found'},
            status=status.HTTP_404_NOT_FOUND
        )

class LoanApplicationView(generics.ListCreateAPIView):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        loan_id = self.kwargs.get('loan_id')
        if loan_id:
            return LoanApplication.objects.filter(loan_id=loan_id)
        return LoanApplication.objects.all()

    def perform_create(self, serializer):
        application = serializer.save(applicant=self.request.user)

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Created loan application for {application.loan.loan_number}',
            request=self.request,
            content_type='loan_application',
            object_id=str(application.id)
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_loan_application(request, application_id):
    """Submit a loan application"""
    try:
        application = LoanApplication.objects.get(id=application_id)

        # Check permissions - only applicant can submit
        if application.applicant != request.user:
            return Response(
                {'error': 'Only the applicant can submit the application'},
                status=status.HTTP_403_FORBIDDEN
            )

        success, message = application.submit_application()

        if success:
            # Log activity
            log_user_activity(
                user=request.user,
                action='update',
                description=f'Submitted loan application for {application.loan.loan_number}',
                request=request,
                content_type='loan_application',
                object_id=str(application.id)
            )

            return Response({
                'message': message,
                'application': LoanApplicationSerializer(application).data
            })
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )

    except LoanApplication.DoesNotExist:
        return Response(
            {'error': 'Application not found'},
            status=status.HTTP_404_NOT_FOUND
        )
