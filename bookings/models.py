from django.db import models
from django.conf import settings
from trains.models import Train, Station, TrainSchedule
import random
import string


def generate_pnr():
    """Generate unique 10-digit PNR"""
    return ''.join(random.choices(string.digits, k=10))


class Payment(models.Model):
    """Payment/Booking Entity - Simplified (PNR = Booking ID)"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash'),
    )
    
    BOOKING_STATUS_CHOICES = (
        ('booked', 'Booked'),
        ('travelled', 'Travelled'),
        ('cancelled', 'Cancelled'),
    )

    
    # PNR = Primary booking identifier
    pnr = models.CharField(max_length=10, unique=True, default=generate_pnr, primary_key=True)
    
    # Foreign Keys
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    train_schedule = models.ForeignKey(TrainSchedule, on_delete=models.CASCADE)
    
    # Journey Details with Stations
    origin_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='origin_payments')
    destination_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='destination_payments')
    journey_date = models.DateField()
    booking_date = models.DateTimeField(auto_now_add=True)
    
    # Fare Details
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reservation_charge = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='booked')

    # Payment Details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    

    
    def __str__(self):
        return f"PNR: {self.pnr} - {self.user.username} - {self.train.train_name}"
    
    def calculate_fare(self):
        """Calculate total fare"""
        self.tax = (self.base_fare + self.reservation_charge) * 0.05  # 5% tax
        self.total_fare = self.base_fare + self.reservation_charge + self.tax
        self.save()
    
    class Meta:
        ordering = ['-booking_date']
        verbose_name = 'Payment/Booking'
        verbose_name_plural = 'Payments/Bookings'