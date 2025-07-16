# clavis_event_inventory/dashboard/views.py

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q
import datetime # Import datetime
from datetime import timedelta
from django.contrib.auth.decorators import login_required # For user-specific notifications

# Import models from other apps
from inventory.models import Item
from clients.models import Client
from bookings.models import Event, Rental, EventItem, RentalItem
from .models import Notification # Import the Notification model

# Define a threshold for low stock - adjust as needed
LOW_STOCK_THRESHOLD = 3

@login_required # Ensure user is logged in to see the dashboard
def dashboard_view(request):
    """
    View function for the main dashboard.
    Gathers data for various widgets and notifications.
    """
    now = timezone.now()
    today = now.date()
    
    next_3_days = today + timedelta(days=3)
    next_7_days = today + timedelta(days=7)

    try:
        start_of_today = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
        end_of_today = timezone.make_aware(datetime.datetime.combine(today, datetime.time.max))
    except Exception as e:
        print(f"Error creating aware datetimes in dashboard_view: {e}")
        start_of_today = datetime.datetime.combine(today, datetime.time.min)
        end_of_today = datetime.datetime.combine(today, datetime.time.max)

    # --- Quick Stats ---
    total_item_types = Item.objects.count()
    total_quantity_owned_agg = Item.objects.aggregate(total=Sum('initial_quantity'))
    total_quantity_owned = total_quantity_owned_agg['total'] if total_quantity_owned_agg['total'] else 0

    assigned_event_qty = EventItem.objects.filter(
        booking__start_date__lte=end_of_today,
        booking__end_date__gte=start_of_today,
        booking__status__in=[Event.StatusChoices.PLANNED, Event.StatusChoices.ACTIVE]
    ).aggregate(total=Sum('quantity'))['total'] or 0

    assigned_rental_qty = RentalItem.objects.filter(
        booking__start_date__lte=end_of_today,
        booking__end_date__gte=start_of_today,
        booking__status__in=[Rental.StatusChoices.BOOKED, Rental.StatusChoices.OUT]
    ).aggregate(total=Sum('quantity'))['total'] or 0

    total_items_assigned_today = assigned_event_qty + assigned_rental_qty
    total_clients = Client.objects.count()

    # --- Upcoming Events/Rentals (Next 7 days) ---
    upcoming_period_end_date = today + timedelta(days=7)
    upcoming_events = Event.objects.filter(
        start_date__date__gte=today,
        start_date__date__lte=upcoming_period_end_date,
        status=Event.StatusChoices.PLANNED
    ).select_related('client').order_by('start_date')[:5]

    upcoming_rentals = Rental.objects.filter(
        start_date__date__gte=today,
        start_date__date__lte=upcoming_period_end_date,
        status=Rental.StatusChoices.BOOKED
    ).select_related('client').order_by('start_date')[:5]

    # --- Items Due Back Soon (Today or next 3 days) ---
    events_ending_soon = Event.objects.filter(
        end_date__date__gte=today,
        end_date__date__lte=next_3_days,
        status=Event.StatusChoices.ACTIVE
    ).select_related('client').order_by('end_date')

    rentals_ending_soon = Rental.objects.filter(
        end_date__gte=now, 
        end_date__date__lte=next_3_days, 
        status__in=[Rental.StatusChoices.OUT, Rental.StatusChoices.BOOKED] 
    ).select_related('client').order_by('end_date')

    # --- Overdue Rentals ---
    overdue_rentals = Rental.objects.filter(
        end_date__lt=now, 
        status__in=[Rental.StatusChoices.OUT, Rental.StatusChoices.BOOKED, Rental.StatusChoices.OVERDUE]
    ).exclude(
        status__in=[Rental.StatusChoices.RETURNED, Rental.StatusChoices.CANCELLED]
    ).select_related('client').order_by('end_date')[:10]

    # --- Low Availability Items ---
    all_items = Item.objects.filter(initial_quantity__gt=0).select_related('category')
    low_stock_items = []
    for item in all_items:
        if item.available_quantity <= LOW_STOCK_THRESHOLD:
            low_stock_items.append(item)
    low_stock_items = low_stock_items[:10]

    # --- Recently Added Items & Clients ---
    recent_items = Item.objects.order_by('-created_at')[:5]
    recent_clients = Client.objects.order_by('-created_at')[:5]

    # --- Fetch Notifications ---
    # Fetch notifications for the current user or system-wide if user is None in Notification model
    # For simplicity, let's assume we show notifications that are either unassigned OR assigned to the current user.
    # You might want to refine this based on your exact needs (e.g., only for logged-in user).
    user_notifications = Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True) # Show user's OR system-wide notifications
    ).order_by('-created_at') # Newest first
    
    unread_notifications_count = user_notifications.filter(is_read=False).count()
    # Show, for example, the latest 10 notifications regardless of read status for the dashboard
    latest_notifications = user_notifications[:10] 


    context = {
        'page_title': 'Dashboard',
        'total_item_types': total_item_types,
        'total_quantity_owned': total_quantity_owned,
        'total_items_assigned_today': total_items_assigned_today,
        'total_clients': total_clients,
        'upcoming_events': upcoming_events,
        'upcoming_rentals': upcoming_rentals,
        'events_ending_soon': events_ending_soon,
        'rentals_ending_soon': rentals_ending_soon,
        'overdue_rentals': overdue_rentals,
        'low_stock_items': low_stock_items,
        'low_stock_threshold': LOW_STOCK_THRESHOLD,
        'recent_items': recent_items,
        'recent_clients': recent_clients,
        'current_time': now,
        'latest_notifications': latest_notifications, # ADDED
        'unread_notifications_count': unread_notifications_count, # ADDED
    }

    return render(request, 'dashboard/dashboard.html', context)