from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin"""
    
    list_display = ['username', 'email', 'role', 'phone_number', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'phone_number']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'address', 'role')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'address', 'role')
        }),
    )