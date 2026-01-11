from django.contrib import admin
from .models import Train, Route, TrainSchedule


class RouteInline(admin.TabularInline):
    model = Route
    extra = 1
    ordering = ['sequence_order']
    fields = ['source', 'destination', 'sequence_order', 'distance_from_origin', 'departure_time', 'arrival_time']


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ['train_number', 'train_name', 'total_seats', 'available_seats', 'off_day', 'classes_available']
    search_fields = ['train_number', 'train_name']
    list_filter = ['off_day']
    inlines = [RouteInline]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['train', 'source', 'destination', 'sequence_order', 'departure_time', 'distance_from_origin']
    list_filter = ['train', 'source', 'destination']
    search_fields = ['train__train_name', 'source', 'destination']
    ordering = ['train', 'sequence_order']


@admin.register(TrainSchedule)
class TrainScheduleAdmin(admin.ModelAdmin):
    list_display = ['train', 'journey_date', 'status', 'delay_minutes']
    list_filter = ['status', 'journey_date']
    search_fields = ['train__train_name']
    date_hierarchy = 'journey_date'