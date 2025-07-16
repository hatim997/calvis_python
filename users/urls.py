# clavis_event_inventory/users/urls.py

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.user_list_view, name='user_list'),  # ✅ No leading slash
    path('add/', views.user_add_view, name='user_add'),
    path('<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
]
