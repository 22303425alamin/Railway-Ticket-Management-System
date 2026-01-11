from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['pnr', 'user', 'train', 'journey_date', 'total_fare', 'payment_status', 'booking_date']
    list_filter = ['payment_status', 'journey_date', 'booking_date', 'payment_method']
    search_fields = ['pnr', 'user__username', 'train__train_name', 'transaction_id']
    readonly_fields = ['pnr', 'booking_date']
    date_hierarchy = 'journey_date'
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('pnr', 'user', 'train', 'route', 'train_schedule', 'journey_date', 'booking_date')
        }),
        ('Fare Details', {
            'fields': ('base_fare', 'reservation_charge', 'tax', 'total_fare')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id', 'payment_date')
        }),
    )