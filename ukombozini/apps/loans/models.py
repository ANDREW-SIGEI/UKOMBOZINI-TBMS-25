from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from ukombozini.apps.sync.models import SyncableModel

class Loan(SyncableModel):
    LOAN_TYPES = (
        ('short_term', 'Short Term Loan (3 months)'),
        ('long_term', 'Long Term Loan (2 years)'),
        ('project', 'Project Loan'),
        ('top_up', 'Top-Up Loan'),
    )

    LOAN_STATUS = (
        ('draft', 'Draft'),
        ('applied', 'Applied'),
        ('pending_verification', 'Pending ID Verification'),
        ('approved', 'Approved'),
        ('disbursed', 'Disbursed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
        ('rejected', 'Rejected'),
    )

    # Basic Information
    loan_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='loans')
    member = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='loans')

    # Loan Amount Details
    principal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Principal Amount"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.0,  # 10% interest for all loans
        verbose_name="Interest Rate (%)"
    )
    total_repayable = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Total Repayable"
    )

    # Loan Terms
    application_date = models.DateField(auto_now_add=True)
    approval_date = models.DateField(blank=True, null=True)
    disbursement_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)

    # For short-term loans: 3 months
    short_term_months = models.PositiveIntegerField(default=3, verbose_name="Loan Period (months)")

    # For long-term loans: 2 years (24 months)
    long_term_months = models.PositiveIntegerField(default=24, verbose_name="Loan Period (months)")

    # For project loans
    project_description = models.TextField(blank=True, null=True, verbose_name="Project Description")
    project_product = models.CharField(max_length=255, blank=True, null=True, verbose_name="Project Product")

    # ID Verification
    id_verified = models.BooleanField(default=False, verbose_name="ID Verified")
    id_verification_method = models.CharField(
        max_length=20,
        choices=(
            ('upload', 'ID Upload'),
            ('camera', 'Live Camera'),
            ('manual', 'Manual Verification'),
        ),
        blank=True,
        null=True,
        verbose_name="Verification Method"
    )
    id_verification_date = models.DateTimeField(blank=True, null=True)
    id_document = models.FileField(
        upload_to='loan_verifications/',
        blank=True,
        null=True,
        verbose_name="ID Document"
    )

    # Repayment Tracking
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    arrears_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    days_in_arrears = models.PositiveIntegerField(default=0)

    # Status
    status = models.CharField(max_length=25, choices=LOAN_STATUS, default='draft')
    is_active = models.BooleanField(default=True)

    # Top-up loan relation
    original_loan = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='top_up_loans'
    )
    top_up_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Top-up Amount"
    )

    # Audit fields
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    verified_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='verified_loans'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Loan'
        verbose_name_plural = 'Loans'
        ordering = ['-application_date']
        indexes = [
            models.Index(fields=['loan_type', 'status']),
            models.Index(fields=['group', 'member']),
            models.Index(fields=['due_date']),
            models.Index(fields=['id_verified']),
        ]

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.get_loan_type_display()} - KES {self.principal_amount}"

    def save(self, *args, **kwargs):
        # Generate loan number if not set
        if not self.loan_number:
            self.loan_number = f"LN{uuid.uuid4().hex[:8].upper()}"

        # Calculate total repayable based on loan type
        self.calculate_repayment()

        # Set due date based on loan type
        self.set_due_date()

        # Update current balance
        self.current_balance = self.total_repayable - self.total_paid

        # Calculate arrears
        self.calculate_arrears()

        # Auto-set status based on verification and dates
        self.update_status()

        super().save(*args, **kwargs)

    def calculate_repayment(self):
        """Calculate total repayable amount based on loan type and interest"""
        if self.loan_type == 'short_term':
            # Simple interest for 3 months
            monthly_interest = (self.interest_rate / 100) / 12
            interest_amount = self.principal_amount * monthly_interest * self.short_term_months
            self.total_repayable = self.principal_amount + interest_amount

        elif self.loan_type in ['long_term', 'project', 'top_up']:
            # Reducing balance for longer terms
            months = self.long_term_months if self.loan_type == 'long_term' else 24
            monthly_rate = (self.interest_rate / 100) / 12
            if monthly_rate > 0:
                self.total_repayable = self.principal_amount * (1 + monthly_rate) ** months
            else:
                self.total_repayable = self.principal_amount

    def set_due_date(self):
        """Set due date based on loan type"""
        if self.disbursement_date:
            if self.loan_type == 'short_term':
                self.due_date = self.disbursement_date + relativedelta(months=self.short_term_months)
            else:
                months = self.long_term_months if self.loan_type == 'long_term' else 24
                self.due_date = self.disbursement_date + relativedelta(months=months)

    def calculate_arrears(self):
        """Calculate arrears amount and days"""
        if self.due_date and date.today() > self.due_date and self.current_balance > 0:
            days_overdue = (date.today() - self.due_date).days
            self.days_in_arrears = days_overdue

            # Calculate arrears amount (could be more sophisticated)
            if self.loan_type == 'short_term':
                monthly_payment = self.total_repayable / self.short_term_months
                overdue_months = max(1, days_overdue // 30)
                self.arrears_amount = monthly_payment * overdue_months
            else:
                months = self.long_term_months if self.loan_type == 'long_term' else 24
                monthly_payment = self.total_repayable / months
                overdue_months = max(1, days_overdue // 30)
                self.arrears_amount = monthly_payment * overdue_months
        else:
            self.days_in_arrears = 0
            self.arrears_amount = 0

    def update_status(self):
        """Update loan status based on current conditions"""
        if self.status == 'draft' and self.principal_amount > 0:
            self.status = 'applied'

        if self.status == 'applied' and not self.id_verified:
            self.status = 'pending_verification'

        if self.id_verified and self.status == 'pending_verification':
            self.status = 'approved'

        if self.disbursement_date and self.status == 'approved':
            self.status = 'disbursed'

        if self.status == 'disbursed' and self.current_balance > 0:
            self.status = 'active'

        if self.current_balance <= 0 and self.principal_amount > 0:
            self.status = 'completed'
            self.is_active = False

        if self.days_in_arrears > 90:  # 3 months in arrears
            self.status = 'defaulted'

    def get_monthly_repayment(self):
        """Calculate monthly repayment amount"""
        if self.loan_type == 'short_term':
            return self.total_repayable / self.short_term_months
        else:
            months = self.long_term_months if self.loan_type == 'long_term' else 24
            return self.total_repayable / months

    def get_repayment_schedule(self):
        """Generate repayment schedule"""
        schedule = []
        if self.disbursement_date:
            monthly_payment = self.get_monthly_repayment()
            balance = self.total_repayable

            months = self.short_term_months if self.loan_type == 'short_term' else self.long_term_months

            for i in range(months):
                due_date = self.disbursement_date + relativedelta(months=i+1)
                interest = balance * (self.interest_rate / 100) / 12
                principal = monthly_payment - interest
                balance -= monthly_payment

                schedule.append({
                    'installment_number': i + 1,
                    'due_date': due_date,
                    'amount_due': monthly_payment,
                    'principal': principal,
                    'interest': interest,
                    'remaining_balance': max(0, balance)
                })

        return schedule

    def get_available_guarantors(self):
        """Get list of available group members who can be guarantors"""
        from ukombozini.apps.users.models import CustomUser

        # Get all group members except the borrower
        # Since there's no separate Member model, we use CustomUser with user_type='member'
        # and assume they are linked to groups through some relationship
        # For now, we'll get all users in the same county/constituency/ward as proxy
        group_members = CustomUser.objects.filter(
            user_type='member',
            assigned_county=self.group.county,
            assigned_constituency=self.group.constituency,
            assigned_ward=self.group.ward
        ).exclude(id=self.member.id)

        available_guarantors = []
        for member in group_members:
            # Check if member is already a guarantor
            existing_guarantee = self.guarantors.filter(member=member).exists()

            if not existing_guarantee:
                # Check guarantee eligibility
                temp_guarantor = Guarantor(loan=self, member=member, guarantee_amount=self.principal_amount * Decimal('0.2'))
                can_guarantee, reason = temp_guarantor.can_be_guarantor()

                available_guarantors.append({
                    'id': member.id,
                    'full_name': member.get_full_name(),
                    'id_number': member.id_number,
                    'phone_number': member.phone_number,
                    'total_savings': member.get_total_savings() if hasattr(member, 'get_total_savings') else 0,
                    'can_guarantee': can_guarantee,
                    'reason': reason,
                    'existing_guarantees': Guarantor.objects.filter(
                        member=member,
                        status='approved',
                        loan__status__in=['active', 'disbursed', 'approved']
                    ).count()
                })

        return available_guarantors

    def add_guarantor(self, member_id, guarantee_amount=None, relationship='group_member'):
        """Add a guarantor to the loan"""
        from ukombozini.apps.users.models import CustomUser

        try:
            member = CustomUser.objects.get(id=member_id, user_type='member')

            if guarantee_amount is None:
                guarantee_amount = self.principal_amount * Decimal('0.2')  # Default 20%

            guarantor = Guarantor.objects.create(
                loan=self,
                member=member,
                guarantee_amount=guarantee_amount,
                relationship=relationship
            )

            return True, guarantor, "Guarantor added successfully"

        except CustomUser.DoesNotExist:
            return False, None, "Member not found"

    @property
    def guarantee_summary(self):
        """Get guarantee summary for the loan"""
        approved_guarantors = self.guarantors.filter(status='approved')
        pending_guarantors = self.guarantors.filter(status='pending')

        # Get application details if exists, otherwise use defaults
        application = getattr(self, 'application', None)
        required_guarantors = getattr(application, 'required_guarantors', 1) if application else 1
        min_coverage_percentage = getattr(application, 'min_guarantee_percentage', 20) if application else 20

        return {
            'total_guarantors': self.guarantors.count(),
            'approved_guarantors': approved_guarantors.count(),
            'pending_guarantors': pending_guarantors.count(),
            'total_guarantee_amount': sum(g.guarantee_amount for g in approved_guarantors),
            'guarantee_coverage_percentage': self.guarantee_coverage_percentage,
            'required_guarantors': required_guarantors,
            'min_coverage_percentage': min_coverage_percentage,
        }

    @property
    def guarantee_coverage_percentage(self):
        """Calculate guarantee coverage percentage"""
        approved_guarantors = self.guarantors.filter(status='approved')
        total_guarantee = sum(g.guarantee_amount for g in approved_guarantors)

        if self.principal_amount > 0:
            return (total_guarantee / self.principal_amount) * 100
        return 0

    def can_disburse(self):
        """Check if loan can be disbursed"""
        return (self.status == 'approved' and
                self.id_verified and
                not self.disbursement_date and
                self.principal_amount > 0)

class LoanRepayment(SyncableModel):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('adjustment', 'Adjustment'),
    )

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    repayment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)

    # For arrears payments
    arrears_cleared = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, blank=True, null=True)
    verification_date = models.DateTimeField(blank=True, null=True)

    # Notes
    notes = models.TextField(blank=True, null=True)

    # Audit
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='created_loanrepayments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Loan Repayment'
        verbose_name_plural = 'Loan Repayments'
        ordering = ['-repayment_date', '-created_at']
        indexes = [
            models.Index(fields=['loan', 'repayment_date']),
            models.Index(fields=['receipt_number']),
        ]

    def __str__(self):
        return f"{self.loan.loan_number} - KES {self.amount_paid} - {self.repayment_date}"

    def save(self, *args, **kwargs):
        # Auto-calculate principal and interest if not set
        if not self.principal_amount and not self.interest_amount:
            self.calculate_breakdown()

        # Update loan totals
        if self.is_verified and not self._state.adding:
            self.update_loan_totals()

        super().save(*args, **kwargs)

    def calculate_breakdown(self):
        """Calculate principal and interest breakdown"""
        # Simple calculation - in practice, this would use amortization
        interest_rate = self.loan.interest_rate / 100 / 12
        total_interest = self.loan.total_repayable - self.loan.principal_amount

        if total_interest > 0:
            interest_ratio = total_interest / self.loan.total_repayable
            self.interest_amount = self.amount_paid * interest_ratio
            self.principal_amount = self.amount_paid - self.interest_amount
        else:
            self.principal_amount = self.amount_paid
            self.interest_amount = Decimal('0.00')

    def update_loan_totals(self):
        """Update loan totals after repayment"""
        self.loan.total_paid += self.amount_paid
        self.loan.current_balance = max(0, self.loan.total_repayable - self.loan.total_paid)
        self.loan.save()

class IDVerification(models.Model):
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )

    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='id_verification')
    member = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='id_verifications')

    # Verification details
    verification_method = models.CharField(
        max_length=20,
        choices=(
            ('upload', 'ID Document Upload'),
            ('camera', 'Live Camera Capture'),
            ('manual', 'Manual Verification'),
        )
    )
    id_number = models.CharField(max_length=20, verbose_name="ID Number")
    id_type = models.CharField(
        max_length=20,
        choices=(
            ('national_id', 'National ID'),
            ('passport', 'Passport'),
            ('driving_license', 'Driving License'),
        ),
        default='national_id'
    )

    # Document/files
    id_front_image = models.ImageField(upload_to='id_verifications/front/', blank=True, null=True)
    id_back_image = models.ImageField(upload_to='id_verifications/back/', blank=True, null=True)
    live_photo = models.ImageField(upload_to='id_verifications/live/', blank=True, null=True)

    # Verification data
    verification_data = models.JSONField(blank=True, null=True)  # Store facial recognition data, etc.
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Confidence Score")

    # Status
    status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verified_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    # Verification by
    verified_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ID Verification'
        verbose_name_plural = 'ID Verifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Set expiry date (e.g., 30 days from creation)
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(days=30) if self.created_at else None

        # Update loan verification status
        if self.status == 'verified' and self.verified_at:
            self.loan.id_verified = True
            self.loan.id_verification_method = self.verification_method
            self.loan.id_verification_date = self.verified_at
            self.loan.verified_by = self.verified_by
            self.loan.save()

        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if verification is still valid"""
        if self.status != 'verified':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            self.status = 'expired'
            self.save()
            return False
        return True

class Guarantor(models.Model):
    GUARANTOR_STATUS = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )

    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='guarantors')
    member = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='guaranteed_loans')

    # Guarantee details
    guarantee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Guarantee Amount"
    )
    guarantee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Guarantee Percentage"
    )

    # Status and approval
    status = models.CharField(max_length=20, choices=GUARANTOR_STATUS, default='pending')
    approved_date = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_guarantors'
    )

    # Relationship with borrower
    relationship = models.CharField(
        max_length=50,
        choices=(
            ('group_member', 'Group Member'),
            ('family', 'Family Member'),
            ('friend', 'Friend'),
            ('business_partner', 'Business Partner'),
            ('other', 'Other'),
        ),
        default='group_member'
    )

    # Notes
    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Guarantor'
        verbose_name_plural = 'Guarantors'
        unique_together = ['loan', 'member']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member.get_full_name()} - {self.loan.loan_number} - KES {self.guarantee_amount}"

    def save(self, *args, **kwargs):
        # Auto-calculate guarantee percentage if not set
        if self.guarantee_amount and self.loan.principal_amount > 0 and not self.guarantee_percentage:
            self.guarantee_percentage = (Decimal(str(self.guarantee_amount)) / self.loan.principal_amount) * 100

        super().save(*args, **kwargs)

    def can_be_guarantor(self):
        """Check if member can be a guarantor"""
        # Check if member is not the borrower
        if self.member == self.loan.member:
            return False, "Cannot guarantee your own loan"

        # Check active guarantees
        active_guarantees = Guarantor.objects.filter(
            member=self.member,
            status='approved',
            loan__status__in=['active', 'disbursed', 'approved']
        ).exclude(loan=self.loan)

        total_active_guarantee = sum(g.guarantee_amount for g in active_guarantees)

        # Check if member has exceeded guarantee limit (e.g., 50% of their savings)
        try:
            member_savings = self.member.get_total_savings() if hasattr(self.member, 'get_total_savings') else 0
            guarantee_limit = member_savings * Decimal('0.5')  # 50% of savings

            if total_active_guarantee + self.guarantee_amount > guarantee_limit:
                return False, f"Guarantee limit exceeded. Available: KES {guarantee_limit - total_active_guarantee:,.2f}"
        except:
            pass

        return True, "Eligible"


class LoanApplication(models.Model):
    """Enhanced loan application with guarantors"""

    APPLICATION_STATUS = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('pending_guarantors', 'Pending Guarantor Approval'),
        ('pending_verification', 'Pending ID Verification'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    loan = models.OneToOneField('Loan', on_delete=models.CASCADE, related_name='application')
    applicant = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='loan_applications')
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='loan_applications')

    # Application details
    application_date = models.DateTimeField(auto_now_add=True)
    submitted_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=25, choices=APPLICATION_STATUS, default='draft')

    # Business details for project loans
    business_plan = models.FileField(upload_to='business_plans/', blank=True, null=True)
    project_description = models.TextField(blank=True, null=True)
    expected_returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Guarantor requirements
    required_guarantors = models.PositiveIntegerField(default=1, verbose_name="Required Guarantors")
    min_guarantee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,  # Minimum 20% guarantee coverage
        verbose_name="Minimum Guarantee Coverage %"
    )

    # Review information
    reviewed_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, blank=True, null=True)
    reviewed_date = models.DateTimeField(blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)

    # Rejection information
    rejection_reason = models.TextField(blank=True, null=True)
    rejected_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='rejected_applications'
    )

    class Meta:
        verbose_name = 'Loan Application'
        verbose_name_plural = 'Loan Applications'
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.applicant.get_full_name()} - {self.loan.loan_number}"

    @property
    def total_guarantee_amount(self):
        """Calculate total guarantee amount from approved guarantors"""
        approved_guarantors = self.loan.guarantors.filter(status='approved')
        return sum(g.guarantee_amount for g in approved_guarantors)

    @property
    def guarantee_coverage_percentage(self):
        """Calculate guarantee coverage percentage"""
        if self.loan.principal_amount > 0:
            return (self.total_guarantee_amount / self.loan.principal_amount) * 100
        return 0

    @property
    def has_sufficient_guarantors(self):
        """Check if application has sufficient guarantors"""
        approved_count = self.loan.guarantors.filter(status='approved').count()
        return approved_count >= self.required_guarantors

    @property
    def has_sufficient_guarantee_coverage(self):
        """Check if guarantee coverage meets minimum requirement"""
        return self.guarantee_coverage_percentage >= self.min_guarantee_percentage

    def can_submit(self):
        """Check if application can be submitted"""
        errors = []

        # Check guarantors
        if not self.has_sufficient_guarantors:
            errors.append(f"Requires {self.required_guarantors} guarantors")

        if not self.has_sufficient_guarantee_coverage:
            errors.append(f"Requires {self.min_guarantee_percentage}% guarantee coverage")

        return len(errors) == 0, errors

    def submit_application(self):
        """Submit the loan application"""
        can_submit, errors = self.can_submit()

        if can_submit:
            self.status = 'submitted'
            self.submitted_date = timezone.now()
            self.save()
            return True, "Application submitted successfully"
        else:
            return False, errors


class LoanTopUp(models.Model):
    original_loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='top_ups')
    top_up_loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='top_up_request')

    top_up_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reason = models.TextField(verbose_name="Top-up Reason")
    approval_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        default='pending'
    )

    # Requirements
    requires_new_verification = models.BooleanField(default=False)
    previous_repayment_performance = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Repayment Performance %")

    # Audit
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    approved_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_top_ups')
    approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Loan Top-Up'
        verbose_name_plural = 'Loan Top-Ups'
        ordering = ['-created_at']

    def __str__(self):
        return f"Top-up for {self.original_loan.loan_number} - KES {self.top_up_amount}"

    def calculate_repayment_performance(self):
        """Calculate repayment performance of original loan"""
        total_expected = self.original_loan.total_paid + self.original_loan.current_balance
        if total_expected > 0:
            self.previous_repayment_performance = (self.original_loan.total_paid / total_expected) * 100
        return self.previous_repayment_performance
