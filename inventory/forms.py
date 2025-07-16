# clavis_event_inventory/inventory/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Item, Category
from suppliers.models import Supplier  # Import Supplier model
import datetime

class AvailabilityCheckForm(forms.Form):
    """Form to select an item and date range for checking availability."""
    item = forms.ModelChoiceField(
        queryset=Item.objects.order_by('name'),
        label="Select Item",
        widget=forms.Select(attrs={'class': 'form-select'}) 
    )
    start_date = forms.DateField(
        label="Start Date",
        required=True, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label="End Date",
        required=True, 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            raise ValidationError("End date cannot be before the start date.")
        return cleaned_data

# Form for Adding/Editing Inventory Items
class ItemForm(forms.ModelForm):
    """Form for creating and editing inventory items."""
    category = forms.ModelChoiceField(
        queryset=Category.objects.order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}) 
    )

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}) 
    )
    image1 = forms.ImageField(
        required=True,
        help_text="Primary image is required.",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    image2 = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    # === NEW Item Source Field ===
    item_source = forms.ChoiceField(
        choices=Item.ItemSourceType.choices,
        label="Item Source",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Specify if this item is owned by the company or supplied by a client for an event."
    )
    # === END NEW Item Source Field ===

    rent_price_per_day = forms.DecimalField(
        max_digits=10, decimal_places=2,
        required=False,
        label="Rent Price/Day (BHD)",
        help_text="Daily rental charge (leave blank if N/A, e.g., for client-supplied items).",
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'})
    )

    class Meta:
        model = Item
        fields = [
            'name', 'description',
            'item_source',  # ADDED item_source
            'category', 'storage_location',
            'initial_quantity',
            'depth', 'width', 'height',
            'dimension_unit', 'image1', 'image2', 'purchase_price',
            'rent_price_per_day', 'supplier'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'storage_location': forms.TextInput(attrs={'class': 'form-control'}),
            'initial_quantity': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'depth': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'width': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'dimension_unit': forms.Select(attrs={'class': 'form-select'}),
            'purchase_price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }
        labels = {
            'depth': 'Depth', 'width': 'Width', 'height': 'Height',
            'item_source': 'Item Source/Ownership',
        }
        help_texts = {
            'depth': 'Depth dimension.', 'width': 'Width dimension.', 'height': 'Height dimension.',
            'dimension_unit': 'Units for Depth x Width x Height.',
            'item_source': 'Select if this item is owned by the company or supplied by a client.'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.item_source == Item.ItemSourceType.CLIENT_SUPPLIED:
            self.fields['rent_price_per_day'].required = False
        elif not self.instance or not self.instance.pk:
            if 'rent_price_per_day' in self.fields and self.fields['rent_price_per_day'].required:
                self.fields['rent_price_per_day'].required = False

        self.fields['purchase_price'].required = False
        self.fields['supplier'].required = False
