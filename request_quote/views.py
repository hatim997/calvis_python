from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from django.http import Http404

from .models import QuoteRequest, QuoteRequestItem
from .forms import QuoteRequestForm, QuoteRequestItemInlineFormSet
from clients.models import Client
from inventory.models import Item
from django import forms

from django.contrib.auth.decorators import login_required

from .utils import generate_quote_pdf

# --- List View ---
def quote_list_view(request):
    if request.user.is_superuser:
        quotes = QuoteRequest.objects.all().select_related('project_manager','client')
    else:
        quotes = QuoteRequest.objects.filter(project_manager=request.user).select_related('project_manager','client')

    quotes = quotes.order_by('-event_start_date')

    context = {
        'quotes': quotes,
        'page_title': 'Quote Requests'
    }
    return render(request, 'request_quote/quote_list.html', context)


# --- Add View ---
@transaction.atomic
def quote_add_view(request):
    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        formset = QuoteRequestItemInlineFormSet(request.POST, prefix='items')

        # Set project_manager to current user if not superuser
        if not request.user.is_superuser:
            form.fields['project_manager'].widget = forms.HiddenInput()
            form.fields['project_manager'].initial = request.user

        if form.is_valid() and formset.is_valid():
            try:
                quote = form.save(commit=False)
                if not request.user.is_superuser:
                    quote.project_manager = request.user
                quote.save()
                formset.instance = quote
                formset.save()
                messages.success(request, f"Quote Request '{quote.event_title}' created successfully.")
                return redirect('request_quote:quote_detail', quote_id=quote.pk)
            except Exception as e:
                messages.error(request, f"An error occurred while saving the quote request: {e}")
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = QuoteRequestForm()
        formset = QuoteRequestItemInlineFormSet(prefix='items')

        # Again, hide field if user is not superuser
        if not request.user.is_superuser:
            form.fields['project_manager'].widget = forms.HiddenInput()
            form.fields['project_manager'].initial = request.user

    return render(request, 'request_quote/quote_form.html', {
        'quote_form': form,
        'item_formset': formset,
        'page_title': 'Create Quote Request',
        'is_superuser': request.user.is_superuser,  # <-- send flag to template
    })


# --- Edit View ---
@transaction.atomic
def quote_edit_view(request, quote_id):
    quote = get_object_or_404(QuoteRequest, pk=quote_id)

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, instance=quote)
        formset = QuoteRequestItemInlineFormSet(request.POST, instance=quote, prefix='items')

        # Hide project_manager field for non-superusers
        if not request.user.is_superuser:
            form.fields['project_manager'].widget = forms.HiddenInput()

        if form.is_valid() and formset.is_valid():
            try:
                updated_quote = form.save(commit=False)
                if not request.user.is_superuser:
                    updated_quote.project_manager = request.user  # ensure data integrity
                updated_quote.save()
                formset.instance = updated_quote
                formset.save()
                messages.success(request, f"Quote Request '{updated_quote.event_title}' updated successfully.")
                return redirect('request_quote:quote_detail', quote_id=updated_quote.pk)
            except Exception as e:
                messages.error(request, f"An error occurred while updating the quote request: {e}")
        else:
            messages.error(request, "Please correct the form errors.")
    else:
        form = QuoteRequestForm(instance=quote)
        formset = QuoteRequestItemInlineFormSet(instance=quote, prefix='items')

        if not request.user.is_superuser:
            form.fields['project_manager'].widget = forms.HiddenInput()

    return render(request, 'request_quote/quote_form.html', {
        'quote_form': form,
        'item_formset': formset,
        'quote_request': quote,
        'page_title': f"Edit Quote Request: {quote.event_title}",
        'is_superuser': request.user.is_superuser,
    })
    
# --- Detail View ---
def quote_detail_view(request, quote_id):
    quote = get_object_or_404(
        QuoteRequest.objects.select_related('project_manager','client').prefetch_related('items__item'),
        pk=quote_id
    )
    context = {
        'quote': quote,
        'page_title': f"Quote Request Details: {quote.event_title or quote.reference_number}"
    }
    return render(request, 'request_quote/quote_detail.html', context)

def quote_pdf_view(request, quote_id):
    try:
        # Retrieve QuoteRequest with related project_manager and items
        quote = get_object_or_404(
            QuoteRequest.objects.select_related('project_manager').prefetch_related('items__item'),
            pk=quote_id
        )
        return generate_quote_pdf(quote)
    except Http404:
        messages.error(request, "Quote request not found.")
        return redirect('dashboard:dashboard_main')
    except Exception as e:
        print(f"Error generating Quote PDF: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, "An error occurred generating the Quote PDF. Please check server logs.")
        return redirect('request_quote:quote_detail', quote_id=quote_id)
    
# --- Delete View ---
def quote_delete_view(request, quote_id):
    quote = get_object_or_404(QuoteRequest, pk=quote_id)
    quote_ref = quote.reference_number
    event_title = quote.event_title
    quote.delete()
    messages.success(request, f"Quote Request '{event_title}' ({quote_ref}) deleted successfully!")
    return redirect('request_quote:quote_list')