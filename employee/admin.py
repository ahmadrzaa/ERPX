"""
admin.py

This page is used to register the model with admins site.
"""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from employee.models import (
    Actiontype,
    BonusPoint,
    DisciplinaryAction,
    Employee,
    EmployeeBankDetails,
    EmployeeNote,
    EmployeeTag,
    EmployeeWorkInformation,
    Policy,
    PolicyMultipleFile,
)
from .models import Grade, GradeStep

# Register your models here.

admin.site.register(Employee)
admin.site.register(EmployeeBankDetails)
admin.site.register(EmployeeWorkInformation, SimpleHistoryAdmin)
admin.site.register([EmployeeNote, EmployeeTag, PolicyMultipleFile, Policy, BonusPoint])
admin.site.register([DisciplinaryAction, Actiontype])

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("label", "value")
    search_fields = ("label",)
    ordering = ("value",)


@admin.register(GradeStep)
class GradeStepAdmin(admin.ModelAdmin):
    list_display = ("grade", "step", "amount")
    search_fields = ("grade__label",)
    list_filter = ("grade",)
    ordering = ("grade", "step")
