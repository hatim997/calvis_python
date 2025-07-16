# clavis_event_inventory/clients/forms.py

from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    """Form for adding or editing a Client."""
    class Meta:
        model = Client
        fields = [
            'name', 'company_name', 'contact_person', 'email', 'phone', 'address',
        ]
        # Ensure all fields use Bootstrap classes
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }