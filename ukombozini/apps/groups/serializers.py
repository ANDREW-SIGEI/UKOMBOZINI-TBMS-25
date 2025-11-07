from rest_framework import serializers
from django.utils import timezone
from .models import Group, CashInTransaction, CashOutTransaction, TRFBalance, GroupMeeting, MeetingAttendance

class GroupSerializer(serializers.ModelSerializer):
    total_members = serializers.ReadOnlyField()
    total_savings = serializers.SerializerMethodField()
    total_loans = serializers.SerializerMethodField()
    cash_in_total = serializers.SerializerMethodField()
    cash_out_total = serializers.SerializerMethodField()
    current_balance = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'registration_number', 'description',
            'county', 'constituency', 'ward', 'location', 'village',
            'chairperson_name', 'chairperson_phone', 'chairperson_email',
            'secretary_name', 'treasurer_name',
            'formation_date', 'registration_date', 'total_members', 'status',
            'initial_capital', 'current_balance',
            'created_by', 'field_officer',
            'total_savings', 'total_loans', 'cash_in_total', 'cash_out_total'
        ]
        read_only_fields = ['id', 'registration_date', 'total_members', 'current_balance']

    def get_total_savings(self, obj):
        return obj.get_total_savings()

    def get_total_loans(self, obj):
        return obj.get_total_loans()

    def get_cash_in_total(self, obj):
        return obj.get_cash_in_total()

    def get_cash_out_total(self, obj):
        return obj.get_cash_out_total()

    def get_current_balance(self, obj):
        return obj.get_cash_in_total() - obj.get_cash_out_total()

class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'county', 'constituency', 'ward',
            'location', 'village', 'chairperson_name', 'chairperson_phone',
            'chairperson_email', 'secretary_name', 'treasurer_name',
            'formation_date', 'initial_capital', 'field_officer'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class CashInTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = CashInTransaction
        fields = [
            'id', 'group', 'transaction_type', 'transaction_type_display',
            'amount', 'description', 'transaction_date', 'receipt_number',
            'related_loan', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_transaction_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Transaction date cannot be in the future.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class CashOutTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = CashOutTransaction
        fields = [
            'id', 'group', 'transaction_type', 'transaction_type_display',
            'amount', 'description', 'transaction_date', 'voucher_number',
            'recipient_name', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_transaction_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Transaction date cannot be in the future.")
        return value

    def validate_amount(self, value):
        group = self.context.get('group')
        if group and value > group.current_balance:
            raise serializers.ValidationError("Cash out amount cannot exceed group balance.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class TRFBalanceSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = TRFBalance
        fields = [
            'id', 'group', 'balance_date', 'balance_account',
            'short_term_arrears', 'long_term_loans_balance',
            'total_assets', 'total_liabilities', 'net_worth',
            'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'net_worth', 'created_at', 'updated_at']

    def validate_balance_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Balance date cannot be in the future.")
        return value

class GroupMeetingSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    attendance_count = serializers.SerializerMethodField()

    class Meta:
        model = GroupMeeting
        fields = [
            'id', 'group', 'meeting_date', 'venue', 'agenda', 'minutes',
            'total_attendance', 'decisions_made', 'amount_collected',
            'is_completed', 'created_by', 'created_by_name', 'attendance_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_attendance_count(self, obj):
        return obj.attendance.count()

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class MeetingAttendanceSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    member_id_number = serializers.CharField(source='member.id_number', read_only=True)

    class Meta:
        model = MeetingAttendance
        fields = [
            'id', 'meeting', 'member', 'member_name', 'member_id_number',
            'attended', 'arrival_time', 'contribution_amount', 'comments'
        ]

class FinancialSummarySerializer(serializers.Serializer):
    """Serializer for group financial summary"""
    group = GroupSerializer(read_only=True)
    total_cash_in = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_cash_out = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)

    # Cash In Breakdown
    banking_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    short_term_loans_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    long_term_loans_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    savings_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    welfare_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    education_project_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    agriculture_project_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    ukombozini_loan_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    application_fee_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    appreciation_fee_total = serializers.DecimalField(max_digits=12, decimal_places=2)

    # TRF Balance
    trf_balance_account = serializers.DecimalField(max_digits=12, decimal_places=2)
    trf_short_term_arrears = serializers.DecimalField(max_digits=12, decimal_places=2)
    trf_long_term_loans_balance = serializers.DecimalField(max_digits=12, decimal_places=2)

class CashInSummarySerializer(serializers.Serializer):
    """Serializer for cash-in summary by type"""
    transaction_type = serializers.CharField()
    transaction_type_display = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
