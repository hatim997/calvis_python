# clavis_event_inventory/clients/urls.py

from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Client List (/clients/)
    path('', views.client_list_view, name='client_list'),

    # Client Add (/clients/add/)
    path('add/', views.client_add_view, name='client_add'),

    # Client Detail (/clients/123/)
    path('<int:client_id>/', views.client_detail_view, name='client_detail'),

    # Client Edit (/clients/123/edit/)
    path('<int:client_id>/edit/', views.client_edit_view, name='client_edit'),

    # Client Delete (/clients/123/delete/) - NEW
    path('<int:client_id>/delete/', views.client_delete_view, name='client_delete'),
]