from django.contrib import admin
from .models import CRMRecord

@admin.register(CRMRecord)
class CRMRecordAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'email', 'phone', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'industry', 'created_at', 'updated_at')
    search_fields = ('customer_name', 'email', 'phone', 'company_name', 'contact_person', 'lead_source')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
