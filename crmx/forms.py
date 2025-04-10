from django import forms
from .models import CRMRecord

class CRMRecordForm(forms.ModelForm):
    class Meta:
        model = CRMRecord
        fields = [
            'customer_name', 'email', 'phone', 'company_name',
            'industry', 'contact_person', 'contact_person_role',
            'building', 'road', 'block', 'area', 'city', 'country',
            'postal_code', 'status', 'lead_source', 'assigned_to', 'notes'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'email': forms.EmailInput(attrs={'class': 'form-control oh-input w-100'}),
            'phone': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'industry': forms.Select(attrs={'class': 'form-select oh-input w-100 select-widget'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'contact_person_role': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'building': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'road': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'block': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'area': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'city': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'country': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'status': forms.Select(attrs={'class': 'form-select oh-input w-100 select-widget'}),
            'lead_source': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'notes': forms.Textarea(attrs={'class': 'form-control oh-input w-100', 'rows': 3}),
        }
