# clavis_event_inventory/suppliers/models.py

from django.db import models

class Supplier(models.Model):
    """Represents a supplier or vendor for inventory items."""
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Name of the supplier company or individual."
    )
    contact_person = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Primary contact person at the supplier."
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Contact email address for the supplier."
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Contact phone number for the supplier."
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Physical or mailing address of the supplier."
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any relevant notes about the supplier."
    )
    created_at = models.DateTimeField(auto_now_add=True) # Automatically set when object is created
    updated_at = models.DateTimeField(auto_now=True)    # Automatically set when object is saved

    def __str__(self):
        """String representation of the Supplier model."""
        return self.name

    class Meta:
        ordering = ['name'] # Order suppliers alphabetically by default