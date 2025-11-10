from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Sum, Q
from django.utils import timezone
from .models import SavingsTransaction
from .serializers import SavingsTransactionSerializer, SavingsTransactionCreateSerializer
from ukombozini.apps.messaging.utils import send_savings_update_notification

class SavingsTransactionViewSet(viewsets.ModelViewSet):
    queryset = SavingsTransaction.objects.select_related('member', 'group', 'recorded_by')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['member', 'group', 'transaction_type', 'transaction_date']
    search_fields = ['member__first_name', 'member__last_name', 'reference', 'notes']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    ordering = ['-transaction_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SavingsTransactionCreateSerializer
        return SavingsTransactionSerializer

    def perform_create(self, serializer):
        transaction = serializer.save(recorded_by=self.request.user)

        # Send SMS notification to member about savings update
        try:
            from ukombozini.apps.members.models import Member
            member = Member.objects.get(user=transaction.member)
            send_savings_update_notification(member, transaction.amount, transaction.get_transaction_type_display())
        except Member.DoesNotExist:
            pass  # Skip if member profile doesn't exist

    @action(detail=False, methods=['get'])
    def member_summary(self, request):
        """Get savings summary for a specific member"""
        member_id = request.query_params.get('member_id')
        if not member_id:
            return Response(
                {'error': 'member_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transactions = self.get_queryset().filter(member_id=member_id)
        total_savings = transactions.aggregate(
            total=Sum('amount', filter=Q(transaction_type='saving'))
        )['total'] or 0

        total_contributions = transactions.aggregate(
            total=Sum('amount', filter=~Q(transaction_type='saving'))
        )['total'] or 0

        return Response({
            'member_id': member_id,
            'total_savings': total_savings,
            'total_contributions': total_contributions,
            'total_balance': total_savings + total_contributions,
            'transaction_count': transactions.count()
        })

    @action(detail=False, methods=['get'])
    def group_summary(self, request):
        """Get savings summary for a specific group"""
        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response(
                {'error': 'group_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transactions = self.get_queryset().filter(group_id=group_id)
        summary = transactions.values('transaction_type').annotate(
            total_amount=Sum('amount')
        ).order_by('transaction_type')

        total_balance = transactions.aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'group_id': group_id,
            'total_balance': total_balance,
            'transaction_count': transactions.count(),
            'breakdown_by_type': list(summary)
        })

    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        """Get monthly savings report"""
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month', timezone.now().month)

        start_date = timezone.datetime(int(year), int(month), 1).date()
        if int(month) == 12:
            end_date = timezone.datetime(int(year) + 1, 1, 1).date()
        else:
            end_date = timezone.datetime(int(year), int(month) + 1, 1).date()

        transactions = self.get_queryset().filter(
            transaction_date__gte=start_date,
            transaction_date__lt=end_date
        )

        summary = transactions.values('transaction_type').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('transaction_type')

        total_amount = transactions.aggregate(total=Sum('amount'))['total'] or 0

        return Response({
            'year': year,
            'month': month,
            'total_amount': total_amount,
            'transaction_count': transactions.count(),
            'breakdown_by_type': list(summary)
        })
