# clavis_event_inventory/suppliers/admin.py

from django.contrib import admin
from .models import Supplier # Import the Supplier model from models.py in the same directory

# Register your models here.
admin.site.register(Supplier)