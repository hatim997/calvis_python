from django import forms
from django.forms import inlineformset_factory
from .models import QuoteRequest, QuoteRequestItem
from clients.models import Client
from inventory.models import Item
from django.contrib.auth.models import User


class QuoteRequestForm(forms.ModelForm):
    """Form for creating or editing a Quote Request."""

    event_title = forms.CharField(
        label="Event Title",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Gala Night 2025'})
    )
    event_start_date = forms.DateTimeField(
        label="Start Date & Time",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    event_end_date = forms.DateTimeField(
        label="End Date & Time",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    setup_installation_datetime = forms.DateTimeField(
        label="Setup Installation Date & Time",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    setup_removal_datetime = forms.DateTimeField(
        label="Setup Removal Date & Time",
        widget=forms.DateTimeInput(attrs={'class': 'form-control flatpickr-datetime'})
    )
    project_manager = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Project Manager"
    )
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Client"
    )
    # client_name = forms.CharField(
    #     label="Client Name",
    #     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ABC Events'})
    # )
    subcontractors = forms.CharField(
        required=False,
        label="Subcontractors (if any)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    delivery_note_signed_from = forms.CharField(
        required=False,
        label="Delivery Note To Be Signed From",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    project_manager_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Notes from Project Manager"
    )

    class Meta:
        model = QuoteRequest
        fields = [
            'client', 'event_title', 'event_start_date', 'event_end_date',
            'setup_installation_datetime', 'setup_removal_datetime',
            'project_manager', 'subcontractors',
            'delivery_note_signed_from', 'project_manager_notes'
        ]



class QuoteRequestItemForm(forms.ModelForm):
    """Form for individual item in the quote request."""
    item = forms.ModelChoiceField(
        queryset=Item.objects.filter(
            item_source=Item.ItemSourceType.OWNED,
            initial_quantity__gt=0
        ).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select item-select'})
    )
    quantity = forms.IntegerField(
        min_value=1, initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control quantity-input'})
    )

    class Meta:
        model = QuoteRequestItem
        fields = ['item', 'quantity']


QuoteRequestItemInlineFormSet = inlineformset_factory(
    QuoteRequest, QuoteRequestItem, form=QuoteRequestItemForm,
    extra=1, can_delete=True, fk_name='booking'
)
