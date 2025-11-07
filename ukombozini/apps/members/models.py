from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from decimal import Decimal
import uuid
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

class Member(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    MARITAL_STATUS = (
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    )

    EDUCATION_LEVEL = (
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('diploma', 'Diploma'),
        ('degree', 'Bachelor Degree'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    )

    # Basic Information
    member_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    user = models.OneToOneField('users.CustomUser', on_delete=models.CASCADE, related_name='member_profile')
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='members')

    # Personal Details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{6,8}$',
                message='ID number must be 6-8 digits'
            )
        ]
    )
    phone_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex='^\+?1?\d{9,15}$',
                message='Phone number must be entered in the format: +254712345678'
            )
        ]
    )
    email = models.EmailField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS, blank=True, null=True)
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL, blank=True, null=True)

    # Occupation Details
    occupation = models.CharField(max_length=100)
    employer = models.CharField(max_length=100, blank=True, null=True)
    monthly_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Contact Information
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    county = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)

    # Membership Details
    date_joined = models.DateField(default=date.today)
    membership_status = models.CharField(
        max_length=20,
        choices=(
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('suspended', 'Suspended'),
            ('terminated', 'Terminated'),
        ),
        default='active'
    )
    membership_type = models.CharField(
        max_length=20,
        choices=(
            ('regular', 'Regular Member'),
            ('premium', 'Premium Member'),
            ('founder', 'Founder Member'),
        ),
        default='regular'
    )

    # ID Verification
    id_document = models.FileField(upload_to='member_ids/', blank=True, null=True)
    id_verified = models.BooleanField(default=False)
    id_verification_date = models.DateTimeField(blank=True, null=True)
    live_photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)

    # Biometric Data (Encrypted)
    biometric_data = models.BinaryField(blank=True, null=True)  # Store fingerprint template
    biometric_verified = models.BooleanField(default=False)

    # Financial Tracking (Denormalized for performance)
    total_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_loans_taken = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_loans_repaid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_interest_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_welfare_contributions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_fines_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Current Month Tracking
    current_month_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_month_welfare = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_month_fines = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Credit Scoring
    credit_score = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)  # 0-100 scale
    risk_category = models.CharField(
        max_length=20,
        choices=(
            ('low', 'Low Risk'),
            ('medium', 'Medium Risk'),
            ('high', 'High Risk'),
            ('very_high', 'Very High Risk'),
        ),
        default='medium'
    )

    # Member Performance
    savings_consistency = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    loan_repayment_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    member_since_months = models.PositiveIntegerField(default=0)

    # Audit Fields
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_members')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Member'
        verbose_name_plural = 'Members'
        ordering = ['-date_joined', 'first_name']
        indexes = [
            models.Index(fields=['member_number']),
            models.Index(fields=['id_number']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['group', 'membership_status']),
            models.Index(fields=['credit_score']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} - {self.member_number}"

    def save(self, *args, **kwargs):
        # Generate member number if not set
        if not self.member_number:
            self.member_number = f"M{uuid.uuid4().hex[:8].upper()}"

        # Calculate member since months
        if self.date_joined:
            today = date.today()
            months = (today.year - self.date_joined.year) * 12 + (today.month - self.date_joined.month)
            self.member_since_months = max(0, months)

        # Update risk category based on credit score
        self.update_risk_category()

        # Update last activity
        self.last_activity = timezone.now()

        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def update_risk_category(self):
        """Update risk category based on credit score"""
        if self.credit_score >= 80:
            self.risk_category = 'low'
        elif self.credit_score >= 60:
            self.risk_category = 'medium'
        elif self.credit_score >= 40:
            self.risk_category = 'high'
        else:
            self.risk_category = 'very_high'

    def calculate_credit_score(self):
        """Calculate comprehensive credit score"""
        score = 50.0  # Base score

        # Savings consistency (30% weight)
        if self.member_since_months > 0:
            savings_consistency = min(100, (self.savings_consistency or 0))
            score += savings_consistency * 0.3

        # Loan repayment rate (40% weight)
        repayment_rate = min(100, (self.loan_repayment_rate or 0))
        score += repayment_rate * 0.4

        # Membership duration (10% weight)
        if self.member_since_months >= 24:
            score += 10
        elif self.member_since_months >= 12:
            score += 7
        elif self.member_since_months >= 6:
            score += 5

        # Financial behavior (20% weight)
        if self.total_fines_charges == 0:
            score += 10
        elif self.total_fines_charges < 1000:
            score += 5

        # Cap at 100
        self.credit_score = min(100, max(0, score))
        self.update_risk_category()
        return self.credit_score

    def get_total_savings(self):
        """Get total savings including all components"""
        return (
            self.total_savings +
            self.total_welfare_contributions -
            self.total_fines_charges
        )

    def get_financial_summary(self):
        """Get comprehensive financial summary"""
        return {
            'total_savings': self.total_savings,
            'total_loans_taken': self.total_loans_taken,
            'total_loans_repaid': self.total_loans_repaid,
            'total_interest_paid': self.total_interest_paid,
            'total_welfare': self.total_welfare_contributions,
            'total_fines': self.total_fines_charges,
            'net_savings': self.get_total_savings(),
            'current_month_savings': self.current_month_savings,
            'current_month_welfare': self.current_month_welfare,
            'current_month_fines': self.current_month_fines,
        }

    def get_loan_performance(self):
        """Get loan performance metrics"""
        if self.total_loans_taken > 0:
            repayment_rate = (self.total_loans_repaid / self.total_loans_taken) * 100
        else:
            repayment_rate = 100

        return {
            'total_loans_taken': self.total_loans_taken,
            'total_loans_repaid': self.total_loans_repaid,
            'outstanding_balance': self.total_loans_taken - self.total_loans_repaid,
            'repayment_rate': repayment_rate,
            'total_interest_paid': self.total_interest_paid,
        }

    def can_take_loan(self):
        """Check if member is eligible for a new loan"""
        # Check membership status
        if self.membership_status != 'active':
            return False, "Member is not active"

        # Check minimum membership duration (3 months)
        if self.member_since_months < 3:
            return False, "Minimum 3 months membership required"

        # Check credit score
        if self.credit_score < 40:
            return False, "Credit score too low"

        # Check savings consistency
        if self.savings_consistency < 50:
            return False, "Poor savings consistency"

        return True, "Eligible for loan"

    def get_loan_limit(self):
        """Calculate maximum loan amount based on savings and performance"""
        base_multiplier = 3  # Base 3x savings

        # Adjust multiplier based on credit score
        if self.credit_score >= 80:
            base_multiplier = 5
        elif self.credit_score >= 60:
            base_multiplier = 4
        elif self.credit_score >= 40:
            base_multiplier = 3
        else:
            base_multiplier = 2

        max_loan = self.total_savings * base_multiplier

        # Cap based on monthly income (6 months income)
        income_cap = self.monthly_income * 6
        max_loan = min(max_loan, income_cap)

        return max_loan

class NextOfKin(models.Model):
    RELATIONSHIP_CHOICES = (
        ('spouse', 'Spouse'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('relative', 'Relative'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    )

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='next_of_kin')

    # Next of Kin Details
    full_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    id_number = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Emergency Contact Priority
    is_primary_contact = models.BooleanField(default=False)
    contact_priority = models.PositiveIntegerField(default=1)  # 1 = highest priority

    # Verification
    id_document = models.FileField(upload_to='next_of_kin_ids/', blank=True, null=True)
    verified = models.BooleanField(default=False)

    # Additional Information
    occupation = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Next of Kin'
        verbose_name_plural = 'Next of Kin'
        ordering = ['contact_priority', 'full_name']
        unique_together = ['member', 'phone_number']

    def __str__(self):
        return f"{self.full_name} ({self.get_relationship_display()}) - {self.member.get_full_name()}"

class MemberDocument(models.Model):
    DOCUMENT_TYPES = (
        ('id_card', 'National ID Card'),
        ('passport', 'Passport'),
        ('kra_pin', 'KRA PIN Certificate'),
        ('passport_photo', 'Passport Photo'),
        ('proof_of_income', 'Proof of Income'),
        ('bank_statement', 'Bank Statement'),
        ('utility_bill', 'Utility Bill'),
        ('other', 'Other Document'),
    )

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='documents')

    # Document Details
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_name = models.CharField(max_length=100)
    document_file = models.FileField(upload_to='member_documents/')

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, blank=True, null=True)
    verified_date = models.DateTimeField(blank=True, null=True)

    # Metadata
    upload_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Member Document'
        verbose_name_plural = 'Member Documents'
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.document_name} - {self.member.get_full_name()}"

class MemberSavings(models.Model):
    SAVINGS_TYPES = (
        ('regular', 'Regular Savings'),
        ('welfare', 'Welfare Contribution'),
        ('emergency', 'Emergency Fund'),
        ('investment', 'Investment Savings'),
        ('fine', 'Fine Payment'),
        ('other', 'Other'),
    )

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='savings_transactions')

    # Transaction Details
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    savings_type = models.CharField(max_length=20, choices=SAVINGS_TYPES, default='regular')

    # Payment Method
    payment_method = models.CharField(
        max_length=20,
        choices=(
            ('cash', 'Cash'),
            ('mpesa', 'M-Pesa'),
            ('bank', 'Bank Transfer'),
            ('check', 'Check'),
            ('adjustment', 'Adjustment'),
        ),
        default='cash'
    )

    # References
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)

    # Description
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, blank=True, null=True)

    # Audit
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='recorded_savings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Member Savings Transaction'
        verbose_name_plural = 'Member Savings Transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['member', 'transaction_date']),
            models.Index(fields=['savings_type']),
        ]

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.get_savings_type_display()} - KES {self.amount}"

    def save(self, *args, **kwargs):
        # Update member's total savings when verified
        if self.is_verified and not self._state.adding:
            self.update_member_savings()

        super().save(*args, **kwargs)

    def update_member_savings(self):
        """Update member's savings totals"""
        member = self.member

        # Update based on savings type
        if self.savings_type == 'regular':
            member.total_savings += self.amount
            member.current_month_savings += self.amount
        elif self.savings_type == 'welfare':
            member.total_welfare_contributions += self.amount
            member.current_month_welfare += self.amount
        elif self.savings_type == 'fine':
            member.total_fines_charges += self.amount
            member.current_month_fines += self.amount

        member.save()

class MemberActivity(models.Model):
    ACTIVITY_TYPES = (
        ('savings_deposit', 'Savings Deposit'),
        ('loan_application', 'Loan Application'),
        ('loan_repayment', 'Loan Repayment'),
        ('profile_update', 'Profile Update'),
        ('document_upload', 'Document Upload'),
        ('meeting_attendance', 'Meeting Attendance'),
        ('status_change', 'Status Change'),
        ('other', 'Other Activity'),
    )

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='activities')

    # Activity Details
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    activity_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    # Related Objects
    related_loan = models.ForeignKey('loans.Loan', on_delete=models.SET_NULL, blank=True, null=True)
    related_savings = models.ForeignKey(MemberSavings, on_delete=models.SET_NULL, blank=True, null=True)

    # IP and Location
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # Performed by
    performed_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Member Activity'
        verbose_name_plural = 'Member Activities'
        ordering = ['-activity_date']
        indexes = [
            models.Index(fields=['member', 'activity_date']),
            models.Index(fields=['activity_type']),
        ]

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.get_activity_type_display()} - {self.activity_date}"

class CreditScoreHistory(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='credit_score_history')

    # Score Details
    score_date = models.DateField(default=date.today)
    credit_score = models.DecimalField(max_digits=5, decimal_places=2)
    risk_category = models.CharField(max_length=20)

    # Factors affecting score
    savings_consistency = models.DecimalField(max_digits=5, decimal_places=2)
    loan_repayment_rate = models.DecimalField(max_digits=5, decimal_places=2)
    membership_duration_months = models.PositiveIntegerField()
    total_fines = models.DecimalField(max_digits=12, decimal_places=2)

    # Change information
    score_change = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    change_reason = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Credit Score History'
        verbose_name_plural = 'Credit Score History'
        ordering = ['-score_date']
        unique_together = ['member', 'score_date']

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.credit_score} - {self.score_date}"
