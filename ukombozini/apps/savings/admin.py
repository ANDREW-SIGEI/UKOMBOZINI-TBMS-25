from django.contrib import admin
from .models import SavingsTransaction

@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'member', 'group', 'transaction_type', 'amount', 'transaction_date',
        'balance_after', 'recorded_by'
    ]
    list_filter = ['transaction_type', 'transaction_date', 'group', 'recorded_by']
    search_fields = ['member__first_name', 'member__last_name', 'reference', 'notes']
    ordering = ['-transaction_date']

    fieldsets = (
        ('Transaction Details', {
            'fields': ('member', 'group', 'amount', 'transaction_type', 'reference')
        }),
        ('Date & Balance', {
            'fields': ('transaction_date', 'balance_after')
        }),
        ('Audit Trail', {
            'fields': ('recorded_by', 'notes')
        })
    )
