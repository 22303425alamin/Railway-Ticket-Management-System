from django.db import models


class Station(models.Model):
    """Railway Station - Separate Entity"""
    station_code = models.CharField(max_length=10, unique=True)
    station_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.station_name} ({self.station_code})"
    
    class Meta:
        ordering = ['station_name']
        verbose_name = 'Station'
        verbose_name_plural = 'Stations'


class Train(models.Model):
    """Train Information"""
    
    CLASS_CHOICES = (
        ('AC', 'Air Conditioned'),
        ('Non-AC', 'Non Air Conditioned'),
        ('Sleeper', 'Sleeper'),
    )
    
    train_number = models.CharField(max_length=10, unique=True)
    train_name = models.CharField(max_length=100)
    total_seats = models.IntegerField(default=100, help_text="Total seats available")
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
        """Increase available seats"""
        if self.available_seats + count <= self.total_seats:
            self.available_seats += count
            self.save()
    
    class Meta:
        ordering = ['train_name']
        verbose_name = 'Train'
        verbose_name_plural = 'Trains'


class Route(models.Model):
    """Train stops at stations - Each entry is one station in the route"""
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='routes')
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    sequence_order = models.IntegerField(help_text="Station sequence in route (1, 2, 3...)")
    arrival_time = models.TimeField(null=True, blank=True, help_text="Arrival time at this station")
    departure_time = models.TimeField(help_text="Departure time from this station")
    distance_from_origin = models.DecimalField(max_digits=6, decimal_places=2, default=0, 
                                                help_text="Distance in KM from first station")
    day_offset = models.IntegerField(default=0, help_text="Days after journey start")
    
    def __str__(self):
        return f"{self.train.train_name} - {self.station.station_name} (Seq: {self.sequence_order})"
    
    class Meta:
        ordering = ['train', 'sequence_order']
        unique_together = ['train', 'sequence_order']
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'


class TrainSchedule(models.Model):
    """Train Schedule - Times and Off Days"""
    
    train = models.OneToOneField(Train, on_delete=models.CASCADE, related_name='schedule')
    
    # Timing
    departure_time = models.TimeField(help_text="Default departure time")
    arrival_time = models.TimeField(help_text="Default arrival time at final destination")
    
    # Off days
    off_days = models.CharField(max_length=100, blank=True, null=True,
                                 help_text="Days when train doesn't run (e.g., Sunday,Monday)")
    
    # Status
    status = models.CharField(max_length=20, default='active', 
                              choices=[('active', 'Active'), ('suspended', 'Suspended')])
    
    def __str__(self):
        return f"{self.train.train_name} Schedule"
    
    def is_running_on_date(self, date):
        """Check if train runs on given date"""
        if not self.off_days:
            return True
        
        day_name = date.strftime('%A')  # Monday, Tuesday, etc.
        off_day_list = [d.strip() for d in self.off_days.split(',')]
        return day_name not in off_day_list
    
    class Meta:
        verbose_name = 'Train Schedule'
        verbose_name_plural = 'Train Schedules'