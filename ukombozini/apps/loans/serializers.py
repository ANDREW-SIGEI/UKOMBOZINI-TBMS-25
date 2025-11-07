from rest_framework import serializers
from django.utils import timezone
from .models import Loan, LoanRepayment, IDVerification, LoanTopUp, Guarantor, LoanApplication

class LoanSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    monthly_repayment = serializers.SerializerMethodField()
    repayment_schedule = serializers.SerializerMethodField()
    can_disburse = serializers.SerializerMethodField()
    guarantee_summary = serializers.SerializerMethodField()
    guarantors = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            'id', 'loan_number', 'loan_type', 'group', 'group_name', 'member', 'member_name',
            'principal_amount', 'interest_rate', 'total_repayable', 'total_paid', 'current_balance',
            'application_date', 'approval_date', 'disbursement_date', 'due_date',
            'short_term_months', 'long_term_months', 'project_description', 'project_product',
            'id_verified', 'id_verification_method', 'id_verification_date', 'id_document',
            'arrears_amount', 'days_in_arrears', 'status', 'is_active',
            'original_loan', 'top_up_amount', 'monthly_repayment', 'repayment_schedule',
            'can_disburse', 'guarantee_summary', 'guarantors', 'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'loan_number', 'total_repayable', 'current_balance', 'created_at',
            'updated_at', 'monthly_repayment', 'repayment_schedule', 'can_disburse'
        ]

    def get_monthly_repayment(self, obj):
        return obj.get_monthly_repayment()

    def get_repayment_schedule(self, obj):
        return obj.get_repayment_schedule()

    def get_can_disburse(self, obj):
        return obj.can_disburse()

    def get_guarantee_summary(self, obj):
        return obj.guarantee_summary

    def get_guarantors(self, obj):
        guarantors = obj.guarantors.select_related('member').all()
        return GuarantorSerializer(guarantors, many=True).data

    def validate(self, attrs):
        # Validate ID verification for loan approval
        if self.instance and self.instance.status in ['approved', 'disbursed']:
            if not self.instance.id_verified:
                raise serializers.ValidationError({
                    'id_verified': 'Loan cannot be approved without ID verification'
                })

        # Validate loan amounts based on type
        loan_type = attrs.get('loan_type', getattr(self.instance, 'loan_type', None))
        principal_amount = attrs.get('principal_amount', getattr(self.instance, 'principal_amount', 0))

        if loan_type == 'short_term' and principal_amount > 50000:
            raise serializers.ValidationError({
                'principal_amount': 'Short-term loans cannot exceed KES 50,000'
            })

        if loan_type == 'top_up':
            original_loan = attrs.get('original_loan', getattr(self.instance, 'original_loan', None))
            if not original_loan:
                raise serializers.ValidationError({
                    'original_loan': 'Top-up loans require an original loan reference'
                })

        return attrs

class LoanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = [
            'loan_type', 'group', 'member', 'principal_amount', 'interest_rate',
            'short_term_months', 'long_term_months', 'project_description', 'project_product',
            'original_loan', 'top_up_amount'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class LoanRepaymentSerializer(serializers.ModelSerializer):
    loan_number = serializers.CharField(source='loan.loan_number', read_only=True)
    member_name = serializers.CharField(source='loan.member.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = LoanRepayment
        fields = [
            'id', 'loan', 'loan_number', 'member_name', 'repayment_date', 'amount_paid',
            'principal_amount', 'interest_amount', 'payment_method', 'receipt_number',
            'transaction_reference', 'arrears_cleared', 'penalty_amount', 'is_verified',
            'verified_by', 'verification_date', 'notes', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_repayment_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Repayment date cannot be in the future")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class IDVerificationSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    loan_number = serializers.CharField(source='loan.loan_number', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)

    class Meta:
        model = IDVerification
        fields = [
            'id', 'loan', 'loan_number', 'member', 'member_name', 'verification_method',
            'id_number', 'id_type', 'id_front_image', 'id_back_image', 'live_photo',
            'verification_data', 'confidence_score', 'status', 'verified_at', 'expires_at',
            'verified_by', 'verified_by_name', 'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'verified_at', 'expires_at']

    def validate(self, attrs):
        # Validate that verification is for the correct member
        loan = attrs.get('loan')
        member = attrs.get('member')

        if loan and member and loan.member != member:
            raise serializers.ValidationError({
                'member': 'Verification member must match loan member'
            })

        return attrs

class LoanTopUpSerializer(serializers.ModelSerializer):
    original_loan_number = serializers.CharField(source='original_loan.loan_number', read_only=True)
    member_name = serializers.CharField(source='original_loan.member.get_full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = LoanTopUp
        fields = [
            'id', 'original_loan', 'original_loan_number', 'top_up_loan', 'top_up_amount',
            'reason', 'approval_status', 'requires_new_verification', 'previous_repayment_performance',
            'member_name', 'created_by', 'created_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'approved_at', 'previous_repayment_performance'
        ]

    def validate(self, attrs):
        original_loan = attrs.get('original_loan')

        if original_loan and original_loan.status not in ['active', 'disbursed']:
            raise serializers.ValidationError({
                'original_loan': 'Only active or disbursed loans can receive top-ups'
            })

        # Calculate repayment performance
        if original_loan:
            top_up = LoanTopUp(original_loan=original_loan)
            performance = top_up.calculate_repayment_performance()
            if performance < 50:  # Less than 50% repayment performance
                raise serializers.ValidationError({
                    'original_loan': 'Loan must have at least 50% repayment performance for top-up'
                })

        return attrs

class GuarantorSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    loan_number = serializers.CharField(source='loan.loan_number', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    can_be_guarantor = serializers.SerializerMethodField()
    member_savings = serializers.SerializerMethodField()

    class Meta:
        model = Guarantor
        fields = [
            'id', 'loan', 'loan_number', 'member', 'member_name', 'guarantee_amount',
            'guarantee_percentage', 'status', 'approved_date', 'approved_by', 'approved_by_name',
            'relationship', 'notes', 'rejection_reason', 'can_be_guarantor', 'member_savings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'guarantee_percentage', 'created_at', 'updated_at']

    def get_can_be_guarantor(self, obj):
        can_guarantee, reason = obj.can_be_guarantor()
        return {'eligible': can_guarantee, 'reason': reason}

    def get_member_savings(self, obj):
        try:
            return obj.member.get_total_savings()
        except:
            return 0

class AvailableGuarantorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    id_number = serializers.CharField()
    phone_number = serializers.CharField()
    total_savings = serializers.DecimalField(max_digits=12, decimal_places=2)
    can_guarantee = serializers.BooleanField()
    reason = serializers.CharField()
    existing_guarantees = serializers.IntegerField()

class LoanApplicationSerializer(serializers.ModelSerializer):
    loan_number = serializers.CharField(source='loan.loan_number', read_only=True)
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    rejected_by_name = serializers.CharField(source='rejected_by.get_full_name', read_only=True)

    # Computed fields
    total_guarantee_amount = serializers.SerializerMethodField()
    guarantee_coverage_percentage = serializers.SerializerMethodField()
    has_sufficient_guarantors = serializers.SerializerMethodField()
    has_sufficient_guarantee_coverage = serializers.SerializerMethodField()
    can_submit = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            'id', 'loan', 'loan_number', 'applicant', 'applicant_name', 'group', 'group_name',
            'application_date', 'submitted_date', 'status', 'project_description', 'business_plan',
            'expected_returns', 'required_guarantors', 'min_guarantee_percentage',
            'reviewed_by', 'reviewed_by_name', 'reviewed_date', 'review_notes',
            'rejection_reason', 'rejected_by', 'rejected_by_name',
            'total_guarantee_amount', 'guarantee_coverage_percentage',
            'has_sufficient_guarantors', 'has_sufficient_guarantee_coverage', 'can_submit'
        ]
        read_only_fields = [
            'id', 'application_date', 'submitted_date', 'total_guarantee_amount',
            'guarantee_coverage_percentage', 'has_sufficient_guarantors',
            'has_sufficient_guarantee_coverage', 'can_submit'
        ]

    def get_total_guarantee_amount(self, obj):
        return obj.total_guarantee_amount

    def get_guarantee_coverage_percentage(self, obj):
        return obj.guarantee_coverage_percentage

    def get_has_sufficient_guarantors(self, obj):
        return obj.has_sufficient_guarantors

    def get_has_sufficient_guarantee_coverage(self, obj):
        return obj.has_sufficient_guarantee_coverage

    def get_can_submit(self, obj):
        can_submit, errors = obj.can_submit()
        return {'can_submit': can_submit, 'errors': errors}
