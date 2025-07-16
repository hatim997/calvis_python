# clavis_event_inventory/inventory/admin.py

from django.contrib import admin
from .models import Category, Item # Import both models from this app's models.py

@admin.register(Category) # Use decorator for cleaner registration
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',) # Allow filtering by parent

@admin.register(Item) # Use decorator and custom admin class for Item
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'sku', 
        'category', 
        'item_source', # ADDED item_source to list display
        'initial_quantity', 
        'available_quantity', 
        'rent_price_per_day', 
        'supplier'
    )
    list_filter = (
        'category', 
        'supplier', 
        'dimension_unit',
        'item_source' # ADDED item_source to filters
    )
    search_fields = (
        'name', 
        'sku', 
        'description', 
        'category__name', 
        'supplier__name',
        'item_source' # ADDED item_source to search fields
    )
    # Make calculated/system fields read-only in admin
    readonly_fields = ('sku', 'created_at', 'updated_at', 'available_quantity')
    list_select_related = ('category', 'supplier') # Optimize fetching related objects for list display

    # Define layout for Add/Edit pages in Admin
    fieldsets = (
        (None, { # Main section
            'fields': ('name', 
                       'item_source', # ADDED item_source here
                       'category', 
                       'sku', 
                       'description')
        }),
        ('Stock & Location', {
            'fields': ('initial_quantity', 'storage_location')
        }),
        ('Images', {
            'fields': ('image1', 'image2')
        }),
        ('Dimensions & Pricing', {
            'fields': (('depth', 'width', 'height', 'dimension_unit'), 'purchase_price', 'rent_price_per_day')
        }),
        ('Supplier & System', {
            'fields': ('supplier', 'created_at', 'updated_at'),
            'classes': ('collapse',) # Make this section collapsible
        }),
    )

# Using @admin.register decorator means we don't need these lines:
# admin.site.register(Category, CategoryAdmin)
# admin.site.register(Item, ItemAdmin)