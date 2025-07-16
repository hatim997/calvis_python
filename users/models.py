from django.db import models
from django.contrib.auth.hashers import make_password

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('viewer', 'Viewer'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    number = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    password = models.CharField(max_length=128)  # Store hashed password
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def __str__(self):
        return self.name
