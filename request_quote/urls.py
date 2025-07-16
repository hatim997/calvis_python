# clavis_event_inventory/users/urls.py

from django.urls import path
from . import views

app_name = 'request_quote'

urlpatterns = [
    path('', views.quote_list_view, name='quote_list'),  # ✅ No leading slash
    path('add/', views.quote_add_view, name='quote_add'),
    path('<int:quote_id>/edit/', views.quote_edit_view, name='quote_edit'),
    path('<int:quote_id>/delete/', views.quote_delete_view, name='quote_delete'),
    path('<int:quote_id>/details/', views.quote_detail_view, name='quote_detail'),
    path('<int:quote_id>/receipt/', views.quote_pdf_view,  name='quote_pdf_view'),
]
