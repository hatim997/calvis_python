# clavis_event_inventory/inventory/models.py

from django.db import models
from django.db.models import Q, Sum # Ensure Q and Sum are imported
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime # Import datetime

# Top-level try-except for initial app loading for Event and Rental (for StatusChoices)
try:
    from bookings.models import Event, Rental
except ImportError:
    Event = None
    Rental = None
# EventItem and RentalItem will be imported directly inside methods

class Category(models.Model):
    """Represents a category for inventory items, supporting hierarchy."""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the category (e.g., Furniture, Linens, AV Equipment)."
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        help_text="Optional parent category for creating hierarchies."
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

class Item(models.Model):
    """Represents a distinct type of inventory item available for rent/events."""

    class DimensionUnit(models.TextChoices):
        """Choices for dimension units."""
        CM = 'CM', _('Centimeters')
        IN = 'IN', _('Inches')
        MM = 'MM', _('Millimeters')
        M = 'M', _('Meters')
        DM = 'DM', _('Diameters')

    # === NEW Item Source Field ===
    class ItemSourceType(models.TextChoices):
        OWNED = 'OWNED', _('Owned by Company')
        CLIENT_SUPPLIED = 'CLIENT_SUPPLIED', _('Supplied by Client for Event')
        # Add more sources later if needed, e.g., CROSS_RENTED
    
    item_source = models.CharField(
        max_length=20,
        choices=ItemSourceType.choices,
        default=ItemSourceType.OWNED,
        help_text="Indicates the source or ownership of the item."
    )
    # === END NEW Item Source Field ===

    name = models.CharField(
        max_length=200,
        help_text="Clear, descriptive name (e.g., 'White Folding Chair', '6ft Rectangular Table')."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="More detailed notes about the item."
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        editable=False,
        help_text="System-generated unique Stock Keeping Unit."
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        help_text="Category this item belongs to."
    )
    storage_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Physical storage location (e.g., Warehouse A, Shelf B-3)."
    )
    initial_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Total number of this specific item owned or received from client." # Updated help_text
    )

    depth = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Depth dimension (optional).")
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Width dimension (optional).")
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Height dimension (optional).")
    dimension_unit = models.CharField(
        max_length=5,
        choices=DimensionUnit.choices,
        default=DimensionUnit.CM,
        help_text="Units for the dimensions provided (Depth x Width x Height)."
    )

    image1 = models.ImageField( upload_to='item_images/', help_text="Primary image of the item." ) # Consider making optional if client items might not have images
    image2 = models.ImageField( upload_to='item_images/', blank=True, null=True, help_text="Optional second image of the item." )
 
    purchase_price = models.DecimalField( 
        max_digits=10, decimal_places=2, null=True, blank=True, 
        help_text="Cost of acquiring a single unit of this item (for valuation, N/A for client-supplied)." 
    )
    rent_price_per_day = models.DecimalField( 
        max_digits=10, decimal_places=2, 
        help_text="Daily rental charge for a single unit of this item (N/A for client-supplied)." 
    ) # Consider null=True, blank=True if client-supplied items have no rent price

    supplier = models.ForeignKey( 
        'suppliers.Supplier', 
        on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='supplied_items', 
        help_text="Supplier this item was purchased from (optional, N/A for client-supplied)." 
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Calculated fields / Methods ---

    def get_assigned_quantity_in_range(self, start_date, end_date, exclude_event_pk=None, exclude_rental_pk=None):
        """ Calculates SUM of quantities from bookings OVERLAPPING the date range, optionally excluding a booking. """
        from bookings.models import EventItem, RentalItem 
        if Event is None or Rental is None: return 0

        unavailable_event_statuses = [Event.StatusChoices.PLANNED, Event.StatusChoices.ACTIVE]
        unavailable_rental_statuses = [Rental.StatusChoices.BOOKED, Rental.StatusChoices.OUT, Rental.StatusChoices.OVERDUE]

        event_items_query = EventItem.objects.filter( item=self, booking__end_date__gte=start_date, booking__start_date__lte=end_date, booking__status__in=unavailable_event_statuses )
        if exclude_event_pk: event_items_query = event_items_query.exclude(booking_id=exclude_event_pk)
        overlapping_event_qty = event_items_query.aggregate(total=Sum('quantity'))['total'] or 0

        rental_items_query = RentalItem.objects.filter( item=self, booking__end_date__gte=start_date, booking__start_date__lte=end_date, booking__status__in=unavailable_rental_statuses )
        if exclude_rental_pk: rental_items_query = rental_items_query.exclude(booking_id=exclude_rental_pk)
        overlapping_rental_qty = rental_items_query.aggregate(total=Sum('quantity'))['total'] or 0
        
        return overlapping_event_qty + overlapping_rental_qty

    def is_available(self, quantity_needed, start_date, end_date, exclude_event_pk=None, exclude_rental_pk=None):
        """ Checks availability using the simple overlapping sum logic, optionally excluding a specific booking. """
        if self.item_source == self.ItemSourceType.CLIENT_SUPPLIED:
            # Client-supplied items are only available for their specific event context,
            # general availability check might not be appropriate here or needs different logic.
            # For now, let's assume if it's booked, it's available for that booking.
            # This method might need refinement for client-supplied items.
            # Consider if quantity_needed is relevant outside of a specific client's booking.
            pass # Let it proceed with normal logic for now, but flag for review.

        if quantity_needed <= 0: return True
        assigned_during_period = self.get_assigned_quantity_in_range( start_date, end_date, exclude_event_pk=exclude_event_pk, exclude_rental_pk=exclude_rental_pk )
        potential_available = self.initial_quantity - assigned_during_period
        return potential_available >= quantity_needed

    def get_assigned_quantity_on_date(self, target_date):
        """ 
        Calculates how many units are assigned out:
        1. For Events: Overlapping the target date and PLANNED or ACTIVE.
        2. For Rentals: 
            a. Overlapping the target date and BOOKED or OUT.
            OR 
            b. Ended BEFORE the target date but status is still OUT or OVERDUE.
        """
        from bookings.models import EventItem, RentalItem 
        if Event is None or Rental is None:
            return 0

        try:
            start_of_day = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time.min))
            end_of_day = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time.max))
        except Exception as e:
            print(f"Error creating aware datetimes in get_assigned_quantity_on_date: {e}")
            return 0

        active_event_statuses = [Event.StatusChoices.PLANNED, Event.StatusChoices.ACTIVE]
        assigned_event_qty = EventItem.objects.filter(
            item=self,
            booking__start_date__lte=end_of_day,
            booking__end_date__gte=start_of_day,
            booking__status__in=active_event_statuses
        ).aggregate(total=Sum('quantity'))['total'] or 0

        rentals_overlapping_today_statuses = [Rental.StatusChoices.BOOKED, Rental.StatusChoices.OUT]
        rental_overlap_query = Q(
            booking__start_date__lte=end_of_day,
            booking__end_date__gte=start_of_day,
            booking__status__in=rentals_overlapping_today_statuses
        )

        rentals_physically_out_overdue_statuses = [Rental.StatusChoices.OUT, Rental.StatusChoices.OVERDUE]
        rental_past_due_and_out_query = Q(
            booking__end_date__lt=start_of_day, 
            booking__status__in=rentals_physically_out_overdue_statuses
        )
        
        assigned_rental_qty = RentalItem.objects.filter(
            Q(item=self) & (rental_overlap_query | rental_past_due_and_out_query)
        ).distinct().aggregate(total=Sum('quantity'))['total'] or 0
        
        total_assigned = assigned_event_qty + assigned_rental_qty
        return total_assigned

    @property
    def currently_assigned(self):
        today = timezone.now().date()
        return self.get_assigned_quantity_on_date(today)

    @property
    def available_quantity(self):
        # For client-supplied items, this might represent "available from what client gave us"
        # rather than "available for any booking".
        # The core logic might still work if initial_quantity is set to what client supplied.
        assigned_now = self.currently_assigned
        return max(0, self.initial_quantity - assigned_now)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # If it's a client-supplied item, some fields might not be relevant
        if self.item_source == self.ItemSourceType.CLIENT_SUPPLIED:
            self.purchase_price = None # Or 0
            # self.rent_price_per_day = None # Or 0, model currently requires this
            self.supplier = None
        
        super().save(*args, **kwargs)
        if is_new and not self.sku and self.pk:
            if self.category and self.category.name:
                prefix = ''.join(filter(str.isalnum, self.category.name.upper()))[:2]
            else:
                prefix = 'ITEM'  # fallback if category missing

            self.sku = f"{prefix}-{str(self.pk).zfill(6)}"
            super().save(update_fields=['sku'])

    def __str__(self):
        return f"{self.name} ({self.sku or 'No SKU'})"

    class Meta:
        ordering = ['category', 'name']
        
class ItemImage(models.Model):
    item = models.ForeignKey(Item, related_name='extra_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='item_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.item.name}"
