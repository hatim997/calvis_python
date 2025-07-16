# clavis_event_inventory/bookings/admin.py

from django.contrib import admin
from .models import Event, Rental, EventItem, RentalItem # Import all booking models

# --- Inline Admin Definitions ---
# These allow editing related items directly within the Event/Rental admin page

class EventItemInline(admin.TabularInline): # Use TabularInline for a compact table format
    model = EventItem
    fields = ('item', 'quantity') # Fields to show in the inline form
    extra = 1 # Number of empty extra forms to display
    autocomplete_fields = ['item'] # Use autocomplete for item selection (requires search_fields on ItemAdmin later)
    verbose_name = "Booked Item"
    verbose_name_plural = "Booked Items for this Event"

class RentalItemInline(admin.TabularInline):
    model = RentalItem
    fields = ('item', 'quantity')
    extra = 1
    autocomplete_fields = ['item'] # Use autocomplete for item selection
    verbose_name = "Booked Item"
    verbose_name_plural = "Booked Items for this Rental"


# --- Main ModelAdmin Definitions ---
# These customize the main admin view for Events and Rentals

@admin.register(Event) # Use decorator to register Event with EventAdmin options
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 
        'event_name', # ADDED event_name
        'client', 
        'event_location',
        'start_date', 
        'end_date', 
        'status',
        'project_manager_name', 
        'subcontractor_name'
    )
    list_filter = ('status', 'start_date', 'client')
    search_fields = (
        'reference_number', 
        'event_name', # ADDED event_name
        'client__name', 
        'client__company_name',
        'event_location', 
        'items__item__name',
        'project_manager_name', 
        'subcontractor_name'
    )
    readonly_fields = ('reference_number', 'created_at', 'updated_at') # Prevent editing these fields
    fieldsets = (
        (None, {
            'fields': ('client', 
                       'event_name', # ADDED event_name
                       ('start_date', 'end_date'), 
                       'status')
        }),
        ('Event Specifics', { # Renamed section for clarity
            'fields': ('event_location', 
                       'project_manager_name', 
                       'subcontractor_name', 
                       'notes')
        }),
        ('System Information', {
            'fields': ('reference_number', 'created_at', 'updated_at'),
            'classes': ('collapse',), # Make this section collapsible
        }),
    )
    inlines = [EventItemInline] # Include the EventItem editor directly on the Event page

@admin.register(Rental) # Use decorator to register Rental with RentalAdmin options
class RentalAdmin(admin.ModelAdmin):
    list_display = (
        'reference_number', 'client', 
        'start_date', 'end_date', 'status',
        'project_manager_name', 'subcontractor_name',
        'delivery_location' # ADDED delivery_location
    )
    list_filter = ('status', 'start_date', 'client')
    search_fields = (
        'reference_number', 'client__name', 'client__company_name',
        'items__item__name',
        'project_manager_name', 'subcontractor_name',
        'delivery_location' # ADDED delivery_location
    )
    readonly_fields = ('reference_number', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('client', ('start_date', 'end_date'), 'status')
        }),
        ('Rental Specifics', { # Renamed section for clarity
            'fields': ('delivery_location', # ADDED delivery_location
                       'project_manager_name', 
                       'subcontractor_name', 
                       'notes')
        }),
        ('System Information', {
            'fields': ('reference_number', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    inlines = [RentalItemInline] # Include the RentalItem editor directly on the Rental page

# Note: We don't need to explicitly register EventItem or RentalItem here
# because they are handled by the 'inlines' in EventAdmin and RentalAdmin.
