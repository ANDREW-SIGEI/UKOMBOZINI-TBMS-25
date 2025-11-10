from django.db import models
from django.utils import timezone
from ukombozini.apps.sync.models import SyncableModel

class SavingsTransaction(SyncableModel):
    TRANSACTION_TYPES = [
        ('saving', 'Saving'),
        ('welfare', 'Welfare'),
        ('fine', 'Fine'),
        ('appreciation_fee', 'Appreciation Fee'),
        ('application_fee', 'Application Fee'),
        ('project_contribution', 'Project Contribution'),
    ]

    member = models.ForeignKey('members.Member', on_delete=models.CASCADE, related_name='savings_transactions_new')
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='savings_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=255, blank=True, null=True)
    transaction_date = models.DateField(default=timezone.now)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recorded_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.member} - {self.transaction_type} ({self.amount})"

    class Meta:
        ordering = ['-transaction_date']
