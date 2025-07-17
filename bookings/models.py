# clavis_event_inventory/bookings/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # For default dates or reference numbers
import uuid # For generating unique reference numbers
from django.urls import reverse 
from django.contrib.auth.models import User

# Import related models from other apps using string paths to avoid circular imports
# from clients.models import Client (use 'clients.Client' instead)
# from inventory.models import Item (use 'inventory.Item' instead)

def generate_reference_number():
    """Generates a unique booking reference number (e.g., BKG-YYYYMMDD-XXXXXX)."""
    today = timezone.now().strftime('%Y%m%d')
    # Generate a short unique part (6 characters from UUID4 hex)
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"BKG-{today}-{unique_part}"

# --- Abstract Base Class for Common Booking Fields ---
class BaseBooking(models.Model):
    """Abstract model containing fields common to both Events and Rentals."""
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT, 
        related_name='%(class)ss', 
        help_text="The client associated with this booking."
    )
    project_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='%(class)ss_as_manager', 
        help_text="User assigned as Project Manager."
    )
    start_date = models.DateTimeField(
        help_text="The date and time the event/rental period begins."
    )
    end_date = models.DateTimeField(
        help_text="The date and time the event/rental period ends."
    )
    project_manager_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Name of the assigned Project Manager."
    )
    subcontractor_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Name of the subcontractor, if any."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes or special instructions for this booking."
    )
    reference_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_reference_number, 
        editable=False, 
        help_text="Unique system-generated reference number for this booking."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True 
        ordering = ['start_date', 'created_at'] 

    def clean(self):
        super().clean() 
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(_("End date cannot be before the start date."))

    def __str__(self):
        client_name = str(self.client) if self.client else "N/A"
        return f"Booking {self.reference_number} for {client_name}"


# --- Event Model ---
class Event(BaseBooking):
    """Represents a scheduled event requiring inventory OR a logistics service.""" # MODIFIED help_text
    class StatusChoices(models.TextChoices):
        PLANNED = 'PLANNED', _('Planned')     
        ACTIVE = 'ACTIVE', _('Active')       
        COMPLETED = 'COMPLETED', _('Completed') 
        CANCELLED = 'CANCELLED', _('Cancelled') 

    event_name = models.CharField(
        max_length=255,
        help_text="The official name or title of the event/service." # MODIFIED help_text
    )
    event_location = models.CharField( 
        max_length=255,
        help_text="Specific address or location description for the event or primary delivery site." # MODIFIED help_text
    )
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PLANNED,
        help_text="Current status of the event booking/logistics task." # MODIFIED help_text
    )

    # === NEW Logistics Specific Fields ===
    is_logistics_only_service = models.BooleanField(
        default=False,
        help_text="Check if this booking is primarily for a logistics/transport service only."
    )
    description_of_goods = models.TextField(
        blank=True, null=True,
        help_text="Description of goods being transported for a logistics service (e.g., quantity, type, special handling)."
    )
    # Leg 1: Client Warehouse to Event Site
    pickup_address = models.TextField( 
        blank=True, null=True,
        help_text="Full address for picking up goods from the client."
    )
    pickup_contact_details = models.TextField(
        blank=True, null=True,
        help_text="Contact name and phone for the pickup location."
    )
    delivery_address_override = models.TextField( 
        blank=True, null=True,
        help_text="Specific delivery address for logistics if different from main Event Location (e.g. event_location)."
    )
    delivery_contact_details = models.TextField(
        blank=True, null=True,
        help_text="Contact name and phone for the delivery at the event site."
    )
    # Leg 2: Event Site back to Client Warehouse
    return_pickup_address = models.TextField( 
        blank=True, null=True,
        help_text="Address for picking up goods from the event site for return (usually same as Event Location or Delivery Address Override)."
    )
    return_pickup_contact_details = models.TextField(
        blank=True, null=True,
        help_text="Contact name and phone for pickup from the event site."
    )
    return_delivery_address = models.TextField( 
        blank=True, null=True,
        help_text="Final return address for the goods (e.g., client's warehouse)."
    )
    return_delivery_contact_details = models.TextField(
        blank=True, null=True,
        help_text="Contact name and phone for the final return delivery."
    )
    # === END NEW Logistics Specific Fields ===

    class Meta(BaseBooking.Meta): 
        verbose_name = "Event / Logistics Booking" # MODIFIED verbose name
        verbose_name_plural = "Event / Logistics Bookings" # MODIFIED verbose name plural

    def __str__(self): 
        client_name = str(self.client) if self.client else "N/A"
        # MODIFIED to reflect service type
        service_type = "Logistics Service" if self.is_logistics_only_service else "Event"
        return f"{service_type}: {self.event_name or 'N/A'} ({self.reference_number}) for {client_name}"

    def get_absolute_url(self):
        return reverse('bookings:event_detail', kwargs={'event_id': self.pk})


# --- Rental Model ---
class Rental(BaseBooking):
    """Represents a rental agreement for inventory items."""
    class StatusChoices(models.TextChoices):
        BOOKED = 'BOOKED', _('Booked')        
        OUT = 'OUT', _('Out for Rental')      
        RETURNED = 'RETURNED', _('Returned')    
        OVERDUE = 'OVERDUE', _('Overdue')     
        CANCELLED = 'CANCELLED', _('Cancelled') 

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.BOOKED,
        help_text="Current status of the rental booking."
    )
    delivery_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional delivery location for the rental items."
    )

    @property
    def is_overdue(self):
        """
        Returns True if the rental's end_date has passed,
        and its status is not 'RETURNED' or 'CANCELLED'.
        """
        if self.end_date and self.status not in [self.StatusChoices.RETURNED, self.StatusChoices.CANCELLED]:
            return timezone.now() > self.end_date
        return False

    class Meta(BaseBooking.Meta): 
        verbose_name = "Rental Booking"
        verbose_name_plural = "Rental Bookings"

    def get_absolute_url(self):
        return reverse('bookings:rental_detail', kwargs={'rental_id': self.pk})


# --- Abstract Base Class for Linking Items to Bookings ---
class BookingItemBase(models.Model):
    """Abstract model for linking an Item with quantity to a Booking."""
    item = models.ForeignKey(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='+', 
        help_text="The specific inventory item booked."
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="The number of units of this item booked."
    )

    class Meta:
        abstract = True 

    def clean(self):
        super().clean()
        if self.quantity <= 0:
            raise ValidationError(_("Quantity must be a positive number."))
        
        # Check if item is None or if item doesn't have 'initial_quantity'
        # This validation will need to be updated if/when 'initial_quantity' in inventory.Item is changed to 'quantity_owned'
        if not self.item or not hasattr(self.item, 'initial_quantity') or not hasattr(self.item, 'item_source'):
            return

        if self.item.item_source == 'OWNED': # Assuming ItemSourceType.OWNED is 'OWNED'
            # Check against the total physical stock ('initial_quantity' for now)
            if self.quantity > self.item.initial_quantity: # Using initial_quantity as per current inventory.models.py
                raise ValidationError(
                    _("Cannot book %(requested)s units of '%(item_name)s'. Only %(owned)s total units are owned by the company.") % {
                        'requested': self.quantity,
                        'owned': self.item.initial_quantity, 
                        'item_name': self.item.name,
                    }
                )
            # A more precise availability check considering other bookings for a *specific date range*
            # would typically use self.item.is_available(quantity, start_date, end_date) in formset validation.

    def __str__(self):
        item_name = self.item.name if self.item else "N/A" 
        return f"{self.quantity} x {item_name}"


# --- Linking Table for Event Items ---
class EventItem(BookingItemBase):
    """Links an Item with quantity to a specific Event."""
    booking = models.ForeignKey(
        Event,
        on_delete=models.CASCADE, 
        related_name='items', 
        help_text="The event this item is booked for."
    )

    class Meta:
        unique_together = [['booking', 'item']]
        verbose_name = "Event Item"
        verbose_name_plural = "Event Items"


# --- Linking Table for Rental Items ---
class RentalItem(BookingItemBase):
    """Links an Item with quantity to a specific Rental."""
    booking = models.ForeignKey(
        Rental,
        on_delete=models.CASCADE, 
        related_name='items', 
        help_text="The rental this item is booked for."
    )

    class Meta:
        unique_together = [['booking', 'item']]
        verbose_name = "Rental Item"
        verbose_name_plural = "Rental Items"