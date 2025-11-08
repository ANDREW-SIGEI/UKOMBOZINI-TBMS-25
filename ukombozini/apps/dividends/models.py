from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import date
from django.utils import timezone

class DividendPeriod(models.Model):
    """
    Represents a dividend calculation period (December only)
    """
    PERIOD_TYPES = [
        ('annual', 'Annual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., "2024 Annual Dividends"
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPES, default='annual')
    year = models.PositiveIntegerField(unique=True)  # e.g., 2024, 2025

    # Data collection months (Jan, Mar, May, Jul, Sep)
    DATA_MONTHS = [1, 3, 5, 7, 9]

    # December-only period (1st Dec to 31st Dec)
    start_date = models.DateField()  # December 1st of the year
    end_date = models.DateField()    # December 31st of the year

    calculation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('approved', 'Approved'),
        ('distributed', 'Distributed'),
    ], default='draft')

    # Admin control for field officer visibility
    visible_to_field_officers = models.BooleanField(default=False)
    visible_to_members = models.BooleanField(default=False)

    # Financial figures for the period (EXCLUDING FINES)
    total_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    net_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Allocation percentages
    reserve_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,  # 20% to reserves
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    development_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,  # 10% to development fund
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    dividend_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00,  # 70% for dividends
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Calculated amounts
    reserve_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    development_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_dividend_pool = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    class Meta:
        ordering = ['-year']
        verbose_name = "Dividend Period"
        verbose_name_plural = "Dividend Periods"
        constraints = [
            models.UniqueConstraint(
                fields=['year'],
                name='unique_dividend_year'
            )
        ]

    def __str__(self):
        return f"{self.year} Annual Dividends ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Ensure only December periods are created"""
        if not self.start_date or not self.end_date:
            # Auto-set to December of the specified year
            self.start_date = date(self.year, 12, 1)
            self.end_date = date(self.year, 12, 31)

        # Validate that it's a December period
        if self.start_date.month != 12 or self.end_date.month != 12:
            raise ValueError("Dividend periods can only be created for December")

        if self.start_date.year != self.year or self.end_date.year != self.year:
            raise ValueError("Dividend period year must match the specified year")

        super().save(*args, **kwargs)

    def is_current_december(self):
        """Check if this is the current December period"""
        today = timezone.now().date()
        return today.month == 12 and today.year == self.year

    def can_calculate_dividends(self):
        """Only allow dividend calculation in December"""
        return self.is_current_december() and self.status == 'draft'

    def get_data_collection_months(self):
        """Get the months used for data collection (Jan, Mar, May, Jul, Sep)"""
        return self.DATA_MONTHS

    def calculate_net_profit_for_group(self, group):
        """
        Calculate net profit EXCLUDING fines for a specific group
        Using data from Jan, Mar, May, Jul, Sep
        """
        from transactions.models import CashInTransaction, CashOutTransaction

        # INCOME SOURCES (EXCLUDING FINES) - For data collection months only
        income_sources = [
            'banking', 'short_term', 'long_term', 'savings', 'welfare',
            'education_project', 'agriculture_project', 'ukombozini_loan',
            'application_fee', 'appreciation_fee',
        ]

        total_income = Decimal('0.00')
        total_expenses = Decimal('0.00')

        # Calculate for each data collection month
        for month in self.DATA_MONTHS:
            month_start = date(self.year, month, 1)
            month_end = date(self.year, month, 1)  # Will be adjusted to end of month

            # Calculate end of month
            if month == 12:
                month_end = date(self.year, month, 31)
            else:
                month_end = date(self.year, month + 1, 1) - timezone.timedelta(days=1)

            # Income for this month
            month_income = CashInTransaction.objects.filter(
                transaction_type__in=income_sources,
                group=group,
                transaction_date__range=[month_start, month_end]
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

            total_income += month_income

            # Expenses for this month
            expense_sources = [
                'service_fee', 'welfare', 'loan_to_ukombozini',
                'short_term_loans', 'long_term_loans', 'project_funding',
            ]

            month_expenses = CashOutTransaction.objects.filter(
                transaction_type__in=expense_sources,
                group=group,
                transaction_date__range=[month_start, month_end]
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

            total_expenses += month_expenses

        net_profit = total_income - total_expenses
        return net_profit, total_income, total_expenses

    def allocate_profits(self):
        """
        Allocate net profit to reserves, development, and dividends
        """
        if self.net_profit <= 0:
            return False

        self.reserve_amount = (self.net_profit * self.reserve_percentage) / 100
        self.development_amount = (self.net_profit * self.development_percentage) / 100
        self.total_dividend_pool = (self.net_profit * self.dividend_percentage) / 100

        self.save()
        return True

    def generate_group_dividends_report(self, group):
        """
        Generate comprehensive dividends payable report for a specific group
        """
        member_dividends = MemberDividend.objects.filter(
            dividend_period=self,
            member__group=group
        )

        # Calculate group financials
        net_profit, total_income, total_expenses = self.calculate_net_profit_for_group(group)

        report = {
            'group_info': {
                'id': group.id,
                'name': group.name,
                'location': group.location,
                'total_members': group.members.count(),
                'active_members': group.members.filter(membership_status='active').count(),
            },
            'financial_summary': {
                'data_months': [self.get_month_name(month) for month in self.DATA_MONTHS],
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
                'reserve_amount': (net_profit * self.reserve_percentage) / 100,
                'development_amount': (net_profit * self.development_percentage) / 100,
                'dividend_pool': (net_profit * self.dividend_percentage) / 100,
            },
            'dividend_summary': {
                'total_members_with_dividends': member_dividends.count(),
                'total_dividends_payable': sum(d.total_dividend for d in member_dividends),
                'average_dividend': sum(d.total_dividend for d in member_dividends) / member_dividends.count() if member_dividends.exists() else 0,
                'highest_dividend': max(d.total_dividend for d in member_dividends) if member_dividends.exists() else 0,
                'lowest_dividend': min(d.total_dividend for d in member_dividends) if member_dividends.exists() else 0,
            },
            'member_breakdown': [
                {
                    'member_id': md.member.id,
                    'member_name': md.member.get_full_name(),
                    'phone_number': md.member.phone_number,
                    'savings_amount': md.member.total_savings,
                    'savings_based_dividend': md.savings_based_amount,
                    'patronage_based_dividend': md.patronage_based_amount,
                    'total_dividend': md.total_dividend,
                    'distribution_status': 'Distributed' if md.distributed else 'Pending'
                }
                for md in member_dividends.order_by('-total_dividend')
            ]
        }

        return report

    def get_month_name(self, month_number):
        """Convert month number to name"""
        months = {
            1: 'January', 3: 'March', 5: 'May',
            7: 'July', 9: 'September'
        }
        return months.get(month_number, 'Unknown')

    def get_previous_payments_for_group(self, group):
        """
        Get all previous dividend payments for a specific group
        """
        previous_periods = DividendPeriod.objects.filter(
            year__lt=self.year,
            status__in=['approved', 'distributed']
        ).order_by('-year')

        previous_payments = []
        for period in previous_periods:
            group_dividends = MemberDividend.objects.filter(
                dividend_period=period,
                member__group=group
            )

            if group_dividends.exists():
                total_distributed = sum(md.total_dividend for md in group_dividends)

                previous_payments.append({
                    'year': period.year,
                    'total_distributed': total_distributed,
                    'member_count': group_dividends.count(),
                    'average_dividend': total_distributed / group_dividends.count(),
                    'status': period.status
                })

        return previous_payments

    def calculate_dividends_for_group(self, group):
        """
        Calculate dividends for ALL members in a specific group
        Only allowed in December
        """
        if not self.can_calculate_dividends():
            return False, "Dividend calculation only allowed in December for draft periods"

        # Calculate net profit for this group
        net_profit, total_income, total_expenses = self.calculate_net_profit_for_group(group)

        if net_profit <= 0:
            return False, f"No profit generated for {group.name}"

        # Allocate profits for this group
        reserve_amount = (net_profit * self.reserve_percentage) / 100
        development_amount = (net_profit * self.development_percentage) / 100
        group_dividend_pool = (net_profit * self.dividend_percentage) / 100

        # Get all active members in this group with savings
        active_members = group.members.filter(
            membership_status='active',
            total_savings__gt=0
        )

        if not active_members.exists():
            return False, f"No active members with savings in {group.name}"

        # Calculate dividends for each member in the group
        savings_dividends = self._calculate_savings_based_dividends_for_group(active_members, group_dividend_pool)
        patronage_dividends = self._calculate_patronage_based_dividends_for_group(active_members, group_dividend_pool)

        # Create dividend records for each member in the group
        dividends_created = 0
        for member in active_members:
            savings_portion = savings_dividends.get(member.id, Decimal('0.00'))
            patronage_portion = patronage_dividends.get(member.id, Decimal('0.00'))
            total_dividend = savings_portion + patronage_portion

            # Create or update member dividend
            MemberDividend.objects.update_or_create(
                dividend_period=self,
                member=member,
                defaults={
                    'savings_based_amount': savings_portion,
                    'patronage_based_amount': patronage_portion,
                    'total_dividend': total_dividend,
                    'calculation_method': 'hybrid_60_40'
                }
            )
            dividends_created += 1

        return True, f"Dividends calculated for {dividends_created} members in {group.name}"

    def _calculate_savings_based_dividends_for_group(self, members, dividend_pool):
        """
        Calculate 60% of dividend pool based on savings ratio for group members
        """
        savings_pool = dividend_pool * Decimal('0.60')
        total_savings = sum(member.total_savings for member in members)

        dividends = {}
        for member in members:
            if total_savings > 0:
                savings_ratio = member.total_savings / total_savings
                dividends[member.id] = savings_pool * savings_ratio
            else:
                dividends[member.id] = Decimal('0.00')

        return dividends

    def _calculate_patronage_based_dividends_for_group(self, members, dividend_pool):
        """
        Calculate 40% of dividend pool based on patronage score for group members
        """
        patronage_pool = dividend_pool * Decimal('0.40')

        # Calculate patronage scores for each member
        member_scores = {}
        total_score = Decimal('0.00')

        for member in members:
            score = self._calculate_patronage_score_for_member(member)
            member_scores[member.id] = score
            total_score += score

        # Distribute patronage pool based on scores
        dividends = {}
        for member in members:
            if total_score > 0:
                patronage_ratio = member_scores[member.id] / total_score
                dividends[member.id] = patronage_pool * patronage_ratio
            else:
                dividends[member.id] = Decimal('0.00')

        return dividends

    def _calculate_patronage_score_for_member(self, member):
        """
        Calculate patronage score for a member using data from Jan, Mar, May, Jul, Sep
        """
        score = Decimal('100.00')  # Base score

        # Calculate for data collection months only
        year_start = date(self.year, 1, 1)
        year_end = date(self.year, 9, 30)  # Only up to September

        # Factor 1: Loan interest paid (30% weight)
        total_interest_paid = member.get_total_interest_paid(year_start, year_end)
        score += (total_interest_paid * Decimal('0.30'))

        # Factor 2: Transaction frequency (20% weight)
        transaction_count = member.get_transaction_count(year_start, year_end)
        score += (transaction_count * Decimal('0.20'))

        # Factor 3: Timely repayments (30% weight)
        on_time_repayments = member.get_on_time_repayment_rate(year_start, year_end)
        score += (on_time_repayments * Decimal('30.00'))

        # Factor 4: Meeting attendance (20% weight)
        attendance_rate = member.get_meeting_attendance_rate(year_start, year_end)
        score += (attendance_rate * Decimal('20.00'))

        return max(score, Decimal('0.00'))


class MemberDividend(models.Model):
    """
    Individual member dividend calculation for a period
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dividend_period = models.ForeignKey(DividendPeriod, on_delete=models.CASCADE)
    member = models.ForeignKey('members.Member', on_delete=models.CASCADE)

    # Calculation breakdown
    savings_based_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    patronage_based_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_dividend = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    calculation_method = models.CharField(max_length=50, default='hybrid_60_40')
    calculated_at = models.DateTimeField(auto_now_add=True)

    # Distribution tracking
    distributed = models.BooleanField(default=False)
    distribution_date = models.DateField(null=True, blank=True)
    distribution_method = models.CharField(max_length=50, blank=True, choices=[
        ('cash', 'Cash'),
        ('savings_account', 'Savings Account'),
        ('reinvestment', 'Reinvestment'),
    ])

    class Meta:
        unique_together = ['dividend_period', 'member']
        ordering = ['-dividend_period__year', 'member__first_name']
        verbose_name = "Member Dividend"
        verbose_name_plural = "Member Dividends"

    def __str__(self):
        return f"{self.member} - {self.dividend_period.year}: {self.total_dividend}"

    def is_visible_to_field_officer(self):
        """Check if field officers can see this dividend"""
        return self.dividend_period.visible_to_field_officers

    def is_visible_to_member(self):
        """Check if members can see this dividend"""
        return self.dividend_period.visible_to_members


class DividendDistribution(models.Model):
    """
    Tracks actual dividend distributions to members
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dividend_period = models.ForeignKey(DividendPeriod, on_delete=models.CASCADE)
    distribution_date = models.DateField()
    total_distributed = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    distributed_by = models.ForeignKey('users.CustomUser', on_delete=models.PROTECT)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-distribution_date']
        verbose_name = "Dividend Distribution"
        verbose_name_plural = "Dividend Distributions"

    def __str__(self):
        return f"Distribution {self.distribution_date} - {self.total_distributed}"


# Legacy model for backward compatibility (deprecated)
class Dividend(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Dividend for {self.user.username}: {self.amount}"

    class Meta:
        ordering = ['-date']
