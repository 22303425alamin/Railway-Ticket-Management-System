from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('new/<int:train_id>/', views.new_booking, name='new_booking'),
    path('confirm/', views.confirm_booking, name='confirm_booking'),
    path('payment/<int:booking_id>/', views.payment, name='payment'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<str:pnr>/', views.booking_detail, name='booking_detail'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('download-ticket/<str:pnr>/', views.download_ticket, name='download_ticket'),
]