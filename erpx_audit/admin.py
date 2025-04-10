"""
admin.py
"""

from django.contrib import admin

from erpx_audit.models import AuditTag, erpxAuditInfo, erpxAuditLog

# Register your models here.

admin.site.register(AuditTag)
