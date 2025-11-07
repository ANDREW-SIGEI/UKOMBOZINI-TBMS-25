from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import CashInTransaction, CashOutTransaction, TransactionReconciliation, TransactionCategory
from .serializers import (
    CashInTransactionSerializer, CashOutTransactionSerializer,
    TransactionReconciliationSerializer, TransactionCategorySerializer,
    FinancialSummarySerializer
)
from ukombozini.apps.users.views import log_user_activity

class CashInTransactionListView(generics.ListCreateAPIView):
    serializer_class = CashInTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = CashInTransaction.objects.select_related(
            'group', 'member', 'recorded_by', 'verified_by'
        )

        # Filter by group if provided
        group_id = self.request.query_params.get('group_id')
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(transaction_date__range=[start_date, end_date])

        # Filter based on user type
        if user.user_type == 'admin':
            return queryset.all()
        elif user.user_type == 'field_officer':
            return queryset.filter(
                Q(group__field_officer=user) | Q(group__created_by=user)
            )
        else:
            # Members can only see their own transactions
            return queryset.filter(member__user=user)

    def perform_create(self, serializer):
        transaction = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Recorded cash in transaction: {transaction.transaction_type} - KES {transaction.amount}',
            request=self.request,
            content_type='cash_in_transaction',
            object_id=str(transaction.id)
        )

class CashInTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CashInTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'admin':
            return CashInTransaction.objects.all()
        elif user.user_type == 'field_officer':
            return CashInTransaction.objects.filter(
                Q(group__field_officer=user) | Q(group__created_by=user)
            )
        else:
            return CashInTransaction.objects.filter(member__user=user)

class CashOutTransactionListView(generics.ListCreateAPIView):
    serializer_class = CashOutTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = CashOutTransaction.objects.select_related(
            'group', 'member', 'created_by', 'requested_by', 'approved_by', 'paid_by'
        )

        # Filter by group if provided
        group_id = self.request.query_params.get('group_id')
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(transaction_date__range=[start_date, end_date])

        # Filter based on user type
        if user.user_type == 'admin':
            return queryset.all()
        elif user.user_type == 'field_officer':
            return queryset.filter(
                Q(group__field_officer=user) | Q(group__created_by=user)
            )
        else:
            # Members can only see their own transactions
            return queryset.filter(member__user=user)

    def perform_create(self, serializer):
        transaction = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Created cash out request: {transaction.transaction_type} - KES {transaction.amount}',
            request=self.request,
            content_type='cash_out_transaction',
            object_id=str(transaction.id)
        )

class CashOutTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CashOutTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'admin':
            return CashOutTransaction.objects.all()
        elif user.user_type == 'field_officer':
            return CashOutTransaction.objects.filter(
                Q(group__field_officer=user) | Q(group__created_by=user)
            )
        else:
            return CashOutTransaction.objects.filter(member__user=user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_cash_out_transaction(request, transaction_id):
    """Approve a cash out transaction"""
    try:
        transaction = CashOutTransaction.objects.get(id=transaction_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only admins and field officers can approve transactions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if transaction can be approved
        if not transaction.can_approve():
            return Response(
                {'error': 'Transaction cannot be approved in its current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.status = 'approved'
        transaction.approved_by = user
        transaction.approved_date = timezone.now()
        transaction.approval_notes = request.data.get('approval_notes', '')
        transaction.save()

        # Log activity
        log_user_activity(
            user=user,
            action='update',
            description=f'Approved cash out transaction: {transaction.transaction_id} - KES {transaction.amount}',
            request=request,
            content_type='cash_out_transaction',
            object_id=str(transaction.id)
        )

        return Response({
            'message': 'Transaction approved successfully',
            'transaction': CashOutTransactionSerializer(transaction).data
        })

    except CashOutTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_cash_out_paid(request, transaction_id):
    """Mark a cash out transaction as paid"""
    try:
        transaction = CashOutTransaction.objects.get(id=transaction_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only admins and field officers can mark transactions as paid'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if transaction can be paid
        if not transaction.can_pay():
            return Response(
                {'error': 'Transaction cannot be paid in its current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.status = 'paid'
        transaction.paid_by = user
        transaction.paid_date = timezone.now()
        transaction.save()

        # Log activity
        log_user_activity(
            user=user,
            action='update',
            description=f'Marked cash out as paid: {transaction.transaction_id} - KES {transaction.amount}',
            request=request,
            content_type='cash_out_transaction',
            object_id=str(transaction.id)
        )

        return Response({
            'message': 'Transaction marked as paid successfully',
            'transaction': CashOutTransactionSerializer(transaction).data
        })

    except CashOutTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_cash_in_transaction(request, transaction_id):
    """Verify a cash in transaction"""
    try:
        transaction = CashInTransaction.objects.get(id=transaction_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            return Response(
                {'error': 'Only admins and field officers can verify transactions'},
                status=status.HTTP_403_FORBIDDEN
            )

        transaction.status = 'verified'
        transaction.is_verified = True
        transaction.verified_by = user
        transaction.verified_date = timezone.now()
        transaction.save()

        # Log activity
        log_user_activity(
            user=user,
            action='update',
            description=f'Verified cash in transaction: {transaction.transaction_id} - KES {transaction.amount}',
            request=request,
            content_type='cash_in_transaction',
            object_id=str(transaction.id)
        )

        return Response({
            'message': 'Transaction verified successfully',
            'transaction': CashInTransactionSerializer(transaction).data
        })

    except CashInTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def financial_summary(request, group_id):
    """Get financial summary for a group"""
    try:
        # Get date range from query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            # Default to current month
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today

        # Calculate totals
        cash_in_total = CashInTransaction.objects.filter(
            group_id=group_id,
            transaction_date__range=[start_date, end_date],
            status='verified'
        ).aggregate(total=Sum('amount'))['total'] or 0

        cash_out_total = CashOutTransaction.objects.filter(
            group_id=group_id,
            transaction_date__range=[start_date, end_date],
            status='paid'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Calculate by transaction type
        cash_in_by_type = CashInTransaction.objects.filter(
            group_id=group_id,
            transaction_date__range=[start_date, end_date],
            status='verified'
        ).values('transaction_type').annotate(total=Sum('amount'))

        cash_out_by_type = CashOutTransaction.objects.filter(
            group_id=group_id,
            transaction_date__range=[start_date, end_date],
            status='paid'
        ).values('transaction_type').annotate(total=Sum('amount'))

        # Convert to dictionaries
        cash_in_dict = {item['transaction_type']: item['total'] for item in cash_in_by_type}
        cash_out_dict = {item['transaction_type']: item['total'] for item in cash_out_by_type}

        # Get transaction count
        transaction_count = (
            CashInTransaction.objects.filter(
                group_id=group_id,
                transaction_date__range=[start_date, end_date],
                status='verified'
            ).count() +
            CashOutTransaction.objects.filter(
                group_id=group_id,
                transaction_date__range=[start_date, end_date],
                status='paid'
            ).count()
        )

        # Calculate average transaction amount
        total_transactions = cash_in_total + cash_out_total
        average_amount = total_transactions / transaction_count if transaction_count > 0 else 0

        summary = {
            'period_start': start_date,
            'period_end': end_date,
            'total_cash_in': cash_in_total,
            'total_cash_out': cash_out_total,
            'net_cash_flow': cash_in_total - cash_out_total,
            'opening_balance': 0,  # This would need to be calculated based on previous periods
            'closing_balance': 0,  # This would need to be calculated
            'cash_in_by_type': cash_in_dict,
            'cash_out_by_type': cash_out_dict,
            'transaction_count': transaction_count,
            'average_transaction_amount': average_amount,
        }

        serializer = FinancialSummarySerializer(summary)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

class TransactionReconciliationView(generics.ListCreateAPIView):
    serializer_class = TransactionReconciliationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = TransactionReconciliation.objects.select_related('group', 'created_by', 'completed_by')

        # Filter by group if provided
        group_id = self.request.query_params.get('group_id')
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        # Filter based on user type
        if user.user_type == 'admin':
            return queryset.all()
        elif user.user_type == 'field_officer':
            return queryset.filter(
                Q(group__field_officer=user) | Q(group__created_by=user)
            )
        else:
            return queryset.none()  # Members cannot see reconciliations

    def perform_create(self, serializer):
        reconciliation = serializer.save()

        # Calculate totals for the reconciliation period
        reconciliation.calculate_totals()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Created reconciliation: {reconciliation.period_start} to {reconciliation.period_end}',
            request=self.request,
            content_type='transaction_reconciliation',
            object_id=str(reconciliation.id)
        )

class TransactionCategoryView(generics.ListAPIView):
    serializer_class = TransactionCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TransactionCategory.objects.filter(is_active=True)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_statistics(request):
    """Get dashboard statistics for transactions"""
    user = request.user

    # Base queryset based on user type
    if user.user_type == 'admin':
        cash_in_qs = CashInTransaction.objects.all()
        cash_out_qs = CashOutTransaction.objects.all()
    elif user.user_type == 'field_officer':
        cash_in_qs = CashInTransaction.objects.filter(
            Q(group__field_officer=user) | Q(group__created_by=user)
        )
        cash_out_qs = CashOutTransaction.objects.filter(
            Q(group__field_officer=user) | Q(group__created_by=user)
        )
    else:
        cash_in_qs = CashInTransaction.objects.filter(member__user=user)
        cash_out_qs = CashOutTransaction.objects.filter(member__user=user)

    # Current month totals
    today = date.today()
    first_day = today.replace(day=1)

    monthly_cash_in = cash_in_qs.filter(
        transaction_date__range=[first_day, today],
        status='verified'
    ).aggregate(total=Sum('amount'))['total'] or 0

    monthly_cash_out = cash_out_qs.filter(
        transaction_date__range=[first_day, today],
        status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Pending approvals
    pending_approvals = cash_out_qs.filter(status='pending_approval').count()

    # Recent transactions
    recent_transactions = list(
        cash_in_qs.filter(status='verified').order_by('-transaction_date')[:5]
    ) + list(
        cash_out_qs.filter(status='paid').order_by('-transaction_date')[:5]
    )
    recent_transactions.sort(key=lambda x: x.transaction_date, reverse=True)

    statistics = {
        'monthly_cash_in': monthly_cash_in,
        'monthly_cash_out': monthly_cash_out,
        'monthly_net_flow': monthly_cash_in - monthly_cash_out,
        'pending_approvals': pending_approvals,
        'total_transactions_this_month': (
            cash_in_qs.filter(transaction_date__range=[first_day, today]).count() +
            cash_out_qs.filter(transaction_date__range=[first_day, today]).count()
        ),
        'recent_transactions': [
            {
                'id': t.id,
                'type': 'cash_in' if isinstance(t, CashInTransaction) else 'cash_out',
                'transaction_id': t.transaction_id,
                'amount': t.amount,
                'date': t.transaction_date,
                'description': getattr(t, 'description', '') or getattr(t, 'purpose', '')
            }
            for t in recent_transactions[:10]  # Limit to 10 most recent
        ]
    }

    return Response(statistics)
