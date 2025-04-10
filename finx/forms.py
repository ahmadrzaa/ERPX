from django import forms
from .models import Account, JournalEntry, Invoice, Expense,Configuration
from django.db.models import Max
from django.db import transaction

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'account_type', 'balance', 'currency', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'account_type': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control oh-input w-100'}),
            'currency': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'description': forms.Textarea(attrs={'class': 'form-control oh-input w-100', 'rows': 3}),
        }

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['number', 'date', 'description', 'debit_account', 'credit_account', 'amount']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control oh-input w-100 read_only', 'readonly': 'readonly'}),
            'date': forms.DateInput(attrs={'class': 'form-control oh-input w-100', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control oh-input w-100', 'rows': 2}),
            'debit_account': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'credit_account': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control oh-input w-100'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Only for new instances
            # Safely determine the next journal entry number
            last_entry = JournalEntry.objects.order_by('-id').first()
            try:
                if last_entry and '-' in last_entry.number:
                    prefix, num = last_entry.number.split('-')
                    next_number = f"{prefix}-{int(num) + 1:04d}"
                else:
                    next_number = "JE-0001"  # Default prefix for journal entries
            except Exception:
                next_number = "JE-0001"  # Fallback in case of malformed data
            self.fields['number'].initial = next_number

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['number', 'client_name', 'client_email', 'amount', 'due_date','issue_date', 'reference','status', 'vat_exempt','currency','vat_rate','line_items',
                 'is_recurring','recurrence_interval','recurrence_end_date']
        widgets = {      
            'line_items': forms.HiddenInput(),     
            'vat_rate': forms.TextInput(attrs={'class': 'form-control oh-input hidden', 'readonly': 'readonly'}),
            'number': forms.TextInput(attrs={'class': 'form-control oh-input w-100 read_only', 'readonly': 'readonly'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control oh-input w-100'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control oh-input w-100'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control oh-input w-100', 'type': 'date'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control oh-input w-100', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'form-control oh-input w-100'}),
            'status': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}), 
            'vat_exempt': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'currency': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}), 
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Only for new instances
            # Safely determine the next invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            try:
                if last_invoice and '-' in last_invoice.number:
                    prefix, num = last_invoice.number.split('-')
                    next_number = f"{prefix}-{int(num) + 1:04d}"
                else:
                    next_number = "INV-0001"  # Default to the first number
            except Exception:
                next_number = "INV-0001"  # Fallback in case of malformed data
            self.fields['number'].initial = next_number
     
        
            
            
            

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['number', 'name', 'email', 'date', 'category', 'amount', 'description', 'status']  # Added 'name' and 'email'
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control oh-input w-100 read_only', 'readonly': 'readonly'}),
            'name': forms.TextInput(attrs={'class': 'form-control oh-input w-100', 'placeholder': 'Enter name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control oh-input w-100', 'placeholder': 'Enter email'}),
            'date': forms.DateInput(attrs={'class': 'form-control oh-input w-100', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control oh-input w-100'}),
            'description': forms.Textarea(attrs={'class': 'form-control oh-input w-100', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control oh-input w-100 select-widget'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Only for new instances
            # Safely determine the next expense number
            last_expense = Expense.objects.order_by('-id').first()
            try:
                if last_expense and '-' in last_expense.number:
                    prefix, num = last_expense.number.split('-')
                    next_number = f"{prefix}-{int(num) + 1:04d}"
                else:
                    next_number = "EXP-001"  # Default to the first number
            except Exception:
                next_number = "EXP-001"  # Fallback in case of malformed data
            self.fields['number'].initial = next_number


class VATPaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=15, decimal_places=2, label="Payment Amount")
    payment_date = forms.DateField(label="Payment Date")
    description = forms.CharField(max_length=255, label="Description (optional)", required=False)
