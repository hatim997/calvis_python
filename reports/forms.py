# clavis_event_inventory/reports/forms.py

from django import forms
from django.utils import timezone # To get the current year/month
import datetime # To work with dates if needed for validation

class MonthlyReportFilterForm(forms.Form):
    """
    Form for selecting the year and month for the monthly summary report.
    """
    # Dynamically create year choices for the last 5 years up to the current year
    current_year = timezone.now().year
    # Create a list of tuples: (value, display_name)
    # Example: [(2025, '2025'), (2024, '2024'), ..., (2021, '2021')]
    YEAR_CHOICES = [("all", "All Years")] + [(year, str(year)) for year in range(current_year - 4, current_year + 1)]
    YEAR_CHOICES.reverse() # Show the most recent year first in the dropdown

    # Define month choices as a list of tuples: (month_number, month_name)
    MONTH_CHOICES = [("all", "All Months")] + [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]


    year = forms.ChoiceField(
        label="Year",
        choices=YEAR_CHOICES,
        initial=current_year, # Default to the current year
        widget=forms.Select(attrs={'class': 'form-select'}) # Apply Bootstrap class
    )
    month = forms.ChoiceField(
        label="Month",
        choices=MONTH_CHOICES,
        initial=timezone.now().month, # Default to the current month
        widget=forms.Select(attrs={'class': 'form-select'}) # Apply Bootstrap class
    )

    def clean_year(self):
        """
        Custom validation to ensure the year is an integer.
        This is generally handled well by ChoiceField, but explicit conversion is good practice.
        """
        year = self.cleaned_data.get('year')
        if year == "all":
            return "all"
        try:
            return int(year)
        except (ValueError, TypeError):
            # This error shouldn't typically be reached with a ChoiceField
            # if choices are correctly set up as numbers.
            raise forms.ValidationError("Invalid year selected.")

    def clean_month(self):
        """
        Custom validation to ensure the month is an integer.
        """
        month = self.cleaned_data.get('month')
        if month == "all":
            return "all"
        try:
            return int(month)
        except (ValueError, TypeError):
            raise forms.ValidationError("Invalid month selected.")