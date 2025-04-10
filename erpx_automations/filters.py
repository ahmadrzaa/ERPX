"""
erpx_automations/filters.py
"""

from erpx.filters import erpxFilterSet, django_filters
from erpx_automations.models import MailAutomation


class AutomationFilter(erpxFilterSet):
    """
    AutomationFilter
    """

    search = django_filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = MailAutomation
        fields = "__all__"
