# clavis_event_inventory/config/urls.py

"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/stable/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include # Make sure include is imported
from django.conf import settings # To access settings like DEBUG, MEDIA_URL, MEDIA_ROOT
from django.conf.urls.static import static # To serve media files during development
from django.contrib.auth import views as auth_views
from users.views import LogoutViaGetView

urlpatterns = [
    # Django Admin Site
    path('admin/', admin.site.urls),

    # Include URLs from your apps
    # Requests starting with 'dashboard/' will be handled by dashboard/urls.py
    path('dashboard/', include('dashboard.urls')),
    # Requests starting with 'inventory/' will be handled by inventory/urls.py
    path('inventory/', include('inventory.urls')),
    # Requests starting with 'clients/' will be handled by clients/urls.py
    path('clients/', include('clients.urls')),
    # Requests starting with 'suppliers/' will be handled by suppliers/urls.py
    path('suppliers/', include('suppliers.urls')),
    # Requests starting with 'bookings/' will be handled by bookings/urls.py
    path('bookings/', include('bookings.urls')),
    # Requests starting with 'reports/' will be handled by reports.urls.py
    path('reports/', include('reports.urls')), # ADDED THIS LINE
    path('users/', include('users.urls')),
    path('request_quote/', include('request_quote.urls')),
    path("logout/", LogoutViaGetView.as_view(), name="logout"),
    # Make the dashboard the default page for the root URL (e.g., http://127.0.0.1:8000/)
    # This also delegates to dashboard/urls.py, looking for a pattern matching ''
    path('', include('dashboard.urls')),
]

# Add URL pattern for serving media files during development ONLY
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
