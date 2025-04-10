from django.contrib import admin
from .models import Contracts, BusinessIncubator   

@admin.register(Contracts)
class ContractsAdmin(admin.ModelAdmin):
    list_display = (
        'contract_number', 'package', 'contract_duration', 'contract_effective_date',
        'contract_expiration_date', 'actual_rent_value', 'business_incubator_number',
        'monthly_rent_fee', 'first_party_signatory_name', 'second_party_signatory_name','status'
    )
    search_fields = ('contract_number', 'first_party_signatory_name', 'second_party_signatory_name')
    list_filter = ('contract_effective_date', 'contract_expiration_date', 'status')
    
    
@admin.register(BusinessIncubator)
class BusinessIncubatorAdmin(admin.ModelAdmin):
    list_display = ('number', 'is_occupied', 'get_contract_id')
    list_filter = ('is_occupied',)
    search_fields = ('number', 'contract_id')

    def get_contract_id(self, obj):
        return obj.contract_id if obj.contract_id else "No Contract"
    get_contract_id.short_description = "Contract ID"  # Rename column in admin panel
    
    
