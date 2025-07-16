# clavis_event_inventory/clients/admin.py

from django.contrib import admin
from .models import Client # Import the Client model from this app

# Register your models here.
admin.site.register(Client)

# Later, we can customize how Clients appear in the admin list/forms
# admin.site.register(Client, ClientAdmin) # using a custom ModelAdmin class