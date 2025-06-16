from django.contrib import admin
from .models import Blocklist

@admin.register(Blocklist)
class BlocklistAdmin(admin.ModelAdmin):
    list_display = ['ip_addr', 'reason', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['ip_addr', 'reason']