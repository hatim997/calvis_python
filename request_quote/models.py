from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from bookings.models import BookingItemBase  # or re-define if not reusable
import uuid

def generate_reference_number():
    today = timezone.now().strftime('%Y%m%d')
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"REQ-{today}-{unique_part}"

class QuoteRequest(models.Model):
    # client_name = models.CharField(max_length=255)
    client = models.ForeignKey(
        'clients.Client',  # <-- This is valid
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)ss',
        help_text="The client associated with this quote."
    )


    # Dates & Times
    event_start_date = models.DateTimeField()
    setup_installation_datetime = models.DateTimeField()
    event_end_date = models.DateTimeField()
    setup_removal_datetime = models.DateTimeField()

    # Project details
    event_title = models.CharField(max_length=255)
    project_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quoted_projects",
        help_text="User assigned as Project Manager"
    )
    subcontractors = models.CharField(max_length=255, blank=True)
    delivery_note_signed_from = models.CharField(max_length=255, blank=True)

    # Meta info
    date_created = models.DateField(auto_now_add=True)
    reference_number = models.CharField(max_length=50, unique=True, default=generate_reference_number)

    # Notes
    project_manager_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.event_title} ({self.reference_number})"

class QuoteRequestItem(BookingItemBase):
    """
    Links an Item with quantity to a specific QuoteRequest.
    """
    booking = models.ForeignKey(
        QuoteRequest,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="The quote request this item is linked to."
    )

    class Meta:
        unique_together = [['booking', 'item']]
        verbose_name = "Quote Request Item"
        verbose_name_plural = "Quote Request Items"
