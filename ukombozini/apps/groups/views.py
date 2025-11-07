from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Group, CashInTransaction, CashOutTransaction, TRFBalance, GroupMeeting
from .serializers import (
    GroupSerializer, GroupCreateSerializer, CashInTransactionSerializer,
    CashOutTransactionSerializer, TRFBalanceSerializer, GroupMeetingSerializer,
    MeetingAttendanceSerializer, FinancialSummarySerializer, CashInSummarySerializer
)
from ukombozini.apps.users.views import log_user_activity

class GroupListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GroupCreateSerializer
        return GroupSerializer

    def get_queryset(self):
        user = self.request.user

        # Filter based on user type
        if user.user_type == 'admin':
            return Group.objects.all()
        elif user.user_type == 'field_officer':
            return Group.objects.filter(
                Q(field_officer=user) | Q(created_by=user)
            )
        else:
            # Group admins and members can only see their groups
            return Group.objects.filter(members__user=user).distinct()

    def perform_create(self, serializer):
        group = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Created new group: {group.name}',
            request=self.request,
            content_type='group',
            object_id=str(group.id)
        )

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type == 'admin':
            return Group.objects.all()
        elif user.user_type == 'field_officer':
            return Group.objects.filter(
                Q(field_officer=user) | Q(created_by=user)
            )
        else:
            return Group.objects.filter(members__user=user).distinct()

    def perform_update(self, serializer):
        group = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='update',
            description=f'Updated group: {group.name}',
            request=self.request,
            content_type='group',
            object_id=str(group.id)
        )

    def perform_destroy(self, instance):
        # Log activity
        log_user_activity(
            user=self.request.user,
            action='delete',
            description=f'Deleted group: {instance.name}',
            request=self.request,
            content_type='group',
            object_id=str(instance.id)
        )
        instance.delete()

class CashInTransactionListView(generics.ListCreateAPIView):
    serializer_class = CashInTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return CashInTransaction.objects.filter(group_id=group_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        transaction = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Added cash-in transaction: {transaction.get_transaction_type_display()} - {transaction.amount}',
            request=self.request,
            content_type='cash_in_transaction',
            object_id=str(transaction.id)
        )

class CashOutTransactionListView(generics.ListCreateAPIView):
    serializer_class = CashOutTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return CashOutTransaction.objects.filter(group_id=group_id)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        context['group'] = Group.objects.get(id=self.kwargs['group_id'])
        return context

    def perform_create(self, serializer):
        transaction = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Added cash-out transaction: {transaction.get_transaction_type_display()} - {transaction.amount}',
            request=self.request,
            content_type='cash_out_transaction',
            object_id=str(transaction.id)
        )

class TRFBalanceListView(generics.ListCreateAPIView):
    serializer_class = TRFBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return TRFBalance.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        balance = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Added TRF balance for {balance.balance_date}',
            request=self.request,
            content_type='trf_balance',
            object_id=str(balance.id)
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def financial_summary(request, group_id):
    """Get comprehensive financial summary for a group"""
    try:
        group = Group.objects.get(id=group_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            if not group.members.filter(user=user).exists():
                return Response(
                    {'error': 'You do not have permission to view this group\'s financials'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Calculate cash-in totals by type
        cash_in_totals = CashInTransaction.objects.filter(group=group).values(
            'transaction_type'
        ).annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        )

        # Create cash-in breakdown
        cash_in_breakdown = {}
        for item in cash_in_totals:
            cash_in_breakdown[f"{item['transaction_type']}_total"] = item['total_amount']

        # Calculate totals
        total_cash_in = CashInTransaction.objects.filter(group=group).aggregate(
            total=Sum('amount')
        )['total'] or 0

        total_cash_out = CashOutTransaction.objects.filter(group=group).aggregate(
            total=Sum('amount')
        )['total'] or 0

        current_balance = total_cash_in - total_cash_out

        # Get latest TRF balance
        latest_trf = TRFBalance.objects.filter(group=group).order_by('-balance_date').first()

        summary_data = {
            'group': group,
            'total_cash_in': total_cash_in,
            'total_cash_out': total_cash_out,
            'current_balance': current_balance,
            # Cash In Breakdown with defaults for missing types
            'banking_total': cash_in_breakdown.get('banking_total', 0),
            'short_term_loans_total': cash_in_breakdown.get('short_term_loans_total', 0),
            'long_term_loans_total': cash_in_breakdown.get('long_term_loans_total', 0),
            'savings_total': cash_in_breakdown.get('savings_total', 0),
            'welfare_total': cash_in_breakdown.get('welfare_total', 0),
            'education_project_total': cash_in_breakdown.get('education_project_total', 0),
            'agriculture_project_total': cash_in_breakdown.get('agriculture_project_total', 0),
            'ukombozini_loan_total': cash_in_breakdown.get('ukombozini_loan_total', 0),
            'application_fee_total': cash_in_breakdown.get('application_fee_total', 0),
            'appreciation_fee_total': cash_in_breakdown.get('appreciation_fee_total', 0),
            # TRF Balance
            'trf_balance_account': latest_trf.balance_account if latest_trf else 0,
            'trf_short_term_arrears': latest_trf.short_term_arrears if latest_trf else 0,
            'trf_long_term_loans_balance': latest_trf.long_term_loans_balance if latest_trf else 0,
        }

        serializer = FinancialSummarySerializer(summary_data)
        return Response(serializer.data)

    except Group.DoesNotExist:
        return Response(
            {'error': 'Group not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def cash_in_summary(request, group_id):
    """Get cash-in summary by transaction type"""
    try:
        group = Group.objects.get(id=group_id)

        # Check permissions
        user = request.user
        if user.user_type not in ['admin', 'field_officer']:
            if not group.members.filter(user=user).exists():
                return Response(
                    {'error': 'You do not have permission to view this group\'s financials'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Get cash-in totals by type with percentages
        cash_in_totals = CashInTransaction.objects.filter(group=group).values(
            'transaction_type'
        ).annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        )

        total_cash_in = sum(item['total_amount'] for item in cash_in_totals)

        summary_data = []
        for item in cash_in_totals:
            percentage = (item['total_amount'] / total_cash_in * 100) if total_cash_in > 0 else 0

            summary_data.append({
                'transaction_type': item['transaction_type'],
                'transaction_type_display': dict(CashInTransaction.TRANSACTION_TYPES).get(item['transaction_type'], 'Unknown'),
                'total_amount': item['total_amount'],
                'transaction_count': item['transaction_count'],
                'percentage': round(percentage, 2)
            })

        serializer = CashInSummarySerializer(summary_data, many=True)
        return Response(serializer.data)

    except Group.DoesNotExist:
        return Response(
            {'error': 'Group not found'},
            status=status.HTTP_404_NOT_FOUND
        )

class GroupMeetingListView(generics.ListCreateAPIView):
    serializer_class = GroupMeetingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return GroupMeeting.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        meeting = serializer.save()

        # Log activity
        log_user_activity(
            user=self.request.user,
            action='create',
            description=f'Scheduled meeting for {meeting.group.name} on {meeting.meeting_date}',
            request=self.request,
            content_type='group_meeting',
            object_id=str(meeting.id)
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def group_statistics(request):
    """Get overall group statistics"""
    user = request.user

    # Base queryset based on user type
    if user.user_type == 'admin':
        groups = Group.objects.all()
    elif user.user_type == 'field_officer':
        groups = Group.objects.filter(
            Q(field_officer=user) | Q(created_by=user)
        )
    else:
        groups = Group.objects.filter(members__user=user).distinct()

    total_groups = groups.count()
    active_groups = groups.filter(status='active').count()
    total_members = sum(group.total_members for group in groups)

    # Financial statistics
    total_savings = sum(group.get_total_savings() for group in groups)
    total_loans = sum(group.get_total_loans() for group in groups)

    statistics = {
        'total_groups': total_groups,
        'active_groups': active_groups,
        'inactive_groups': total_groups - active_groups,
        'total_members': total_members,
        'total_savings': total_savings,
        'total_loans': total_loans,
        'average_members_per_group': round(total_members / total_groups, 2) if total_groups > 0 else 0,
    }

    return Response(statistics)
