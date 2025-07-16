# clavis_event_inventory/inventory/urls.py

from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Item URLs
    path('items/', views.item_list_view, name='item_list'),
    path('items/add/', views.item_add_view, name='item_add'), # NEW
    path('item/<int:item_id>/', views.item_detail_view, name='item_detail'),
    path('item/<int:item_id>/edit/', views.item_edit_view, name='item_edit'), # NEW
    path('item/<int:item_id>/delete/', views.item_delete_view, name='item_delete'), # NEW
    path('item/delete-image/<int:image_id>/', views.delete_item_image, name='delete_item_image'),

    # Report URLs
    path('reports/master-inventory/', views.master_inventory_report, name='report_master_inventory'),
    path('reports/availability/', views.availability_report_view, name='report_availability'),
    
    # Barcode URLs
    path('print-barcode/<int:item_id>/', views.print_barcode_view, name='print_barcode'),

]