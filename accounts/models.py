from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User Model - Customer & Admin with Passenger Info"""
    
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Administrator'),
    )
    
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    
    # Contact Info
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Passenger Info (merged from Passenger entity)
    full_name = models.CharField(max_length=100, blank=True, null=True, 
                                  help_text="Full name for ticket")
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    
    # Role
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin_user(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'