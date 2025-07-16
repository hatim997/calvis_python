# dashboard/admin.py
from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message_snippet', 'user', 'created_at', 'is_read', 'link')
    list_filter = ('is_read', 'created_at', 'user')
    search_fields = ('message', 'user__username')
    list_editable = ('is_read',)

    def message_snippet(self, obj):
        return (obj.message[:75] + '...') if len(obj.message) > 75 else obj.message
    message_snippet.short_description = 'Message'