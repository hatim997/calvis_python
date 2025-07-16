# clavis_event_inventory/dashboard/urls.py

from django.urls import path
from . import views # Import views from the current directory

# app_name = 'dashboard' # REMOVED/COMMENTED OUT previously to resolve W005 warning

urlpatterns = [
    # Map the root URL of this app ('/' relative to '/dashboard/' or '')
    # to the dashboard_view function.
    path('', views.dashboard_view, name='dashboard_main'),
]