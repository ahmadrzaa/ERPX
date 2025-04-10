from django.contrib import admin
from .models import Account, JournalEntry, Invoice, Configuration,Currency
from django.contrib import messages

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'balance', 'currency', 'description')
    list_filter = ('account_type', 'currency')

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'debit_account', 'credit_account', 'amount')
    list_filter = ('date',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'client_name', 'amount', 'vat_amount', 'total_amount', 'due_date', 'vat_exempt')
    list_filter = ('due_date','vat_exempt')


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('vat_rate','api_key_exchange',)
    fields = ('vat_rate','api_key_exchange',)

@admin.action(description='Update Exchange Rates')
def update_exchange_rates_action(modeladmin, request, queryset):
    result = Currency.update_exchange_rates()
    modeladmin.message_user(request, result)
    
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'exchange_rate', 'last_updated','is_default' )
    list_editable = ('exchange_rate', 'is_default')
    search_fields = ('code', 'name')
    actions = [update_exchange_rates_action]



