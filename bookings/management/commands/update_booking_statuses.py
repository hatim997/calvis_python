# bookings/management/commands/update_booking_statuses.py

from django.core.management.base import BaseCommand
from django.utils import timezone
# from django.core.mail import send_mail # Not sending email directly for now
from django.conf import settings
from datetime import timedelta
from bookings.models import Event, Rental
from dashboard.models import Notification # Import the Notification model
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch # To generate URLs for notification links

User = get_user_model()

class Command(BaseCommand):
    help = 'Updates booking statuses based on dates and creates in-app notifications.'

    def _create_notification(self, message, booking_object=None):
        """
        Helper function to create a Notification object.
        Tries to assign to a superuser, then staff, then first active user.
        Constructs a link to the booking object if possible.
        """
        target_user = None
        # Prioritize superusers, then staff, then any active user
        admin_users = User.objects.filter(is_superuser=True, is_active=True).order_by('pk')
        if admin_users.exists():
            target_user = admin_users.first()
        else:
            staff_users = User.objects.filter(is_staff=True, is_active=True).order_by('pk')
            if staff_users.exists():
                target_user = staff_users.first()
            else: 
                active_users = User.objects.filter(is_active=True).order_by('pk')
                if active_users.exists():
                    target_user = active_users.first()
        
        link_url_path = None
        if booking_object:
            try:
                if isinstance(booking_object, Event) and hasattr(booking_object, 'get_absolute_url'):
                    link_url_path = booking_object.get_absolute_url()
                elif isinstance(booking_object, Rental) and hasattr(booking_object, 'get_absolute_url'):
                    link_url_path = booking_object.get_absolute_url()
                
                # Prepend SITE_URL if defined and link_url_path is not None
                # Ensure SITE_URL does not end with '/' and link_url_path does not start with '/' before joining
                if link_url_path and hasattr(settings, 'SITE_URL') and settings.SITE_URL:
                    site_url = str(settings.SITE_URL).rstrip('/')
                    path = str(link_url_path).lstrip('/')
                    link_url_path = f"{site_url}/{path}"
                elif link_url_path: # If SITE_URL not set, use relative path
                    pass # link_url_path is already relative
                else:
                    link_url_path = None


            except NoReverseMatch:
                 self.stdout.write(self.style.ERROR(f"Could not generate URL for booking {booking_object.reference_number}. Ensure get_absolute_url and URL patterns (e.g., 'bookings:event_detail', 'bookings:rental_detail') are correct in your urls.py and models."))
                 link_url_path = None 
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error generating link for booking {booking_object.reference_number}: {e}"))
                link_url_path = None
        
        Notification.objects.create(
            user=target_user, # Assign to the found admin/staff user, or None
            message=message,
            link=link_url_path
        )
        self.stdout.write(self.style.NOTICE(f"In-app notification created: {message}"))


    def handle(self, *args, **options):
        now = timezone.now()
        one_day_from_now_date = (now + timedelta(days=1)).date()
        
        if not hasattr(settings, 'SITE_URL') or not settings.SITE_URL:
            self.stdout.write(self.style.WARNING(
                "settings.SITE_URL is not defined or is empty. "
                "Notification links will be relative if get_absolute_url provides relative paths, "
                "or may be incomplete if get_absolute_url relies on SITE_URL."
            ))
            # To avoid errors if SITE_URL is used in string formatting and is None
            # It's better to ensure get_absolute_url returns a relative path if SITE_URL is not set.
            # The _create_notification method handles prepending settings.SITE_URL.

        self.stdout.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Running update_booking_statuses command...")
        
        updated_event_count = 0
        updated_rental_count = 0
        notifications_created_count = 0

        # --- Process Events ---
        # Rule 1: PLANNED -> ACTIVE
        events_to_activate = Event.objects.filter(
            status=Event.StatusChoices.PLANNED,
            start_date__lte=now,
            end_date__gte=now 
        )
        for event in events_to_activate:
            event.status = Event.StatusChoices.ACTIVE
            event.save()
            updated_event_count += 1
            msg = f"Event '{event.event_name}' (Ref: {event.reference_number}) status changed to ACTIVE."
            self.stdout.write(self.style.SUCCESS(msg))
            self._create_notification(message=msg, booking_object=event)
            notifications_created_count +=1

        # Rule 2: ACTIVE -> COMPLETED
        events_to_complete = Event.objects.filter(
            status=Event.StatusChoices.ACTIVE,
            end_date__lt=now 
        )
        for event in events_to_complete:
            event.status = Event.StatusChoices.COMPLETED
            event.save()
            updated_event_count += 1
            msg = f"Event '{event.event_name}' (Ref: {event.reference_number}) status changed to COMPLETED."
            self.stdout.write(self.style.SUCCESS(msg))
            self._create_notification(message=msg, booking_object=event)
            notifications_created_count +=1
            
        # Notification: Upcoming Events (1 day in advance)
        upcoming_events_to_notify = Event.objects.filter(
            status=Event.StatusChoices.PLANNED,
            start_date__date=one_day_from_now_date 
        )
        for event in upcoming_events_to_notify:
            message = (
                f"Upcoming Event Reminder: '{event.event_name}' (Ref: {event.reference_number}) "
                f"for client '{event.client}' is scheduled to start on {event.start_date.strftime('%Y-%m-%d %H:%M')}."
            )
            self._create_notification(message=message, booking_object=event)
            notifications_created_count +=1

        # Notification: Events Nearing Completion (1 day in advance of end_date)
        events_ending_soon_to_notify = Event.objects.filter(
            status=Event.StatusChoices.ACTIVE,
            end_date__date=one_day_from_now_date
        )
        for event in events_ending_soon_to_notify:
            message = (
                f"Event Nearing Completion: '{event.event_name}' (Ref: {event.reference_number}) "
                f"for client '{event.client}' is scheduled to end on {event.end_date.strftime('%Y-%m-%d %H:%M')}."
            )
            self._create_notification(message=message, booking_object=event)
            notifications_created_count +=1

        # --- Process Rentals ---
        # Rule 1: BOOKED -> OUT
        rentals_to_set_out = Rental.objects.filter(
            status=Rental.StatusChoices.BOOKED,
            start_date__lte=now,
            end_date__gte=now 
        )
        for rental in rentals_to_set_out:
            rental.status = Rental.StatusChoices.OUT
            rental.save()
            updated_rental_count += 1
            msg = f"Rental (Ref: {rental.reference_number}) for client '{rental.client}' status changed to OUT."
            self.stdout.write(self.style.SUCCESS(msg))
            self._create_notification(message=msg, booking_object=rental)
            notifications_created_count +=1

        # Rule 2: OUT -> OVERDUE
        rentals_to_set_overdue = Rental.objects.filter(
            status=Rental.StatusChoices.OUT,
            end_date__lt=now 
        ).exclude(status__in=[Rental.StatusChoices.RETURNED, Rental.StatusChoices.CANCELLED])
        
        for rental in rentals_to_set_overdue:
            rental.status = Rental.StatusChoices.OVERDUE
            rental.save()
            updated_rental_count += 1
            msg = f"Rental (Ref: {rental.reference_number}) for client '{rental.client}' status changed to OVERDUE."
            self.stdout.write(self.style.WARNING(msg))
            self._create_notification(message=msg, booking_object=rental)
            notifications_created_count +=1

        # Notification: Upcoming Rentals (1 day in advance)
        upcoming_rentals_to_notify = Rental.objects.filter(
            status=Rental.StatusChoices.BOOKED,
            start_date__date=one_day_from_now_date
        )
        for rental in upcoming_rentals_to_notify:
            message = (
                f"Upcoming Rental Reminder: Rental (Ref: {rental.reference_number}) "
                f"for client '{rental.client}' is scheduled for pickup on {rental.start_date.strftime('%Y-%m-%d %H:%M')}."
            )
            self._create_notification(message=message, booking_object=rental)
            notifications_created_count +=1

        # Notification: Rentals Nearing Return (1 day in advance of end_date)
        rentals_ending_soon_to_notify = Rental.objects.filter(
            status__in=[Rental.StatusChoices.OUT, Rental.StatusChoices.OVERDUE],
            end_date__date=one_day_from_now_date
        ).exclude(status__in=[Rental.StatusChoices.RETURNED, Rental.StatusChoices.CANCELLED])
        
        for rental in rentals_ending_soon_to_notify:
            message = (
                f"Rental Nearing Return: Rental (Ref: {rental.reference_number}) "
                f"for client '{rental.client}' is due for return on {rental.end_date.strftime('%Y-%m-%d %H:%M')}."
            )
            self._create_notification(message=message, booking_object=rental)
            notifications_created_count +=1

        self.stdout.write(self.style.SUCCESS(f"Finished updating statuses. Events updated: {updated_event_count}. Rentals updated: {updated_rental_count}."))
        if notifications_created_count > 0:
            self.stdout.write(self.style.NOTICE(f"Total in-app notifications created: {notifications_created_count}"))
        else:
            self.stdout.write("No new notifications created this run.")