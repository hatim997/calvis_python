# clavis_event_inventory/reports/views.py

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Sum
import calendar

from .forms import MonthlyReportFilterForm
from bookings.models import Event, Rental, EventItem, RentalItem
from clients.models import Client
from inventory.models import Item


# Import utility functions for export
from .utils import (
    generate_monthly_summary_excel,
    generate_monthly_summary_pdf,
    generate_monthly_summary_docx,
    get_month_year_str,
)

def monthly_summary_report_view(request):
    """
    Displays a monthly summary report of events, logistics services, rentals, clients, and item usage.
    Handles export requests.
    """
    # form = MonthlyReportFilterForm(request.GET or None)
    user = request.user
    form = MonthlyReportFilterForm(request.GET or None, user=user)

    # Default empty values
    regular_events_in_month = Event.objects.none()
    logistics_services_in_month = Event.objects.none()
    rentals_in_month = Rental.objects.none()
    clients_summary = {'new_clients': Client.objects.none(), 'new_clients_count': 0}
    item_usage_summary = []

    selected_year = None
    selected_month = None
    selected_pm = None
    month_year_str = "Not Selected"

    if form.is_valid():
        selected_year = form.cleaned_data.get('year', "all")
        selected_month = form.cleaned_data.get('month', "all")
        if 'project_manager' in form.fields:
            selected_pm = form.cleaned_data.get('project_manager')
        else:
            # If user is not superuser, default to their own events
            selected_pm = user
        month_year_str = get_month_year_str(selected_year, selected_month)

        # 1. Regular Events
        regular_events_in_month = Event.objects.filter(is_logistics_only_service=False)
        if selected_year != "all":
            regular_events_in_month = regular_events_in_month.filter(start_date__year=selected_year)
        if selected_month != "all":
            regular_events_in_month = regular_events_in_month.filter(start_date__month=selected_month)
        if selected_pm:
            regular_events_in_month = regular_events_in_month.filter(project_manager=selected_pm)

        # 2. Logistics Services
        logistics_services_in_month = Event.objects.filter(is_logistics_only_service=True)
        if selected_year != "all":
            logistics_services_in_month = logistics_services_in_month.filter(start_date__year=selected_year)
        if selected_month != "all":
            logistics_services_in_month = logistics_services_in_month.filter(start_date__month=selected_month)
        if selected_pm:
            logistics_services_in_month = logistics_services_in_month.filter(project_manager=selected_pm)

        # 3. Rentals
        rentals_in_month = Rental.objects.all()
        if selected_year != "all":
            rentals_in_month = rentals_in_month.filter(start_date__year=selected_year)
        if selected_month != "all":
            rentals_in_month = rentals_in_month.filter(start_date__month=selected_month)
        if selected_pm:
            rentals_in_month = rentals_in_month.filter(project_manager=selected_pm)

        # 4. Clients Summary
        new_clients_in_month = Client.objects.all()
        if selected_year != "all":
            new_clients_in_month = new_clients_in_month.filter(created_at__year=selected_year)
        if selected_month != "all":
            new_clients_in_month = new_clients_in_month.filter(created_at__month=selected_month)

        clients_summary = {
            'new_clients': new_clients_in_month.order_by('created_at'),
            'new_clients_count': new_clients_in_month.count()
        }

        # 5. Item Usage Summary
        usage_dict = {}

        # Event Items
        event_items_usage = EventItem.objects.filter(
            booking__is_logistics_only_service=False
        )
        if selected_year != "all":
            event_items_usage = event_items_usage.filter(booking__start_date__year=selected_year)
        if selected_month != "all":
            event_items_usage = event_items_usage.filter(booking__start_date__month=selected_month)

        event_items_usage = event_items_usage.values('item__name', 'item__sku').annotate(
            times_used=Count('booking', distinct=True),
            total_quantity_used=Sum('quantity')
        )

        for usage in event_items_usage:
            key = (usage['item__sku'], usage['item__name'])
            usage_dict.setdefault(key, {'times_used': 0, 'total_quantity_used': 0})
            usage_dict[key]['times_used'] += usage['times_used']
            usage_dict[key]['total_quantity_used'] += usage.get('total_quantity_used', 0) or 0

        # Rental Items
        rental_items_usage = RentalItem.objects.all()
        if selected_year != "all":
            rental_items_usage = rental_items_usage.filter(booking__start_date__year=selected_year)
        if selected_month != "all":
            rental_items_usage = rental_items_usage.filter(booking__start_date__month=selected_month)

        rental_items_usage = rental_items_usage.values('item__name', 'item__sku').annotate(
            times_used=Count('booking', distinct=True),
            total_quantity_used=Sum('quantity')
        )

        for usage in rental_items_usage:
            key = (usage['item__sku'], usage['item__name'])
            usage_dict.setdefault(key, {'times_used': 0, 'total_quantity_used': 0})
            usage_dict[key]['times_used'] += usage['times_used']
            usage_dict[key]['total_quantity_used'] += usage.get('total_quantity_used', 0) or 0

        # Final list
        item_usage_summary = [
            {'item__name': name, 'item__sku': sku, **data}
            for (sku, name), data in usage_dict.items()
        ]
        item_usage_summary = sorted(item_usage_summary, key=lambda x: (-x['total_quantity_used'], x['item__name']))

        # 6. Export Handling
        export_format = request.GET.get('format')
        if export_format:
            if export_format == 'xlsx':
                return generate_monthly_summary_excel(
                    selected_year, selected_month,
                    regular_events_in_month, logistics_services_in_month,
                    rentals_in_month, clients_summary, item_usage_summary
                )
            elif export_format == 'pdf':
                return generate_monthly_summary_pdf(
                    selected_year, selected_month,
                    regular_events_in_month, logistics_services_in_month,
                    rentals_in_month, clients_summary, item_usage_summary
                )
            elif export_format == 'docx':
                return generate_monthly_summary_docx(
                    selected_year, selected_month,
                    regular_events_in_month, logistics_services_in_month,
                    rentals_in_month, clients_summary, item_usage_summary
                )

    context = {
        'form': form,
        'regular_events_in_month': regular_events_in_month,
        'logistics_services_in_month': logistics_services_in_month,
        'rentals_in_month': rentals_in_month,
        'clients_summary': clients_summary,
        'item_usage_summary': item_usage_summary,
        'selected_month_year_str': month_year_str,
        'page_title': 'Monthly Summary Report'
    }

    return render(request, 'reports/monthly_summary_report.html', context)
