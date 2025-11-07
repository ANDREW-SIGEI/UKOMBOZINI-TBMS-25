from django.contrib import admin
from .models import Dividend

@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'date', 'description')
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'description')
    ordering = ('-date',)
