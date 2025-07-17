# clavis_event_inventory/bookings/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from django.http import Http404, HttpResponseForbidden

# Models
from .models import Event, Rental, EventItem, RentalItem
from inventory.models import Item 
from clients.models import Client

# Forms
from .forms import EventForm, EventItemInlineFormSet, RentalForm, RentalItemInlineFormSet

# Utils (for PDF generation)
from .utils import generate_delivery_note_pdf, generate_receipt_pdf
# We will add generate_logistics_waybill_pdf later in utils.py
# from .utils import generate_logistics_waybill_pdf


# --- List Views ---
def event_list_view(request):
    events = Event.objects.all().select_related('client').order_by('-start_date')
    context = { 'events': events, 'page_title': 'Event & Logistics Bookings' } # Updated title
    return render(request, 'bookings/event_list.html', context)

def rental_list_view(request):
    rentals = Rental.objects.all().select_related('client').order_by('-start_date')
    context = { 'rentals': rentals, 'page_title': 'Rental Bookings' }
    return render(request, 'bookings/rental_list.html', context)


# --- Add Views ---
@transaction.atomic
def event_add_view(request):
    if request.method == 'POST':
        event_form = EventForm(request.POST)
        # Initialize item_formset; it will only be validated if not logistics_only
        item_formset = EventItemInlineFormSet(request.POST, prefix='items')

        if event_form.is_valid():
            event_instance = event_form.save(commit=False)
            # Assign project_manager_id
            project_manager = event_form.cleaned_data.get('project_manager')
            event_instance.project_manager = project_manager  # sets project_manager_id

            # Assign project_manager_name as "First Last"
            if project_manager:
                event_instance.project_manager_name = f"{project_manager.first_name} {project_manager.last_name}"
            else:
                event_instance.project_manager_name = ""
            is_logistics_service = event_form.cleaned_data.get('is_logistics_only_service', False)
            event_instance.is_logistics_only_service = is_logistics_service # Ensure it's set on the instance

            if is_logistics_service:
                # For logistics only, we don't need to validate or save the item_formset
                # (unless you decide to use it for ancillary items like packing materials later)
                try:
                    # event_instance.status = Event.StatusChoices.PLANNED # Already handled by form default
                    event_instance.save() # Save the event
                    messages.success(request, f"Logistics Service '{event_instance.event_name}' created successfully!")
                    return redirect(event_instance.get_absolute_url())
                except Exception as e:
                    messages.error(request, f"An error occurred while saving the logistics service: {e}")
            else:
                # For regular events, validate and process the item_formset
                if item_formset.is_valid():
                    start_date = event_form.cleaned_data.get('start_date')
                    end_date = event_form.cleaned_data.get('end_date')
                    all_items_available = True
                    
                    # Check item availability only if there are forms with data and not marked for deletion
                    has_items_to_book = any(form.has_changed() and not form.cleaned_data.get('DELETE', False) for form in item_formset)

                    if has_items_to_book:
                        for form in item_formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                item = form.cleaned_data.get('item')
                                quantity = form.cleaned_data.get('quantity')
                                if item and quantity and start_date and end_date:
                                    # Using initial_quantity for now as per inventory/models.py
                                    if not item.is_available(quantity, start_date, end_date):
                                        all_items_available = False
                                        # Accessing available_quantity property from Item model
                                        error_msg = f"Not enough '{item.name}' available ({item.available_quantity} currently free) for the selected dates [{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}]."
                                        form.add_error('item', error_msg)
                                elif form.has_changed() and not (item and quantity):
                                    form.add_error(None, "Please select an item and quantity, or leave the row empty/delete if not needed.")
                                    all_items_available = False
                    
                    if all_items_available:
                        try:
                            # event_instance.status = Event.StatusChoices.PLANNED # Handled by form
                            event_instance.save() # Save the event object first
                            item_formset.instance = event_instance 
                            item_formset.save() # Save items
                            messages.success(request, f"Event Booking '{event_instance.event_name}' created successfully!")
                            return redirect(event_instance.get_absolute_url())
                        except Exception as e:
                            messages.error(request, f"An error occurred while saving: {e}")
                    else:
                        messages.error(request, "Could not create event. Please correct item availability or form errors.")
                else: # item_formset is not valid
                    messages.error(request, "Please correct the item booking errors below.")
        else: # event_form is not valid
            messages.error(request, "Please correct the event details errors below.")
            # Re-initialize item_formset without POST data if event_form is invalid, to prevent data loss on template
            item_formset = EventItemInlineFormSet(prefix='items')
            
    else: # GET request
        event_form = EventForm()
        item_formset = EventItemInlineFormSet(prefix='items')
    
    context = { 
        'event_form': event_form, 
        'item_formset': item_formset, 
        'page_title': 'Add New Event / Logistics Service', 
    }
    return render(request, 'bookings/event_form.html', context)


@transaction.atomic
def event_edit_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        event_form = EventForm(request.POST, instance=event)
        # Initialize item_formset; it will be processed based on the 'is_logistics_only_service' flag
        item_formset = EventItemInlineFormSet(request.POST, instance=event, prefix='items')

        if event_form.is_valid():
            event_instance = event_form.save(commit=False) # Don't save yet, need to check is_logistics_only_service
            # Update project manager fields
            project_manager = event_form.cleaned_data.get('project_manager')
            event_instance.project_manager = project_manager
            if project_manager:
                event_instance.project_manager_name = f"{project_manager.first_name} {project_manager.last_name}"
            else:
                event_instance.project_manager_name = ""
            is_logistics_service = event_form.cleaned_data.get('is_logistics_only_service', False)
            event_instance.is_logistics_only_service = is_logistics_service # Update the instance

            if is_logistics_service:
                try:
                    event_instance.save() # Save changes to the Event model
                    # If it's now a logistics service, delete any associated items
                    EventItem.objects.filter(booking=event_instance).delete()
                    messages.success(request, f"Logistics Service '{event_instance.event_name}' updated successfully! Associated items (if any) have been removed.")
                    return redirect(event_instance.get_absolute_url())
                except Exception as e:
                    messages.error(request, f"An error occurred while updating the logistics service: {e}")
            else:
                # For regular events, validate and process item_formset
                if item_formset.is_valid():
                    start_date = event_form.cleaned_data.get('start_date')
                    end_date = event_form.cleaned_data.get('end_date')
                    all_items_available = True
                    availability_errors = []

                    has_items_to_book = any(form.has_changed() and not form.cleaned_data.get('DELETE', False) for form in item_formset)

                    if has_items_to_book:
                        for form in item_formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                item = form.cleaned_data.get('item')
                                quantity = form.cleaned_data.get('quantity')
                                if item and quantity and start_date and end_date:
                                    # Using initial_quantity for now as per inventory/models.py
                                    if not item.is_available(quantity, start_date, end_date, exclude_event_pk=event.pk):
                                        all_items_available = False
                                        # Accessing available_quantity property from Item model
                                        error_msg = f"Not enough '{item.name}' available ({item.available_quantity} currently free) for the period [{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}], considering other bookings."
                                        form.add_error('item', error_msg)
                                        availability_errors.append(error_msg)
                                elif form.has_changed() and not (item and quantity) and not form.cleaned_data.get('DELETE', False):
                                    form.add_error(None, "Both item and quantity are required if using this row and not deleting.")
                                    all_items_available = False
                    
                    if all_items_available:
                        try:
                            event_instance.save() 
                            item_formset.instance = event_instance 
                            item_formset.save() 
                            messages.success(request, f"Event Booking '{event_instance.event_name}' updated successfully!")
                            return redirect(event_instance.get_absolute_url())
                        except Exception as e:
                            messages.error(request, f"An error occurred while updating the booking: {e}")
                    elif availability_errors:
                         messages.error(request, "Could not update booking. Please correct the item availability errors below.")
                    else: # Other item_formset errors not related to availability
                        messages.error(request, "Could not update booking. Please ensure all added item rows are complete or marked for deletion.")
                else: # item_formset is not valid
                    messages.error(request, "Please correct the item booking errors below.")
        else: # event_form is not valid
            messages.error(request, "Please correct the event details errors below.")
            # Re-initialize item_formset with instance data if event_form is invalid to show current items
            item_formset = EventItemInlineFormSet(instance=event, prefix='items')

    else: # GET request
        event_form = EventForm(instance=event)
        item_formset = EventItemInlineFormSet(instance=event, prefix='items')
    
    context = { 
        'event_form': event_form, 
        'item_formset': item_formset, 
        'event': event, 
        'page_title': f'Edit {"Logistics Service" if event.is_logistics_only_service else "Event"}: {event.event_name}', 
    }
    return render(request, 'bookings/event_form.html', context)

@transaction.atomic
def rental_add_view(request):
    if request.method == 'POST':
        rental_form = RentalForm(request.POST)
        item_formset = RentalItemInlineFormSet(request.POST, prefix='items')
        if rental_form.is_valid() and item_formset.is_valid():
            start_date = rental_form.cleaned_data.get('start_date')
            end_date = rental_form.cleaned_data.get('end_date')
            all_items_available = True
            
            has_items_to_book = any(form.has_changed() and not form.cleaned_data.get('DELETE', False) for form in item_formset)
            if has_items_to_book:
                for form in item_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        item = form.cleaned_data.get('item')
                        quantity = form.cleaned_data.get('quantity')
                        if item and quantity and start_date and end_date:
                            if not item.is_available(quantity, start_date, end_date):
                                all_items_available = False
                                error_msg = f"Not enough '{item.name}' available ({item.available_quantity} currently free) for the selected dates [{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}]."
                                form.add_error('item', error_msg)
                        elif not item and not quantity and form.has_changed(): # Empty touched row
                            form.add_error(None, "Please select an item and quantity, or leave the row empty if not needed.")
                            all_items_available = False
                        elif not (item and quantity) and form.has_changed(): # Incomplete touched row
                            form.add_error(None, "Both item and quantity are required if using this row.")
                            all_items_available = False
            
            if all_items_available:
                try:
                    rental = rental_form.save(commit=False)

                    # Set status
                    rental.status = Rental.StatusChoices.BOOKED

                    # Set project_manager and project_manager_name
                    project_manager = rental_form.cleaned_data.get('project_manager')
                    rental.project_manager = project_manager
                    if project_manager:
                        rental.project_manager_name = f"{project_manager.first_name} {project_manager.last_name}"
                    else:
                        rental.project_manager_name = ""

                    # Save the rental
                    rental.save()
                    item_formset.instance = rental
                    item_formset.save()
                    messages.success(request, f"Rental Booking '{rental.reference_number}' created successfully!")
                    return redirect(rental.get_absolute_url()) # Use get_absolute_url
                except Exception as e: messages.error(request, f"An error occurred while saving: {e}")
            else: messages.error(request, "Could not create rental. Please correct item availability or form errors.")
        else: messages.error(request, "Please correct the form errors below.")
    else: # GET request
        rental_form = RentalForm()
        item_formset = RentalItemInlineFormSet(prefix='items')
    
    context = { 
        'rental_form': rental_form, 
        'item_formset': item_formset, 
        'page_title': 'Add New Rental Booking', 
    }
    return render(request, 'bookings/rental_form.html', context)


@transaction.atomic
def rental_edit_view(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    if request.method == 'POST':
        rental_form = RentalForm(request.POST, instance=rental)
        item_formset = RentalItemInlineFormSet(request.POST, instance=rental, prefix='items')
        if rental_form.is_valid() and item_formset.is_valid():
            start_date = rental_form.cleaned_data.get('start_date')
            end_date = rental_form.cleaned_data.get('end_date')
            all_items_available = True
            availability_errors = []

            has_items_to_book = any(form.has_changed() and not form.cleaned_data.get('DELETE', False) for form in item_formset)
            if has_items_to_book:
                for form in item_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        item = form.cleaned_data.get('item')
                        quantity = form.cleaned_data.get('quantity')
                        if item and quantity and start_date and end_date:
                            if not item.is_available(quantity, start_date, end_date, exclude_rental_pk=rental.pk):
                                all_items_available = False
                                error_msg = f"Not enough '{item.name}' available ({item.available_quantity} currently free) for the period [{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}], considering other bookings."
                                form.add_error('item', error_msg)
                                availability_errors.append(error_msg)
                        elif not item and not quantity and form.has_changed():
                            form.add_error(None, "Please select an item and quantity, or mark for deletion.")
                            all_items_available = False
                        elif not (item and quantity) and form.has_changed():
                            form.add_error(None, "Both item and quantity are required if using this row.")
                            all_items_available = False
            
            if all_items_available:
                try:
                    rental_instance = rental_form.save(commit=False)
                    project_manager = rental_form.cleaned_data.get('project_manager')

                    rental_instance.project_manager = project_manager
                    if project_manager:
                        rental_instance.project_manager_name = f"{project_manager.first_name} {project_manager.last_name}"
                    else:
                        rental_instance.project_manager_name = ""

                    rental_instance.save()
                    item_formset.save()
                    messages.success(request, f"Rental Booking '{rental.reference_number}' updated successfully!")
                    return redirect(rental.get_absolute_url()) # Use get_absolute_url
                except Exception as e: messages.error(request, f"An error occurred while updating the booking: {e}")
            elif availability_errors:
                 messages.error(request, "Could not update booking. Please correct the item availability errors below.")
            else:
                messages.error(request, "Could not update booking. Please ensure all added item rows are complete or marked for deletion.")
        else:
             messages.error(request, "Please correct the form errors below.")
    else: # GET request
        rental_form = RentalForm(instance=rental)
        item_formset = RentalItemInlineFormSet(instance=rental, prefix='items')
    
    context = { 
        'rental_form': rental_form, 
        'item_formset': item_formset, 
        'rental': rental, 
        'page_title': f'Edit Rental Booking: {rental.reference_number}', 
    }
    return render(request, 'bookings/rental_form.html', context)

# --- Detail Views ---
def event_detail_view(request, event_id):
    event = get_object_or_404( Event.objects.select_related('client').prefetch_related('items__item__category'), pk=event_id ) # Added item__category
    context = { 'event': event, 'page_title': f'{"Logistics Service" if event.is_logistics_only_service else "Event"} Details: {event.event_name or event.reference_number}' }
    return render(request, 'bookings/event_detail.html', context)

def rental_detail_view(request, rental_id):
    rental = get_object_or_404( Rental.objects.select_related('client').prefetch_related('items__item__category'), pk=rental_id ) # Added item__category
    context = { 'rental': rental, 'page_title': f'Rental Details: {rental.reference_number}' }
    return render(request, 'bookings/rental_detail.html', context)

# --- PDF Generation Views ---
def delivery_note_pdf_view(request, booking_type, booking_id): # This view is now for both Event (non-logistics) and Rental
    booking = None
    try:
        if booking_type == 'event': 
            booking = get_object_or_404( Event.objects.select_related('client').prefetch_related('items__item'), pk=booking_id )
            if booking.is_logistics_only_service: # Should not happen if URLs are correct
                messages.error(request, "Delivery Notes are not applicable for Logistics Services. Use Waybill.")
                return redirect(booking.get_absolute_url())
        elif booking_type == 'rental': 
            booking = get_object_or_404( Rental.objects.select_related('client').prefetch_related('items__item'), pk=booking_id )
        else: 
            raise Http404("Invalid booking type specified for Delivery Note.")
        return generate_delivery_note_pdf(booking)
    except Http404 as e: 
        messages.error(request, str(e))
        return redirect('dashboard:dashboard_main') 
    except Exception as e:
        print(f"Error generating Delivery Note PDF: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred generating the Delivery Note PDF. Please check server logs.")
        if booking:
            if isinstance(booking, Event): return redirect('bookings:event_detail', event_id=booking_id)
            if isinstance(booking, Rental): return redirect('bookings:rental_detail', rental_id=booking_id)
        return redirect('dashboard:dashboard_main')

# NEW: Logistics Waybill PDF View
def logistics_waybill_pdf_view(request, event_id):
    event = get_object_or_404(Event.objects.select_related('client'), pk=event_id)
    if not event.is_logistics_only_service:
        messages.error(request, "Waybill is only for Logistics Services.")
        return redirect(event.get_absolute_url())
    
    # We will create generate_logistics_waybill_pdf in utils.py in the next step
    from .utils import generate_logistics_waybill_pdf # Import it here
    try:
        return generate_logistics_waybill_pdf(event)
    except Exception as e:
        print(f"Error generating Logistics Waybill PDF: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred generating the Logistics Waybill PDF: {e}. Please check server logs.")
        return redirect('bookings:event_detail', event_id=event_id)


def receipt_pdf_view(request, booking_type, booking_id):
    booking = None
    try:
        if booking_type == 'event': 
            booking = get_object_or_404( Event.objects.select_related('client').prefetch_related('items__item'), pk=booking_id )
        elif booking_type == 'rental': 
            booking = get_object_or_404( Rental.objects.select_related('client').prefetch_related('items__item'), pk=booking_id )
        else: 
            raise Http404("Invalid booking type specified for Receipt.")
        return generate_receipt_pdf(booking) 
    except Http404 as e: 
        messages.error(request, str(e))
        return redirect('dashboard:dashboard_main')
    except Exception as e:
        print(f"Error generating Receipt PDF: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred generating the Receipt PDF: {e}. Please check server logs.")
        if booking:
            if isinstance(booking, Event): return redirect('bookings:event_detail', event_id=booking_id)
            if isinstance(booking, Rental): return redirect('bookings:rental_detail', rental_id=booking_id)
        return redirect('dashboard:dashboard_main')

# --- Delete Views ---
def event_delete_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        try: 
            event_ref = event.reference_number
            event_name = event.event_name
            event.delete()
            messages.success(request, f"Booking '{event_name}' ({event_ref}) deleted successfully!")
            return redirect('bookings:event_list')
        except ProtectedError: # Catch ProtectedError specifically
             messages.error(request, f"Cannot delete '{event.event_name}'. It is linked to other records (e.g., items). Please remove these links first.")
             return redirect('bookings:event_detail', event_id=event_id)
        except Exception as e: 
            messages.error(request, f"An error occurred while deleting the booking: {e}")
            return redirect('bookings:event_detail', event_id=event_id)
    context = { 
        'event': event, 
        'page_title': f'Confirm Delete: {event.event_name or event.reference_number}' 
    }
    return render(request, 'bookings/event_confirm_delete.html', context)

def rental_delete_view(request, rental_id):
    rental = get_object_or_404(Rental, pk=rental_id)
    if request.method == 'POST':
        try: 
            rental_ref = rental.reference_number
            rental.delete()
            messages.success(request, f"Rental Booking '{rental_ref}' deleted successfully!")
            return redirect('bookings:rental_list')
        except ProtectedError:
            messages.error(request, f"Cannot delete Rental '{rental.reference_number}'. It is linked to other records (e.g., items). Please remove these links first.")
            return redirect('bookings:rental_detail', rental_id=rental_id)
        except Exception as e: 
            messages.error(request, f"An error occurred while deleting the rental booking: {e}")
            return redirect('bookings:rental_detail', rental_id=rental_id)
    context = { 
        'rental': rental, 
        'page_title': f'Confirm Delete Rental: {rental.reference_number}' 
    }
    return render(request, 'bookings/rental_confirm_delete.html', context)