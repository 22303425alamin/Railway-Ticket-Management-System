from django.db import models


class Train(models.Model):
    """Train Information with Seat Availability"""
    
    CLASS_CHOICES = (
        ('AC', 'Air Conditioned'),
        ('Non-AC', 'Non Air Conditioned'),
        ('Sleeper', 'Sleeper'),
    )
    
    train_number = models.CharField(max_length=10, unique=True)
    train_name = models.CharField(max_length=100)
    total_seats = models.IntegerField(default=100, help_text="Total seats per train")
    available_seats = models.IntegerField(default=100, help_text="Currently available seats")
    total_coaches = models.IntegerField(default=10)
    classes_available = models.CharField(max_length=100, help_text="e.g., AC,Non-AC,Sleeper")
    off_day = models.CharField(max_length=50, blank=True, null=True, 
                                help_text="Days when train doesn't run (e.g., Sunday)")
    
    def __str__(self):
        return f"{self.train_name} ({self.train_number})"
    
    def book_seat(self, count=1):
        """Reduce available seats"""
        if self.available_seats >= count:
            self.available_seats -= count
            self.save()
            return True
        return False
    
    def release_seat(self, count=1):
        """Increase available seats (for cancellation)"""
        if self.available_seats + count <= self.total_seats:
            self.available_seats += count
            self.save()
    
    class Meta:
        ordering = ['train_name']
        verbose_name = 'Train'
        verbose_name_plural = 'Trains'


class Route(models.Model):
    """Train Route with Station Info (Station entity merged here)"""
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='routes')
    
    # Station info merged
    source = models.CharField(max_length=100, help_text="Starting station")
    destination = models.CharField(max_length=100, help_text="End station")
    
    # Route details
    sequence_order = models.IntegerField(help_text="Station order in route (1, 2, 3...)")
    distance_from_origin = models.DecimalField(max_digits=6, decimal_places=2, default=0, 
                                                help_text="Distance in KM from first station")
    departure_time = models.TimeField(help_text="Departure time from this station")
    arrival_time = models.TimeField(null=True, blank=True, help_text="Arrival time (if not first station)")
    day_offset = models.IntegerField(default=0, help_text="Days after journey start (0=same day)")
    
    def __str__(self):
        return f"{self.train.train_name} - {self.source} to {self.destination} (Seq: {self.sequence_order})"
    
    class Meta:
        ordering = ['train', 'sequence_order']
        unique_together = ['train', 'sequence_order']
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'


class TrainSchedule(models.Model):
    """Train Schedule - Max 10 days ahead"""
    
    STATUS_CHOICES = (
        ('running', 'Running'),
        ('cancelled', 'Cancelled'),
        ('delayed', 'Delayed'),
    )
    
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    journey_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    delay_minutes = models.IntegerField(default=0, help_text="Delay in minutes")
    
    def __str__(self):
        return f"{self.train.train_name} - {self.journey_date} ({self.status})"
    
    class Meta:
        ordering = ['-journey_date']
        unique_together = ['train', 'journey_date']
        verbose_name = 'Train Schedule'
        verbose_name_plural = 'Train Schedules'