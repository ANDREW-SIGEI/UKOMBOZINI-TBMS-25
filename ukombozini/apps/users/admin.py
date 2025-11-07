from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserActivity

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Filter users based on user type
        if request.user.user_type == 'field_officer':
            # Field officers can only see themselves and other field officers in their county
            qs = qs.filter(
                models.Q(id=request.user.id) |  # Can see themselves
                models.Q(user_type='field_officer', assigned_county=request.user.assigned_county)  # Can see other field officers in same county
            )
        # Admin users can see all users

        return qs

    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type',
                   'assigned_county', 'is_active', 'date_joined', 'last_activity')
    list_filter = ('user_type', 'is_active', 'is_staff', 'assigned_county', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'id_number')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': (
                'user_type', 'phone_number', 'id_number', 'profile_picture',
                'assigned_county', 'assigned_constituency', 'assigned_ward',
                'last_location', 'last_activity'
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': (
                'user_type', 'phone_number', 'id_number',
                'assigned_county', 'assigned_constituency', 'assigned_ward'
            )
        }),
    )

    readonly_fields = ('last_activity', 'date_joined')

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'description', 'timestamp', 'ip_address', 'location')
    list_filter = ('action', 'timestamp', 'user__user_type')
    search_fields = ('user__username', 'description', 'ip_address', 'location')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
