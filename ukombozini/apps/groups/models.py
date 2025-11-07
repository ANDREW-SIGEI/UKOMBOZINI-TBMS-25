from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Group(models.Model):
    GROUP_STATUS = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    )

    # Basic Information
    name = models.CharField(max_length=255, unique=True, verbose_name="Group Name")
    registration_number = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Registration Number")
    description = models.TextField(blank=True, null=True, verbose_name="Group Description")

    # Geographical Information
    county = models.CharField(max_length=100, verbose_name="County")
    constituency = models.CharField(max_length=100, verbose_name="Constituency")
    ward = models.CharField(max_length=100, verbose_name="Ward")
    location = models.CharField(max_length=100, verbose_name="Location")
    village = models.CharField(max_length=100, verbose_name="Village")

    # Leadership Information
    chairperson_name = models.CharField(max_length=255, verbose_name="Chairperson Name")
    chairperson_phone = models.CharField(max_length=15, verbose_name="Chairperson Phone")
    chairperson_email = models.EmailField(blank=True, null=True, verbose_name="Chairperson Email")
    secretary_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Secretary Name")
    treasurer_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Treasurer Name")

    # Contact Information
    contact_person = models.CharField(max_length=255, default="Chairperson", verbose_name="Contact Person")
    contact_phone = models.CharField(max_length=15, verbose_name="Contact Phone")
    contact_email = models.EmailField(blank=True, null=True, verbose_name="Contact Email")

    # Group Details
    formation_date = models.DateField(verbose_name="Formation Date")
    registration_date = models.DateField(auto_now_add=True, verbose_name="Registration Date")
    total_members = models.PositiveIntegerField(default=0, verbose_name="Total Members")
    status = models.CharField(max_length=20, choices=GROUP_STATUS, default='active', verbose_name="Status")

    # Financial Information
    initial_capital = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Initial Capital"
    )
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Current Balance"
    )

    # Management
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        verbose_name="Created By"
    )
    field_officer = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_groups',
        limit_choices_to={'user_type': 'field_officer'},
        verbose_name="Field Officer"
    )

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        ordering = ['name']
        indexes = [
            models.Index(fields=['county', 'constituency']),
            models.Index(fields=['status']),
            models.Index(fields=['registration_date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.county}"

    def save(self, *args, **kwargs):
        # Set contact information to chairperson if not specified
        if not self.contact_person:
            self.contact_person = self.chairperson_name
        if not self.contact_phone:
            self.contact_phone = self.chairperson_phone
        if not self.contact_email and self.chairperson_email:
            self.contact_email = self.chairperson_email

        # Save first to ensure we have a primary key
        super().save(*args, **kwargs)

        # Update total members count and current balance after save
        if self.pk:
            # Since there's no separate Member model, count CustomUser with user_type='member'
            # in the same county/constituency/ward as proxy for group members
            from ukombozini.apps.users.models import CustomUser
            self.total_members = CustomUser.objects.filter(
                user_type='member',
                assigned_county=self.county,
                assigned_constituency=self.constituency,
                assigned_ward=self.ward
            ).count()
            self.current_balance = self.get_cash_in_total() - self.get_cash_out_total()
            # Save again to update the calculated fields
            super().save(update_fields=['total_members', 'current_balance'])

    def get_total_savings(self):
        """Calculate total savings for the group"""
        from django.db.models import Sum
        result = self.cash_in_transactions.filter(transaction_type='savings').aggregate(
            total=Sum('amount')
        )
        return result['total'] or 0

    def get_total_loans(self):
        """Calculate total active loans"""
        from django.db.models import Sum
        result = self.loans.filter(status__in=['active', 'disbursed']).aggregate(
            total=Sum('principal_amount')
        )
        return result['total'] or 0

    def get_cash_in_total(self):
        """Calculate total cash in"""
        from django.db.models import Sum
        result = self.cash_in_transactions.aggregate(total=Sum('amount'))
        return result['total'] or 0

    def get_cash_out_total(self):
        """Calculate total cash out"""
        from django.db.models import Sum
        result = self.cash_out_transactions.aggregate(total=Sum('amount'))
        return result['total'] or 0

class CashInTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('banking', 'Banking'),
        ('short_term_loans', 'Short Term Loans'),
        ('long_term_loans', 'Long Term Loans'),
        ('savings', 'Savings'),
        ('welfare', 'Welfare'),
        ('education_project', 'Education Project'),
        ('agriculture_project', 'Agriculture Project'),
        ('ukombozini_loan', 'Ukombozini Loan'),
        ('application_fee', 'Application Fee'),
        ('appreciation_fee', 'Appreciation Fee'),
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='cash_in_transactions')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField(blank=True, null=True)
    transaction_date = models.DateField()
    receipt_number = models.CharField(max_length=50, blank=True, null=True)

    # For appreciation fee calculation
    related_loan = models.ForeignKey('loans.Loan', on_delete=models.SET_NULL, blank=True, null=True, related_name='appreciation_fees')
                                   

    # Audit fields
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cash In Transaction'
        verbose_name_plural = 'Cash In Transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['group', 'transaction_date']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.group.name} - {self.get_transaction_type_display()} - {self.amount}"

    def save(self, *args, **kwargs):
        # Auto-calculate appreciation fee if it's 1% of a loan
        if self.transaction_type == 'appreciation_fee' and self.related_loan:
            self.amount = self.related_loan.principal_amount * Decimal('0.01')
            self.description = f"1% appreciation fee for loan #{self.related_loan.id}"
        super().save(*args, **kwargs)

class CashOutTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('service_fee', 'Service Fee'),
        ('welfare', 'Welfare Payment'),
        ('loan_to_ukombozini', 'Loan to Ukombozini'),
        ('short_term_loans', 'Short Term Loans Disbursement'),
        ('long_term_loans', 'Long Term Loans Disbursement'),
        ('operational_costs', 'Operational Costs'),
        ('dividends', 'Dividends Payment'),
        ('other', 'Other Expenses'),
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='cash_out_transactions')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField()
    transaction_date = models.DateField()
    voucher_number = models.CharField(max_length=50, blank=True, null=True)
    recipient_name = models.CharField(max_length=255, blank=True, null=True)

    # Audit fields
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cash Out Transaction'
        verbose_name_plural = 'Cash Out Transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['group', 'transaction_date']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.group.name} - {self.get_transaction_type_display()} - {self.amount}"

class TRFBalance(models.Model):
    """TRF (Transfer) Balance Table - Second financial table"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='trf_balances')
    balance_date = models.DateField()
    balance_account = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    short_term_arrears = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    long_term_loans_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Additional tracking
    total_assets = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_liabilities = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_worth = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Notes
    notes = models.TextField(blank=True, null=True)

    # Audit fields
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'TRF Balance'
        verbose_name_plural = 'TRF Balances'
        ordering = ['-balance_date']
        unique_together = ['group', 'balance_date']

    def __str__(self):
        return f"{self.group.name} - TRF Balance - {self.balance_date}"

    def save(self, *args, **kwargs):
        # Calculate net worth
        self.net_worth = self.total_assets - self.total_liabilities
        super().save(*args, **kwargs)

    def calculate_balances(self):
        """Calculate automatic balances from transactions"""
        # This method can be called to auto-calculate balances from transactions
        cash_in_total = self.group.get_cash_in_total()
        cash_out_total = self.group.get_cash_out_total()

        # Simple calculation - in real implementation, this would be more complex
        self.balance_account = cash_in_total - cash_out_total
        self.save()

class GroupMeeting(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='meetings')
    meeting_date = models.DateTimeField()
    venue = models.CharField(max_length=255)
    agenda = models.TextField(blank=True, null=True)
    minutes = models.TextField(blank=True, null=True)

    # Attendance
    total_attendance = models.PositiveIntegerField(default=0)

    # Financial decisions
    decisions_made = models.TextField(blank=True, null=True)
    amount_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Status
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Group Meeting'
        verbose_name_plural = 'Group Meetings'
        ordering = ['-meeting_date']

    def __str__(self):
        return f"{self.group.name} Meeting - {self.meeting_date.strftime('%Y-%m-%d')}"

class MeetingAttendance(models.Model):
    meeting = models.ForeignKey(GroupMeeting, on_delete=models.CASCADE, related_name='attendance')
    # member = models.ForeignKey('members.Member', on_delete=models.CASCADE)
    attended = models.BooleanField(default=True)
    arrival_time = models.TimeField(blank=True, null=True)
    contribution_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        # unique_together = ['meeting', 'member']
        verbose_name = 'Meeting Attendance'
        verbose_name_plural = 'Meeting Attendances'

    def __str__(self):
        status = "Present" if self.attended else "Absent"
        return f"{self.member} - {status} - {self.meeting}"
