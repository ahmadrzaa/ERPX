from django import forms
from .models import Contracts, BusinessIncubator

class ContractsForm(forms.ModelForm):
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get all available incubators dynamically
        available_incubators = BusinessIncubator.get_available_incubators()

        # Ensure at least one option is available
        available_incubators.insert(0, ("", "Select an Incubator"))

        # If editing a contract, keep the assigned incubator
        if self.instance and self.instance.business_incubator_number:
            assigned_incubator = self.instance.business_incubator_number
            if (assigned_incubator, assigned_incubator) not in available_incubators:
                available_incubators.append((assigned_incubator, assigned_incubator))

        # Assign choices dynamically every time the form loads
        self.fields['business_incubator_number'] = forms.ChoiceField(
            choices=available_incubators,
            required=False,
            widget=forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'})
        )

    
    class Meta:
        
        model = Contracts
        fields = [
            'package', 'contract_duration', 'contract_effective_date', 
            'contract_expiration_date', 'actual_rent_value', 'business_incubator_number', 
            'monthly_rent_fee', 'first_party_signatory_name', 'first_party_designation', 
            'first_party_signature_date', 'second_party_signatory_name', 'second_party_title', 
            'second_party_personal_id', 'second_party_commercial_name', 
            'second_party_commercial_registry_number', 'second_party_signature_date',     
            'second_party_signatory_name_ar', 'second_party_title_ar', 'second_party_phone_number', 
            'second_party_email', 'second_party_commercial_name_ar', 'payment_interval', 
            'company_type', 'need_more_assistance', 'cpr_copy', 'cr_copy', 'cr_extract', 
            'business_brief','first_party_designation_ar','first_party_signatory_name_ar','status',
            'sme_registration',  # ✅ Newly added field
        ]
        widgets = {           
            'package': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'contract_duration': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'contract_effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control oh-input w-100'}),
            'contract_expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control oh-input w-100'}),
            'actual_rent_value': forms.NumberInput(attrs={'class': 'form-control oh-input w-100'}),
            'business_incubator_number': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'monthly_rent_fee': forms.NumberInput(attrs={'class': 'form-control oh-input w-100','required': True}),
            'first_party_signatory_name': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'first_party_signatory_name_ar': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget', 'dir': 'rtl'}),
            'first_party_designation': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'first_party_designation_ar': forms.TextInput(attrs={'class': 'form-control oh-input w-100', 'dir': 'rtl'}),
            'first_party_signature_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control oh-input w-100'}),
            'second_party_signatory_name': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'second_party_title': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'second_party_personal_id': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'second_party_commercial_name': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'second_party_commercial_registry_number': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'second_party_signature_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control oh-input w-100'}),
            'second_party_signatory_name_ar': forms.TextInput(attrs={'class': 'form-control oh-input w-100', 'dir': 'rtl'}),
            'second_party_title_ar': forms.TextInput(attrs={'class': 'form-control oh-input w-100', 'dir': 'rtl'}),
            'second_party_phone_number': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'second_party_email': forms.EmailInput(attrs={'class': 'form-control oh-input w-100'}),
            'second_party_commercial_name_ar': forms.TextInput(attrs={'class': 'form-control oh-input w-100', 'dir': 'rtl'}),
            'payment_interval': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'company_type': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'need_more_assistance': forms.Textarea(attrs={'class': 'form-control oh-input w-100', 'rows': 3}),
            'cpr_copy': forms.ClearableFileInput(attrs={'class': 'form-control oh-input w-100'}),
            'cr_copy': forms.ClearableFileInput(attrs={'class': 'form-control oh-input w-100'}),
            'cr_extract': forms.ClearableFileInput(attrs={'class': 'form-control oh-input w-100'}),
            'business_brief': forms.ClearableFileInput(attrs={'class': 'form-control oh-input w-100'}),
            'status': forms.Select(choices=Contracts.STATUS_CHOICES, attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'sme_registration': forms.Select(choices=Contracts.SME_REGISTRATION_CHOICES, attrs={'class': 'form-control oh-input w-100 select-widget'}),  # ✅ Added widget
        }



        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
