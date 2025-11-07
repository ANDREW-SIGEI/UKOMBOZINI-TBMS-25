from django.contrib import admin
from .models import Dividend

@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Filter dividends based on user type
        if request.user.user_type == 'field_officer':
            # Field officers can only see dividends for groups assigned to them
            # Since dividends are paid to users, we need to filter based on user's groups
            qs = qs.filter(user__managed_groups__field_officer=request.user).distinct()
        # Admin users can see all dividends

        return qs

    list_display = ('user', 'amount', 'date', 'description')
    list_filter = ('date', 'user')
    search_fields = ('user__username', 'description')
    ordering = ('-date',)
