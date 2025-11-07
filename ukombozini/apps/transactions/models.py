from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

class CashInTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('savings', 'Member Savings'),
        ('loan_repayment', 'Loan Repayment'),
        ('welfare', 'Welfare Contribution'),
        ('fine', 'Fine Payment'),
        ('membership_fee', 'Membership Fee'),
        ('donation', 'Donation'),
        ('investment', 'Investment Income'),
        ('other_income', 'Other Income'),
    )

    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('mobile_banking', 'Mobile Banking'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('reversed', 'Reversed'),
    )

    # Basic Information
    transaction_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='transactions_cash_in_transactions')

    # Transaction Details
    transaction_date = models.DateField(default=date.today)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')

    # Member Association (if applicable)
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_in_transactions'
    )

    # Loan Association (if applicable)
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_in_transactions'
    )

    # Payment References
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="M-Pesa Code")

    # Description
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Verification & Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_cash_in_transactions'
    )
    verified_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Supporting Documents
    supporting_document = models.FileField(
        upload_to='cash_in_documents/',
        blank=True,
        null=True,
        verbose_name="Supporting Document"
    )

    # Audit Fields
    recorded_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_cash_in_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cash In Transaction'
        verbose_name_plural = 'Cash In Transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['group', 'transaction_date']),
            models.Index(fields=['member', 'transaction_date']),
        ]

    def __str__(self):
        return f"Cash In - {self.get_transaction_type_display()} - KES {self.amount} - {self.transaction_date}"

    def save(self, *args, **kwargs):
        # Generate transaction ID if not set
        if not self.transaction_id:
            self.transaction_id = f"CI{uuid.uuid4().hex[:8].upper()}"

        # Auto-set verification status
        if self.status == 'verified':
            self.is_verified = True
            if not self.verified_date:
                self.verified_date = timezone.now()
        else:
            self.is_verified = False

        super().save(*args, **kwargs)

    def clean(self):
        """Validate transaction data"""
        if self.transaction_date > date.today():
            raise ValidationError({'transaction_date': 'Transaction date cannot be in the future'})

        if self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be greater than zero'})

        # Validate member-specific transactions
        if self.transaction_type in ['savings', 'loan_repayment', 'welfare', 'fine'] and not self.member:
            raise ValidationError({
                'member': f'Member is required for {self.get_transaction_type_display()} transactions'
            })

    def get_transaction_summary(self):
        """Get comprehensive transaction summary"""
        return {
            'transaction_id': self.transaction_id,
            'type': self.get_transaction_type_display(),
            'amount': self.amount,
            'date': self.transaction_date,
            'status': self.get_status_display(),
            'member': self.member.get_full_name() if self.member else 'N/A',
            'payment_method': self.get_payment_method_display(),
            'verified': self.is_verified,
        }

class CashOutTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('loan_disbursement', 'Loan Disbursement'),
        ('member_withdrawal', 'Member Savings Withdrawal'),
        ('operational_expense', 'Operational Expense'),
        ('welfare_payout', 'Welfare Payout'),
        ('supplier_payment', 'Supplier Payment'),
        ('staff_salary', 'Staff Salary'),
        ('utility_bill', 'Utility Bill'),
        ('other_expense', 'Other Expense'),
    )

    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('mobile_banking', 'Mobile Banking'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('reversed', 'Reversed'),
    )

    # Basic Information
    transaction_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='transactions_cash_out_transactions')

    # Transaction Details
    transaction_date = models.DateField(default=date.today)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')

    # Recipient Information
    payee_name = models.CharField(max_length=200)
    payee_phone = models.CharField(max_length=15, blank=True, null=True)
    payee_id_number = models.CharField(max_length=20, blank=True, null=True)

    # Member Association (if applicable)
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_out_transactions'
    )

    # Loan Association (if applicable)
    loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_out_transactions'
    )

    # Payment Details
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account = models.CharField(max_length=50, blank=True, null=True)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="M-Pesa Code")

    # Description
    description = models.TextField()
    purpose = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    # Approval Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    requested_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='requested_cash_out_transactions'
    )
    requested_date = models.DateTimeField(auto_now_add=True)

    approved_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_cash_out_transactions'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True)

    paid_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paid_cash_out_transactions'
    )
    paid_date = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(blank=True, null=True)

    # Supporting Documents
    supporting_document = models.FileField(
        upload_to='cash_out_documents/',
        blank=True,
        null=True,
        verbose_name="Supporting Document"
    )
    receipt_document = models.FileField(
        upload_to='cash_out_receipts/',
        blank=True,
        null=True,
        verbose_name="Receipt Document"
    )

    # Audit Fields
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cash_out_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cash Out Transaction'
        verbose_name_plural = 'Cash Out Transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['group', 'transaction_date']),
            models.Index(fields=['member', 'transaction_date']),
        ]

    def __str__(self):
        return f"Cash Out - {self.get_transaction_type_display()} - KES {self.amount} - {self.transaction_date}"

    def save(self, *args, **kwargs):
        # Generate transaction ID if not set
        if not self.transaction_id:
            self.transaction_id = f"CO{uuid.uuid4().hex[:8].upper()}"

        # Auto-set requested date for new pending transactions
        if self.status == 'pending_approval' and not self.requested_date:
            self.requested_date = timezone.now()

        super().save(*args, **kwargs)

    def clean(self):
        """Validate transaction data"""
        if self.transaction_date > date.today():
            raise ValidationError({'transaction_date': 'Transaction date cannot be in the future'})

        if self.amount <= 0:
            raise ValidationError({'amount': 'Amount must be greater than zero'})

        # Validate member-specific transactions
        if self.transaction_type in ['loan_disbursement', 'member_withdrawal', 'welfare_payout'] and not self.member:
            raise ValidationError({
                'member': f'Member is required for {self.get_transaction_type_display()} transactions'
            })

    def can_approve(self):
        """Check if transaction can be approved"""
        return self.status in ['draft', 'pending_approval']

    def can_pay(self):
        """Check if transaction can be paid"""
        return self.status == 'approved'

    def get_transaction_summary(self):
        """Get comprehensive transaction summary"""
        return {
            'transaction_id': self.transaction_id,
            'type': self.get_transaction_type_display(),
            'amount': self.amount,
            'date': self.transaction_date,
            'status': self.get_status_display(),
            'payee': self.payee_name,
            'member': self.member.get_full_name() if self.member else 'N/A',
            'payment_method': self.get_payment_method_display(),
        }

class TransactionReconciliation(models.Model):
    RECONCILIATION_STATUS = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('disputed', 'Disputed'),
    )

    # Reconciliation Information
    reconciliation_id = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    reconciliation_date = models.DateField(default=date.today)
    period_start = models.DateField()
    period_end = models.DateField()
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='transactions_reconciliations')

    # Financial Summary
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cash_in = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cash_out = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status
    status = models.CharField(max_length=20, choices=RECONCILIATION_STATUS, default='pending')
    completed_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions_completed_reconciliations'
    )
    completed_date = models.DateTimeField(null=True, blank=True)

    # Notes
    notes = models.TextField(blank=True, null=True)
    variance_explanation = models.TextField(blank=True, null=True)

    # Audit
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions_created_reconciliations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transaction Reconciliation'
        verbose_name_plural = 'Transaction Reconciliations'
        ordering = ['-reconciliation_date']
        unique_together = ['group', 'period_start', 'period_end']

    def __str__(self):
        return f"Reconciliation {self.reconciliation_id} - {self.period_start} to {self.period_end}"

    def save(self, *args, **kwargs):
        # Generate reconciliation ID if not set
        if not self.reconciliation_id:
            self.reconciliation_id = f"REC{uuid.uuid4().hex[:8].upper()}"

        # Calculate expected balance and variance
        self.expected_balance = self.opening_balance + self.total_cash_in - self.total_cash_out
        self.variance = self.actual_balance - self.expected_balance

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate transaction totals for the period"""
        cash_in_total = CashInTransaction.objects.filter(
            group=self.group,
            transaction_date__range=[self.period_start, self.period_end],
            status='verified'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        cash_out_total = CashOutTransaction.objects.filter(
            group=self.group,
            transaction_date__range=[self.period_start, self.period_end],
            status='paid'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        self.total_cash_in = cash_in_total
        self.total_cash_out = cash_out_total
        self.save()

class TransactionCategory(models.Model):
    CATEGORY_TYPES = (
        ('income', 'Income Category'),
        ('expense', 'Expense Category'),
    )

    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # Budgeting
    has_budget = models.BooleanField(default=False)
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Transaction Category'
        verbose_name_plural = 'Transaction Categories'
        ordering = ['category_type', 'name']
        unique_together = ['name', 'category_type']

    def __str__(self):
        return f"{self.get_category_type_display()} - {self.name}"

    def get_current_month_total(self):
        """Get total transactions for current month"""
        today = date.today()
        first_day = today.replace(day=1)

        if self.category_type == 'income':
            return CashInTransaction.objects.filter(
                transaction_type=self.name,
                transaction_date__range=[first_day, today],
                status='verified'
            ).aggregate(total=models.Sum('amount'))['total'] or 0
        else:
            return CashOutTransaction.objects.filter(
                transaction_type=self.name,
                transaction_date__range=[first_day, today],
                status='paid'
            ).aggregate(total=models.Sum('amount'))['total'] or 0

    def get_budget_utilization(self):
        """Calculate budget utilization percentage"""
        if self.has_budget and self.monthly_budget > 0:
            current_total = self.get_current_month_total()
            return (current_total / self.monthly_budget) * 100
        return 0
