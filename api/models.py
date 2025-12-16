from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('guest', 'Guest'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    status = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class Forwarder(models.Model):
    name = models.CharField(max_length=255)
    # Status is varchar in your diagram, assuming 'Active'/'Inactive'
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    
    # Relationship to the User who created this
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='forwarders')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    
class Destination(models.Model):
    name = models.CharField(max_length=255)
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    
    # Relationship to User
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='destinations')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return
    
# class OrderImport(models.Model):
#     file = models.FileField(upload_to='uploads/orders/')
#     uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
#     uploaded_at = models.DateTimeField(auto_now_add=True)
    
#     # We will store the parsed excel data here as JSON
#     parsed_data = models.JSONField(null=True, blank=True)
    
#     def __str__(self):
#         return f"Order {self.id} - {self.uploaded_at}"

class OrderImport(models.Model):
    file = models.FileField(upload_to='uploads/orders/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_data = models.JSONField(null=True, blank=True)
    
    # --- THESE ARE THE MISSING FIELDS CAUSING THE ERROR ---
    BOT_STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    bot_status = models.CharField(max_length=20, choices=BOT_STATUS_CHOICES, default='idle')
    bot_message = models.TextField(blank=True, null=True) 
    generated_zip = models.FileField(upload_to='downloads/zips/', null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.uploaded_at}"