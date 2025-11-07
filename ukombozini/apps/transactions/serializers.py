from rest_framework import serializers
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import CashInTransaction, CashOutTransaction, TransactionReconciliation, TransactionCategory

class CashInTransactionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    transaction_summary = serializers.SerializerMethodField()

    class Meta:
        model = CashInTransaction
        fields = [
            'id', 'transaction_id', 'group', 'group_name', 'transaction_date',
            'transaction_type', 'amount', 'payment_method', 'member', 'member_name',
            'loan', 'receipt_number', 'transaction_reference', 'mpesa_code',
            'description', 'notes', 'status', 'is_verified', 'verified_by',
            'verified_by_name', 'verified_date', 'rejection_reason',
            'supporting_document', 'recorded_by', 'recorded_by_name',
            'transaction_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'created_at', 'updated_at', 'transaction_summary'
        ]

    def get_transaction_summary(self, obj):
        return obj.get_transaction_summary()

    def validate(self, attrs):
        # Validate transaction date
        if attrs.get('transaction_date') > timezone.now().date():
            raise serializers.ValidationError({
                'transaction_date': 'Transaction date cannot be in the future'
            })

        # Validate member-specific transactions
        transaction_type = attrs.get('transaction_type')
        member = attrs.get('member')

        if transaction_type in ['savings', 'loan_repayment', 'welfare', 'fine'] and not member:
            raise serializers.ValidationError({
                'member': f'Member is required for {transaction_type} transactions'
            })

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['recorded_by'] = request.user
        return super().create(validated_data)

class CashOutTransactionSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    paid_by_name = serializers.CharField(source='paid_by.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    transaction_summary = serializers.SerializerMethodField()
    can_approve = serializers.SerializerMethodField()
    can_pay = serializers.SerializerMethodField()

    class Meta:
        model = CashOutTransaction
        fields = [
            'id', 'transaction_id', 'group', 'group_name', 'transaction_date',
            'transaction_type', 'amount', 'payment_method', 'payee_name',
            'payee_phone', 'payee_id_number', 'member', 'member_name', 'loan',
            'cheque_number', 'bank_name', 'bank_account', 'mpesa_code',
            'description', 'purpose', 'notes', 'status', 'requested_by',
            'requested_by_name', 'requested_date', 'approved_by', 'approved_by_name',
            'approved_date', 'approval_notes', 'paid_by', 'paid_by_name',
            'paid_date', 'rejection_reason', 'supporting_document', 'receipt_document',
            'created_by', 'created_by_name', 'transaction_summary', 'can_approve',
            'can_pay', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'requested_date', 'created_at', 'updated_at',
            'transaction_summary', 'can_approve', 'can_pay'
        ]

    def get_transaction_summary(self, obj):
        return obj.get_transaction_summary()

    def get_can_approve(self, obj):
        return obj.can_approve()

    def get_can_pay(self, obj):
        return obj.can_pay()

    def validate(self, attrs):
        # Validate transaction date
        if attrs.get('transaction_date') > timezone.now().date():
            raise serializers.ValidationError({
                'transaction_date': 'Transaction date cannot be in the future'
            })

        # Validate member-specific transactions
        transaction_type = attrs.get('transaction_type')
        member = attrs.get('member')

        if transaction_type in ['loan_disbursement', 'member_withdrawal', 'welfare_payout'] and not member:
            raise serializers.ValidationError({
                'member': f'Member is required for {transaction_type} transactions'
            })

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
            validated_data['requested_by'] = request.user

            # Auto-set status to pending approval for non-draft transactions
            if validated_data.get('status') == 'draft':
                validated_data['status'] = 'pending_approval'

        return super().create(validated_data)

class TransactionReconciliationSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    completed_by_name = serializers.CharField(source='completed_by.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = TransactionReconciliation
        fields = [
            'id', 'reconciliation_id', 'reconciliation_date', 'period_start',
            'period_end', 'group', 'group_name', 'opening_balance', 'total_cash_in',
            'total_cash_out', 'expected_balance', 'actual_balance', 'variance',
            'status', 'completed_by', 'completed_by_name', 'completed_date',
            'notes', 'variance_explanation', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reconciliation_id', 'expected_balance', 'variance',
            'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        # Validate period dates
        period_start = attrs.get('period_start')
        period_end = attrs.get('period_end')

        if period_start and period_end and period_start >= period_end:
            raise serializers.ValidationError({
                'period_end': 'Period end must be after period start'
            })

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class TransactionCategorySerializer(serializers.ModelSerializer):
    current_month_total = serializers.SerializerMethodField()
    budget_utilization = serializers.SerializerMethodField()

    class Meta:
        model = TransactionCategory
        fields = [
            'id', 'name', 'category_type', 'description', 'is_active',
            'has_budget', 'monthly_budget', 'current_month_total',
            'budget_utilization'
        ]

    def get_current_month_total(self, obj):
        return obj.get_current_month_total()

    def get_budget_utilization(self, obj):
        return obj.get_budget_utilization()

class FinancialSummarySerializer(serializers.Serializer):
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_cash_in = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cash_out = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_cash_flow = serializers.DecimalField(max_digits=12, decimal_places=2)
    opening_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    closing_balance = serializers.DecimalField(max_digits=12, decimal_places=2)

    cash_in_by_type = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))
    cash_out_by_type = serializers.DictField(child=serializers.DecimalField(max_digits=12, decimal_places=2))

    transaction_count = serializers.IntegerField()
    average_transaction_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
