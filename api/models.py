from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import os

def get_folder_name(instance):
    """Helper to get and clean the user's custom folder name"""
    folder = getattr(instance, 'folder_name', None)
    if not folder:
        folder = 'uploads' # Default fallback
    
    # Sanitize: Allow letters, numbers, spaces, dashes, underscores, and slashes
    clean_folder = "".join(x for x in folder if x.isalnum() or x in " -_/")
    
    # Remove leading/trailing slashes to prevent path errors
    return clean_folder.strip('/')

def get_upload_path(instance, filename):
    """
    Path for the INPUT file (The Excel Checklist).
    Example: "My-Invoices/2024/checklist.xlsx"
    """
    folder = get_folder_name(instance)
    return f'{folder}/{filename}'

def get_zip_path(instance, filename):
    """
    Path for the OUTPUT file (The Downloaded Result).
    Now saves to the SAME folder as the input!
    Example: "My-Invoices/2024/checklist_completed.zip"
    """
    folder = get_folder_name(instance)
    return f'{folder}/{filename}'


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


class OrderImport(models.Model):
    # Field to store the custom folder name from Frontend
    folder_name = models.CharField(max_length=255, default='uploads', blank=True)

    # 1. INPUT: Uses get_upload_path
    file = models.FileField(upload_to=get_upload_path)
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_data = models.JSONField(null=True, blank=True)
    
    BOT_STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    bot_status = models.CharField(max_length=20, choices=BOT_STATUS_CHOICES, default='idle')
    bot_message = models.TextField(blank=True, null=True) 
    
    # 2. OUTPUT: Now uses get_zip_path (which points to the same folder)
    generated_zip = models.FileField(upload_to=get_zip_path, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.uploaded_at}"

# class OrderImport(models.Model):
#     file = models.FileField(upload_to='uploads/orders/')
#     uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     parsed_data = models.JSONField(null=True, blank=True)
    
#     # --- THESE ARE THE MISSING FIELDS CAUSING THE ERROR ---
#     BOT_STATUS_CHOICES = [
#         ('idle', 'Idle'),
#         ('running', 'Running'),
#         ('completed', 'Completed'),
#         ('failed', 'Failed')
#     ]
#     bot_status = models.CharField(max_length=20, choices=BOT_STATUS_CHOICES, default='idle')
#     bot_message = models.TextField(blank=True, null=True) 
#     generated_zip = models.FileField(upload_to='downloads/zips/', null=True, blank=True)

#     def __str__(self):
#         return f"Order {self.id} - {self.uploaded_at}"