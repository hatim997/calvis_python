# clavis_event_inventory/bookings/forms.py

from django import forms
from django.forms import inlineformset_factory, BooleanField # Import BooleanField

# Import models from their correct apps
from .models import Event, EventItem, Rental, RentalItem
from inventory.models import Item # This should still refer to the Item model with initial_quantity
from clients.models import Client
from django.contrib.auth.models import User

# --- Event Forms ---

class EventForm(forms.ModelForm):
    """Form for creating or editing an Event or Logistics Service."""
    client = forms.ModelChoiceField(
        queryset=Client.objects.order_by('company_name', 'name'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    event_name = forms.CharField(
        label="Event/Service Title", # Changed label to be more generic
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Annual Gala Dinner / Equipment Transport'})
    )
    start_date = forms.DateTimeField(
        label="Start Date & Time", # Generic label
        help_text="Select the date and time the event/service begins.",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    end_date = forms.DateTimeField(
        label="End Date & Time", # Generic label
        help_text="Select the date and time the event/service ends.",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    project_manager_name = forms.CharField(
        label="Project Manager",
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of Project Manager'})
    )
    project_manager = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Project Manager"
    )
    subcontractor_name = forms.CharField(
        label="Subcontractor",
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of Subcontractor'})
    )
    
    # === NEW Logistics Fields Added to Form ===
    is_logistics_only_service = forms.BooleanField(
        label="This is a Logistics-Only Service",
        required=False, # Important: allow it to be unchecked
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}) 
    )
    description_of_goods = forms.CharField(
        label="Description of Goods (for Logistics)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., 2x Pallets of AV Equipment, 1x Generator'})
    )
    pickup_address = forms.CharField(
        label="Pickup Address (Leg 1)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    pickup_contact_details = forms.CharField(
        label="Pickup Contact (Leg 1)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    delivery_address_override = forms.CharField(
        label="Delivery Address (Leg 1 - if different from Event Location)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    delivery_contact_details = forms.CharField(
        label="Delivery Contact (Leg 1)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    return_pickup_address = forms.CharField(
        label="Return Pickup Address (Leg 2 - from site)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    return_pickup_contact_details = forms.CharField(
        label="Return Pickup Contact (Leg 2)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    return_delivery_address = forms.CharField(
        label="Return Delivery Address (Leg 2 - to client/warehouse)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    return_delivery_contact_details = forms.CharField(
        label="Return Delivery Contact (Leg 2)",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    # === END NEW Logistics Fields ===

    class Meta:
        model = Event
        fields = [
            'client', 
            'event_name', 
            'event_location', 
            'project_manager', 
            'start_date', 'end_date', 
            'project_manager_name', 'subcontractor_name', 
            'status', 
            'is_logistics_only_service', # ADDED
            'description_of_goods',      # ADDED
            'pickup_address',            # ADDED
            'pickup_contact_details',    # ADDED
            'delivery_address_override', # ADDED
            'delivery_contact_details',  # ADDED
            'return_pickup_address',       # ADDED
            'return_pickup_contact_details',# ADDED
            'return_delivery_address',     # ADDED
            'return_delivery_contact_details',# ADDED
            'notes', # Moved notes to the end
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'event_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main event/service location or primary delivery site'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class EventItemForm(forms.ModelForm):
    """Form for an individual item within the Event booking."""
    # This queryset uses 'initial_quantity' which is correct for your backup project state.
    # It also now filters by item_source='OWNED'
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(
            item_source=Item.ItemSourceType.OWNED, # Only show company-owned items for selection
            initial_quantity__gt=0 # Ensure there's some stock
        ).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select item-select'}),
        help_text="Select an item from your company's inventory." # Added help_text
    )
    quantity = forms.IntegerField(
        min_value=1, initial=1,
        widget=forms.NumberInput(attrs={'min': '1', 'class': 'form-control quantity-input'})
    )
    class Meta:
        model = EventItem
        fields = ['item', 'quantity']

EventItemInlineFormSet = inlineformset_factory(
    Event, EventItem, form=EventItemForm, 
    extra=1, can_delete=True, fk_name='booking' # Explicitly set fk_name
)


# --- Rental Forms ---

class RentalForm(forms.ModelForm):
    """Form for creating or editing a Rental."""
    client = forms.ModelChoiceField(
        queryset=Client.objects.order_by('company_name', 'name'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateTimeField(
        label="Rental Pickup Date & Time",
        help_text="Select the date and time the rental period begins (pickup).",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    end_date = forms.DateTimeField(
        label="Rental Return Date & Time",
        help_text="Select the date and time the rental period ends (return).",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    project_manager_name = forms.CharField(
        label="Project Manager",
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of Project Manager'})
    )
    project_manager = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Project Manager"
    )
    subcontractor_name = forms.CharField(
        label="Subcontractor",
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of Subcontractor'})
    )
    delivery_location = forms.CharField(
        label="Delivery Location (Optional)",
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Specific address or location for delivery, if different from client address or if items are being delivered.'})
    )

    class Meta:
        model = Rental
        fields = [
            'client', 'start_date', 'end_date', 'project_manager', 
            'project_manager_name', 'subcontractor_name', 
            'delivery_location', 
            'notes', 'status'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

# RentalItemForm - assuming it should also only use company-owned items
class RentalItemForm(forms.ModelForm):
    """Form for an individual item within the Rental booking."""
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(
            item_source=Item.ItemSourceType.OWNED, # Only show company-owned items
            initial_quantity__gt=0
        ).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select item-select'}),
        help_text="Select an item from your company's inventory."
    )
    quantity = forms.IntegerField(
        min_value=1, initial=1,
        widget=forms.NumberInput(attrs={'min': '1', 'class': 'form-control quantity-input'})
    )
    class Meta:
        model = RentalItem
        fields = ['item', 'quantity']

RentalItemInlineFormSet = inlineformset_factory(
    Rental, RentalItem, form=RentalItemForm, # Changed to use RentalItemForm
    extra=1, can_delete=True, fk_name='booking' # Explicitly set fk_name
)