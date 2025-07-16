# clavis_event_inventory/clients/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import ProtectedError # Import ProtectedError
from .models import Client
from .forms import ClientForm

def client_list_view(request):
    # ... (list view as before) ...
    clients = Client.objects.all().order_by('company_name', 'name')
    context = { 'clients': clients, 'page_title': 'Clients' }
    return render(request, 'clients/client_list.html', context)

def client_detail_view(request, client_id):
    # ... (detail view as before) ...
    client = get_object_or_404(Client, pk=client_id)
    event_history = client.events.all().order_by('-start_date')
    rental_history = client.rentals.all().order_by('-start_date')
    context = { 'client': client, 'event_history': event_history, 'rental_history': rental_history, 'page_title': f"Client Details: {client}", }
    return render(request, 'clients/client_detail.html', context)

def client_add_view(request):
    # ... (add view as before) ...
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Client '{client.name}' added successfully!")
            return redirect('clients:client_list')
        else: messages.error(request, "Please correct the errors below.")
    else: form = ClientForm()
    context = { 'form': form, 'page_title': 'Add New Client' }
    return render(request, 'clients/client_form.html', context)

def client_edit_view(request, client_id):
    # ... (edit view as before) ...
    client = get_object_or_404(Client, pk=client_id)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client '{client.name}' updated successfully!")
            return redirect('clients:client_detail', client_id=client.id)
        else: messages.error(request, "Please correct the errors below.")
    else: form = ClientForm(instance=client)
    context = { 'form': form, 'client': client, 'page_title': f'Edit Client: {client.name}' }
    return render(request, 'clients/client_form.html', context)

# NEW: Client Delete View
def client_delete_view(request, client_id):
    """Handles deletion of a client after confirmation."""
    client = get_object_or_404(Client, pk=client_id)
    has_bookings = client.events.exists() or client.rentals.exists() # Check related bookings

    if request.method == 'POST':
        # Confirmation received
        if has_bookings:
            # Should not happen if button is hidden, but double-check
            messages.error(request, f"Cannot delete client '{client.name}' because they have associated bookings. Please reassign or delete bookings first.")
            return redirect('clients:client_detail', client_id=client.id)
        else:
            try:
                client_name = client.name # Get name before deleting
                client.delete()
                messages.success(request, f"Client '{client_name}' deleted successfully!")
                return redirect('clients:client_list')
            except ProtectedError: # Should be caught by has_bookings check, but good failsafe
                 messages.error(request, f"Cannot delete client '{client.name}' due to existing related records (likely bookings).")
                 return redirect('clients:client_detail', client_id=client.id)
            except Exception as e:
                 messages.error(request, f"An error occurred while deleting the client: {e}")
                 return redirect('clients:client_detail', client_id=client.id)

    # GET request: Show confirmation page
    context = {
        'client': client,
        'has_bookings': has_bookings, # Pass flag to template
        'page_title': f'Confirm Delete Client: {client.name}'
    }
    return render(request, 'clients/client_confirm_delete.html', context)