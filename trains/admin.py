from django.contrib import admin
from .models import Station, Train, Route, TrainSchedule


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['station_code', 'station_name', 'city']
    search_fields = ['station_code', 'station_name', 'city']
    ordering = ['station_name']


class RouteInline(admin.TabularInline):
    model = Route
    extra = 1
    ordering = ['sequence_order']
    fields = ['station', 'sequence_order', 'distance_from_origin', 'departure_time', 'arrival_time']


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ['train_number', 'train_name', 'total_seats', 'available_seats', 'off_day', 'classes_available']
    search_fields = ['train_number', 'train_name']
    list_filter = ['off_day']
    inlines = [RouteInline]


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['train', 'station', 'sequence_order', 'departure_time', 'distance_from_origin']
    list_filter = ['train', 'station']
    search_fields = ['train__train_name', 'station__station_name']
    ordering = ['train', 'sequence_order']


@admin.register(TrainSchedule)
class TrainScheduleAdmin(admin.ModelAdmin):
    list_display = ['train', 'departure_time', 'arrival_time', 'off_days', 'status']
    list_filter = ['status']
    search_fields = ['train__train_name']