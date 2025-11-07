from rest_framework import serializers
from django.utils import timezone
from .models import Member, NextOfKin, MemberDocument, MemberSavings, MemberActivity, CreditScoreHistory

class NextOfKinSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextOfKin
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class MemberDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberDocument
        fields = '__all__'
        read_only_fields = ['upload_date']

class MemberSavingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberSavings
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class MemberActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberActivity
        fields = '__all__'
        read_only_fields = ['activity_date']

class CreditScoreHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditScoreHistory
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    next_of_kin = NextOfKinSerializer(many=True, read_only=True)
    documents = MemberDocumentSerializer(many=True, read_only=True)
    recent_savings = MemberSavingsSerializer(many=True, read_only=True, source='savings_transactions')
    recent_activities = MemberActivitySerializer(many=True, read_only=True, source='activities')
    credit_history = CreditScoreHistorySerializer(many=True, read_only=True, source='credit_score_history')

    # Computed fields
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    financial_summary = serializers.SerializerMethodField()
    loan_performance = serializers.SerializerMethodField()
    loan_eligibility = serializers.SerializerMethodField()
    loan_limit = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id', 'member_number', 'user', 'group', 'first_name', 'last_name',
            'id_number', 'phone_number', 'email', 'date_of_birth', 'gender',
            'marital_status', 'education_level', 'occupation', 'employer',
            'monthly_income', 'address', 'city', 'county', 'postal_code',
            'date_joined', 'membership_status', 'membership_type',
            'id_document', 'id_verified', 'id_verification_date',
            'live_photo', 'biometric_data', 'biometric_verified',
            'total_savings', 'total_loans_taken', 'total_loans_repaid',
            'total_interest_paid', 'total_welfare_contributions',
            'total_fines_charges', 'current_month_savings',
            'current_month_welfare', 'current_month_fines',
            'credit_score', 'risk_category', 'savings_consistency',
            'loan_repayment_rate', 'member_since_months',
            'created_by', 'created_at', 'updated_at', 'last_activity',
            # Related data
            'next_of_kin', 'documents', 'recent_savings', 'recent_activities', 'credit_history',
            # Computed fields
            'full_name', 'age', 'financial_summary', 'loan_performance',
            'loan_eligibility', 'loan_limit'
        ]
        read_only_fields = [
            'member_number', 'credit_score', 'risk_category', 'member_since_months',
            'total_savings', 'total_loans_taken', 'total_loans_repaid',
            'total_interest_paid', 'total_welfare_contributions', 'total_fines_charges',
            'savings_consistency', 'loan_repayment_rate', 'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_age(self, obj):
        if obj.date_of_birth:
            today = timezone.now().date()
            return today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
        return None

    def get_financial_summary(self, obj):
        return obj.get_financial_summary()

    def get_loan_performance(self, obj):
        return obj.get_loan_performance()

    def get_loan_eligibility(self, obj):
        can_take, reason = obj.can_take_loan()
        return {
            'eligible': can_take,
            'reason': reason
        }

    def get_loan_limit(self, obj):
        return obj.get_loan_limit()

class MemberCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new members"""
    class Meta:
        model = Member
        fields = [
            'user', 'group', 'first_name', 'last_name', 'id_number',
            'phone_number', 'email', 'date_of_birth', 'gender',
            'marital_status', 'education_level', 'occupation', 'employer',
            'monthly_income', 'address', 'city', 'county', 'postal_code',
            'membership_type', 'id_document', 'live_photo'
        ]

    def create(self, validated_data):
        # Set created_by from request context
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user

        return super().create(validated_data)

class MemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating member information"""
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'phone_number', 'email', 'date_of_birth',
            'marital_status', 'education_level', 'occupation', 'employer',
            'monthly_income', 'address', 'city', 'county', 'postal_code',
            'membership_status', 'membership_type', 'id_document', 'live_photo'
        ]

class MemberFinancialSerializer(serializers.Serializer):
    """Serializer for financial operations"""
    member_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = serializers.ChoiceField(choices=[
        ('savings', 'Savings Deposit'),
        ('welfare', 'Welfare Contribution'),
        ('fine', 'Fine Payment'),
        ('withdrawal', 'Savings Withdrawal')
    ])
    payment_method = serializers.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check')
    ])
    description = serializers.CharField(max_length=500, required=False)
    receipt_number = serializers.CharField(max_length=100, required=False)

class MemberCreditScoreSerializer(serializers.Serializer):
    """Serializer for credit score operations"""
    member_id = serializers.IntegerField()
    recalculate = serializers.BooleanField(default=True)
    notes = serializers.CharField(max_length=500, required=False)

class MemberVerificationSerializer(serializers.Serializer):
    """Serializer for member verification operations"""
    member_id = serializers.IntegerField()
    verification_type = serializers.ChoiceField(choices=[
        ('id', 'ID Verification'),
        ('biometric', 'Biometric Verification'),
        ('document', 'Document Verification')
    ])
    verified = serializers.BooleanField()
    notes = serializers.CharField(max_length=500, required=False)
