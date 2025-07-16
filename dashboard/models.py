# clavis_event_inventory/dashboard/models.py

from django.db import models
from django.conf import settings # To link to the User model
from django.utils import timezone

class Notification(models.Model):
    """
    Model to store in-app notifications for users.
    """
    # Link to the user who should receive the notification.
    # If you want notifications for specific users, otherwise this can be omitted
    # or made nullable if notifications are system-wide for all admins.
    # For now, let's assume notifications are for the admin/staff.
    # We can refine this later if needed (e.g., link to a specific Project Manager).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        null=True, # Make null=True if notifications can be system-wide and not user-specific
        blank=True # Make blank=True if not always assigning to a specific user
    )
    
    # The content of the notification message.
    message = models.TextField(
        help_text="The content of the notification."
    )
    
    # Timestamp for when the notification was created.
    created_at = models.DateTimeField(
        default=timezone.now
    )
    
    # Boolean field to mark if the notification has been read by the user.
    is_read = models.BooleanField(
        default=False,
        help_text="Has this notification been read?"
    )
    
    # Optional: Link to a relevant object (e.g., an Event or Rental booking)
    # This requires generic foreign keys if you want to link to different model types,
    # or separate ForeignKey fields for each type of related object.
    # For simplicity now, we'll omit this, but it can be added.
    # Example:
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    # object_id = models.PositiveIntegerField(null=True, blank=True)
    # related_object = GenericForeignKey('content_type', 'object_id')

    # Optional: A URL that the notification can link to directly in the frontend.
    link = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Optional URL to navigate to when the notification is clicked."
    )

    class Meta:
        ordering = ['-created_at'] # Show newest notifications first
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        timestamp = self.created_at.strftime('%Y-%m-%d %H:%M')
        read_status = "Read" if self.is_read else "Unread"
        msg_snippet = (self.message[:75] + '...') if len(self.message) > 75 else self.message
        user_info = f"for {self.user.username} " if self.user else ""
        return f"Notification {user_info}({read_status}) @ {timestamp}: {msg_snippet}"

    def mark_as_read(self):
        """Marks the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    def mark_as_unread(self):
        """Marks the notification as unread."""
        if self.is_read:
            self.is_read = False
            self.save(update_fields=['is_read'])