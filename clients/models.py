# clavis_event_inventory/clients/models.py

from django.db import models

class Client(models.Model):
    """Represents a client (individual or company) who books events or rentals."""
    name = models.CharField(
        max_length=200,
        help_text="Client's full name or primary contact name if company."
    )
    company_name = models.CharField(
        max_length=200,
        blank=True, # Optional field
        null=True,  # Allow null in database
        help_text="Company name, if applicable."
    )
    contact_person = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Specific contact person at the company (if different from name)."
    )
    email = models.EmailField(
        unique=True, # Still unique if provided
        null=True,   # Allow NULL in the database (for optional unique fields)
        blank=True,  # Allow to be blank in forms
        help_text="Primary email address for the client (optional)."
    )
    phone = models.CharField(
        max_length=30, # Adjust max_length based on expected phone number formats
        blank=True,    # Allow to be blank in forms
        null=True,     # Allow NULL in the database
        help_text="Primary phone number for the client (optional)."
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Billing or primary address for the client."
    )
    created_at = models.DateTimeField(auto_now_add=True) # Timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)    # Timestamp for last update

    def __str__(self):
        """String representation of the Client model."""
        if self.company_name:
            return f"{self.company_name} ({self.name})"
        return self.name

    class Meta:
        ordering = ['company_name', 'name'] # Order clients primarily by company, then name
