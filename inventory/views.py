# clavis_event_inventory/inventory/views.py
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum, ProtectedError 
from .models import Item, Category, ItemImage
from .forms import AvailabilityCheckForm, ItemForm
from bookings.models import EventItem, RentalItem 
from .utils import generate_master_inventory_excel, generate_master_inventory_pdf, generate_master_inventory_docx
from django.utils import timezone # Make sure timezone is imported
import datetime # Make sure datetime is imported
from .utils import generate_barcode_base64 #barcode imported
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# --- Item List/Detail Views ---
# def item_list_view(request):
#     search_query = request.GET.get('q', '')
#     selected_category_id = request.GET.get('category', '')
#     selected_item_source = request.GET.get('item_source', '')

#     queryset = Item.objects.all().select_related('category', 'supplier')

#     if selected_category_id:
#         try:
#             category_id_int = int(selected_category_id)
#             queryset = queryset.filter(category_id=category_id_int)
#         except (ValueError, TypeError):
#             selected_category_id = '' 
    
#     if selected_item_source:
#         queryset = queryset.filter(item_source=selected_item_source)

#     if search_query:
#         queryset = queryset.filter(
#             Q(name__icontains=search_query) | 
#             Q(sku__icontains=search_query) | 
#             Q(description__icontains=search_query) | 
#             Q(category__name__icontains=search_query)
#         ).distinct()
    
#     categories = Category.objects.all().order_by('name')
#     # items = queryset.order_by('category__name', 'name') # This will be done in template if needed or after pagination

#     items = queryset.order_by('category__name', 'name')
#     # Inject barcode image into each item
#     for item in items:
#         item.barcode_image = generate_barcode_base64(item.sku)
        
#     context = {
#         'items': items,
#         'categories': categories,
#         'selected_category_id': selected_category_id,
#         'search_query': search_query,
#         'page_title': 'Inventory Items',
#         'item_source_choices': Item.ItemSourceType.choices,
#         'selected_item_source': selected_item_source,
#     }

#     # context = { 
#     #     'items': queryset.order_by('category__name', 'name'), # Apply ordering here
#     #     'categories': categories, 
#     #     'selected_category_id': selected_category_id, 
#     #     'search_query': search_query, 
#     #     'page_title': 'Inventory Items',
#     #     'item_source_choices': Item.ItemSourceType.choices, 
#     #     'selected_item_source': selected_item_source,     
#     # }
#     return render(request, 'inventory/item_list.html', context)
def item_list_view(request):
    search_query = request.GET.get('q', '')
    selected_category_id = request.GET.get('category', '')
    selected_item_source = request.GET.get('item_source', '')

    queryset = Item.objects.all().select_related('category', 'supplier')

    if selected_category_id:
        try:
            category_id_int = int(selected_category_id)
            queryset = queryset.filter(category_id=category_id_int)
        except (ValueError, TypeError):
            selected_category_id = '' 

    if selected_item_source:
        queryset = queryset.filter(item_source=selected_item_source)

    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) | 
            Q(sku__icontains=search_query) | 
            Q(description__icontains=search_query) | 
            Q(category__name__icontains=search_query)
        ).distinct()

    queryset = queryset.order_by('category__name', 'name')
    
    # Pagination logic
    paginator = Paginator(queryset, 10)  # Show 10 items per page
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    # Inject barcode
    for item in items:
        item.barcode_image = generate_barcode_base64(item.sku)

    categories = Category.objects.all().order_by('name')

    context = {
        'items': items,
        'categories': categories,
        'selected_category_id': selected_category_id,
        'search_query': search_query,
        'page_title': 'Inventory Items',
        'item_source_choices': Item.ItemSourceType.choices,
        'selected_item_source': selected_item_source,
        'page_obj': items  # For template pagination controls
    }

    return render(request, 'inventory/item_list.html', context)

def print_barcode_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    from .utils import generate_barcode_base64
    barcode_image = generate_barcode_base64(item.sku)
    return render(request, 'inventory/print_barcode.html', {
        'item': item,
        'barcode_image': barcode_image,
    })


def item_detail_view(request, item_id):
    item = get_object_or_404(Item.objects.select_related('category', 'supplier'), pk=item_id)
    context = { 
        'item': item, 
        'page_title': f"Item Details: {item.name}", 
    }
    return render(request, 'inventory/item_detail.html', context)

# --- Item Add/Edit Views ---
def item_add_view(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()

            # Handle multiple uploaded files
            for image_file in request.FILES.getlist('images'):
                ItemImage.objects.create(item=item, image=image_file)

            messages.success(request, f"Item '{item.name}' added successfully!")
            return redirect('inventory:item_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ItemForm()

    context = {
        'form': form,
        'page_title': 'Add New Inventory Item'
    }
    return render(request, 'inventory/item_form.html', context)

def item_edit_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()

            # Handle multiple uploaded files
            for image_file in request.FILES.getlist('images'):
                ItemImage.objects.create(item=item, image=image_file)

            messages.success(request, f"Item '{item.name}' updated successfully!")
            return redirect('inventory:item_detail', item_id=item.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'existing_images': item.extra_images.all(),
        'page_title': f'Edit Item: {item.name}'
    }
    return render(request, 'inventory/item_form.html', context)

def item_delete_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    has_event_bookings = EventItem.objects.filter(item=item).exists()
    has_rental_bookings = RentalItem.objects.filter(item=item).exists()
    is_protected = has_event_bookings or has_rental_bookings

    if request.method == 'POST':
        if is_protected:
            messages.error(request, f"Cannot delete item '{item.name}' because it is associated with existing or past bookings.")
            return redirect('inventory:item_detail', item_id=item.id)
        else:
            try:
                item_name = item.name
                item.delete() 
                messages.success(request, f"Item '{item_name}' deleted successfully!")
                return redirect('inventory:item_list')
            except ProtectedError: 
                messages.error(request, f"Cannot delete item '{item.name}' due to database protection rules (likely linked to bookings).")
                return redirect('inventory:item_detail', item_id=item.id)
            except Exception as e:
                messages.error(request, f"An error occurred while deleting the item: {e}")
                return redirect('inventory:item_detail', item_id=item.id)

    context = {
        'item': item,
        'is_protected': is_protected, 
        'page_title': f'Confirm Delete Item: {item.name}'
    }
    return render(request, 'inventory/item_confirm_delete.html', context)

def delete_item_image(request, image_id):
    image = get_object_or_404(ItemImage, pk=image_id)
    item_id = image.item.id

    if request.method == 'GET' and request.GET.get('confirm') == '1':
        # Delete file from media folder
        if image.image and os.path.isfile(image.image.path):
            os.remove(image.image.path)
        image.delete()
        messages.success(request, "Image deleted successfully.")

    return redirect('inventory:item_edit', item_id=item_id)
# --- Report Views ---
def master_inventory_report(request):
    format_param = request.GET.get('format') 
    items = Item.objects.all().select_related('category', 'supplier').order_by('category', 'name')
    if format_param == 'xlsx': return generate_master_inventory_excel(items)
    elif format_param == 'pdf': return generate_master_inventory_pdf(items)
    elif format_param == 'docx': return generate_master_inventory_docx(items)
    else:
        context = { 'items': items, 'page_title': 'Master Inventory Report', }
        return render(request, 'inventory/master_inventory_report.html', context)

def availability_report_view(request):
    form = AvailabilityCheckForm(request.GET or None)
    overlapping_events = None
    overlapping_rentals = None
    selected_item_obj = None
    start_date_val = None # This will be a date object
    end_date_val = None   # This will be a date object

    if form.is_valid():
        selected_item_obj = form.cleaned_data['item']
        start_date_val = form.cleaned_data['start_date'] # This is a datetime.date
        end_date_val = form.cleaned_data['end_date']     # This is a datetime.date

        # --- MODIFICATION: Make datetimes timezone-aware ---
        # Combine date objects with min/max times and make them timezone-aware
        start_datetime_aware = timezone.make_aware(datetime.datetime.combine(start_date_val, datetime.time.min))
        end_datetime_aware = timezone.make_aware(datetime.datetime.combine(end_date_val, datetime.time.max))
        # --- END MODIFICATION ---

        # Use the aware datetime objects in your filters
        overlapping_events = EventItem.objects.filter(
            item=selected_item_obj,
            booking__end_date__gte=start_datetime_aware, # Use aware datetime
            booking__start_date__lte=end_datetime_aware   # Use aware datetime
        ).select_related('booking__client', 'item').order_by('booking__start_date')
        
        overlapping_rentals = RentalItem.objects.filter(
            item=selected_item_obj,
            booking__end_date__gte=start_datetime_aware, # Use aware datetime
            booking__start_date__lte=end_datetime_aware   # Use aware datetime
        ).select_related('booking__client', 'item').order_by('booking__start_date')

    context = { 
        'form': form, 
        'selected_item': selected_item_obj, # Changed from selected_item_obj for consistency with template
        'start_date': start_date_val,       # Pass original date objects for display
        'end_date': end_date_val,         # Pass original date objects for display
        'overlapping_events': overlapping_events, 
        'overlapping_rentals': overlapping_rentals, 
        'page_title': 'Inventory Availability Report' 
    }
    return render(request, 'inventory/availability_report.html', context)