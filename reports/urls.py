# clavis_event_inventory/reports/urls.py
from django.urls import path
from . import views # We created views.py in a previous step

app_name = 'reports'

urlpatterns = [
    # path('items-out/', views.items_out_report, name='report_items_out'), # Keep if you re-added this report
    
    # NEW: URL for the Monthly Summary Report
    path('monthly-summary/', views.monthly_summary_report_view, name='report_monthly_summary'),
    
    # Add other report URLs here later
]
