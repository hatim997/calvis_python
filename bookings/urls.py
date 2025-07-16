# clavis_event_inventory/bookings/urls.py

from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # --- Event URLs ---
    path('events/', views.event_list_view, name='event_list'),
    path('events/add/', views.event_add_view, name='event_add'),
    path('events/<int:event_id>/', views.event_detail_view, name='event_detail'),
    path('events/<int:event_id>/edit/', views.event_edit_view, name='event_edit'),
    path('events/<int:event_id>/delete/', views.event_delete_view, name='event_delete'),
    path('events/<int:booking_id>/delivery-note/', views.delivery_note_pdf_view, {'booking_type': 'event'}, name='delivery_note_pdf_event'),
    path('events/<int:booking_id>/receipt/', views.receipt_pdf_view, {'booking_type': 'event'}, name='receipt_pdf_event'),
    
    # NEW: URL for Logistics Waybill PDF
    path('events/<int:event_id>/waybill/', views.logistics_waybill_pdf_view, name='logistics_waybill_pdf'),


    # --- Rental URLs ---
    path('rentals/', views.rental_list_view, name='rental_list'),
    path('rentals/add/', views.rental_add_view, name='rental_add'),
    path('rentals/<int:rental_id>/', views.rental_detail_view, name='rental_detail'),
    path('rentals/<int:rental_id>/edit/', views.rental_edit_view, name='rental_edit'),
    path('rentals/<int:rental_id>/delete/', views.rental_delete_view, name='rental_delete'), 
    path('rentals/<int:booking_id>/delivery-note/', views.delivery_note_pdf_view, {'booking_type': 'rental'}, name='delivery_note_pdf_rental'),
    path('rentals/<int:booking_id>/receipt/', views.receipt_pdf_view, {'booking_type': 'rental'}, name='receipt_pdf_rental'),

]