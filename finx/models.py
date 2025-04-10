from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.utils import timezone 
from django.utils.timezone import now
from django.db import transaction
from django.contrib.auth.models import User
from django.db.models import Sum, F, Q, DecimalField
from django.core.exceptions import ValidationError
from datetime import timedelta
import requests




# Chart of Accounts Model
class Account(models.Model):
    CURRENCY_CHOICES = [('BHD', 'Bahraini Dinar'), ('USD', 'US Dollar')]
    ACCOUNT_TYPES = [
        ('asset', _('Asset')),
        ('liability', _('Liability')),
        ('equity', _('Equity')),
        ('revenue', _('Revenue')),
        ('expense', _('Expense')),
    ]

    name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='BHD')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

    def update_balance(self, amount):
        """
        Updates the balance of the account, ensuring proper accounting logic:
        - Assets/Expenses increase with debits (+amount), decrease with credits (-amount).
        - Liabilities/Equity/Revenue increase with credits (-amount), decrease with debits (+amount).
        """
        if self.account_type in ['asset', 'expense']:
            self.balance += amount  # Debit increases balance
        elif self.account_type in ['liability', 'equity', 'revenue']:
            self.balance -= amount  # Credit increases balance

        if self.balance < 0:
            raise ValidationError(f"Account '{self.name}' balance cannot be negative.")

        self.save()

    def clean(self):
        if not self.name:
            raise ValidationError("Account name cannot be empty.")
        if self.balance < 0:
            raise ValidationError("Balance cannot be negative.")



class JournalEntry(models.Model):
        
    number = models.CharField(max_length=50, unique=True,default='JE-0001')
    date = models.DateField()
    description = models.TextField()
    debit_account = models.ForeignKey(Account, related_name="debit_entries", on_delete=models.CASCADE)
    credit_account = models.ForeignKey(Account, related_name="credit_entries", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    is_reversal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
   
    def save(self, *args, **kwargs):
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be greater than zero.")
        if self.debit_account == self.credit_account:
            raise ValidationError("Debit and Credit accounts cannot be the same.")

        # Assign journal entry number for new instances
        if not self.pk:  # Only for new entries
            last_entry = JournalEntry.objects.order_by('-id').first()
            if last_entry and '-' in last_entry.number:
                prefix, num = last_entry.number.split('-')
                self.number = f"{prefix}-{int(num) + 1:04d}"
            else:
                self.number = "JE-0001"  # Default prefix for journal entries
        
        
        with transaction.atomic():
            if not self.pk:  # New entry
                self.debit_account.update_balance(self.amount)
                self.credit_account.update_balance(-self.amount)
            else:  # Editing an existing entry
                original = JournalEntry.objects.get(pk=self.pk)
                delta = self.amount - original.amount
                self.debit_account.update_balance(delta)
                self.credit_account.update_balance(-delta)

        super().save(*args, **kwargs)

    
    
class Currency(models.Model):
    code = models.CharField(
        max_length=3,
        unique=True,
        help_text="Currency code (e.g., USD, EUR, BHD)"
    )
    name = models.CharField(
        max_length=50,
        help_text="Currency name (e.g., US Dollar, Euro, Bahraini Dinar)"
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Exchange rate relative to the base currency"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Mark this currency as the default currency"
    )
    last_updated = models.DateTimeField(null=True, blank=True, help_text="When the exchange rate was last updated")
    
  
    

    @classmethod
    def update_exchange_rates(cls):
        """
        Updates exchange rates for all currencies relative to the default currency.
        """
        now_time = now()
        stale_time = now_time - timedelta(hours=0.0167)
        base_currency = cls.get_default_currency()

        if not base_currency:
            return "No default currency set. Please configure a default currency."

        API_URL = "http://api.exchangerate.host/live"
        config = Configuration.objects.first()

        if not config or not config.api_key_exchange:
            return "API Key for exchange rates is not configured."

        API_KEY = config.api_key_exchange

        params = {
            "access_key": API_KEY, 
            "source": base_currency,
          
        }

        try:
            # Make the API request
            response = requests.get(API_URL, params=params)
            response.raise_for_status()

            # Parse the response
            data = response.json()
            print(data)
            if data.get("success"):
                rates = data.get("quotes", {})
                updated_count = 0

                # Update exchange rates for stale currencies
                for currency in cls.objects.all():
                    currency_code = f"{base_currency}{currency.code}"
                    if currency_code in rates:
                        currency.exchange_rate = Decimal(str(rates[currency_code]))
                        currency.last_updated = now_time
                        currency.save()
                        updated_count += 1

                return f"Exchange rates updated successfully for {updated_count} currencies."
            else:
                return f"API Error: {data.get('error', {}).get('info', 'Unknown error occurred')}"

        except requests.exceptions.RequestException as e:
            return f"API request failed: {str(e)}"

        except Exception as e:
            return f"Unexpected error occurred: {str(e)}"



        
    
    def save(self, *args, **kwargs):
        # Ensure only one default currency
        if self.is_default:
            Currency.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default_currency(cls):
        """
        Returns the default currency.
        """
        return cls.objects.filter(is_default=True).first().code

    @classmethod
    def get_currency_choices(cls):
        """
        Fetch all currencies from the Currency model and format them as choices.
        Each choice will have the exchange rate as the value and the currency code as the display.
        """
        try:
            currencies = cls.objects.all()
            return [
                (str(currency.code), f"{currency.name} [{currency.exchange_rate}]")
                for currency in currencies
            ]
        except cls.DoesNotExist:
            return []    
    
    
    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
      

class Configuration(models.Model):
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,  # Default VAT rate as 10%
        help_text="Set the VAT rate as a percentage (e.g., 10 for 10%)"
    )
    api_key_exchange = models.CharField(
        max_length=150,
        help_text="API KEY for exchange rate (e.g., https://api.exchangerate.host/latest)",
        default=""
    )
        
    def __str__(self):
        return "Global Configuration"

    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configuration"

class Invoice(models.Model):
   
    currency = models.CharField(max_length=10, choices=Currency.get_currency_choices(), default='BHD')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0, help_text="exchange rate")
    vat_rate =  models.DecimalField(max_digits=15, decimal_places=2,blank=True, null=True,default=Configuration.objects.first().vat_rate)
    number = models.CharField(max_length=50, unique=True)
    reference = models.CharField(max_length=100, null=True, blank=True) 
    issue_date=models.DateField(default=now)
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    due_date = models.DateField(default=now)
    created_date = models.DateField(default=now)
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [('unpaid', 'Unpaid'), ('paid', 'Paid')]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    vat_exempt = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    line_items = models.JSONField(default=list, help_text="List of line items as JSON")

    is_recurring = models.BooleanField(default=False, help_text="Mark this invoice as recurring")
    recurrence_interval = models.CharField(
        max_length=10,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        null=True, blank=True,
        help_text="Recurrence interval for this invoice"
    )
    recurrence_end_date = models.DateField(null=True, blank=True, help_text="End date for recurring invoices")
    
    # ✅ Added this new field for manually entered payment date
    payment_date = models.DateField(null=True, blank=True, help_text="Manually entered payment date", default=now)
    
    def get_next_due_date(self):
        """
        Calculate the next due date based on recurrence interval.
        """
        if not self.is_recurring or not self.due_date:
            return None

        if self.recurrence_interval == 'daily':
            return self.due_date + timedelta(days=1)
        elif self.recurrence_interval == 'weekly':
            return self.due_date + timedelta(weeks=1)
        elif self.recurrence_interval == 'monthly':
            return self.due_date + timedelta(days=30)
        elif self.recurrence_interval == 'quarterly':
            return self.due_date + timedelta(days=90)
        elif self.recurrence_interval == 'yearly':
            return self.due_date + timedelta(days=365)

        return None
 
    def save(self, *args, **kwargs):
        try:
            
            selected_currency = Currency.objects.filter(code=self.currency).first()
           
            
            print (self.amount)
            if self.vat_exempt:                
                self.vat_amount = 0
                self.total_amount = self.amount    
            else:
                # Fetch VAT rate from configuration
                config = Configuration.objects.first()
                vat_rate = Decimal('0.00') if self.vat_exempt else (config.vat_rate / 100 if config else Decimal('0.10'))

                # Calculate VAT and total amount
                self.amount, self.vat_amount = self.calculate_totals()
                #self.vat_amount = self.amount * vat_rate
                self.total_amount = self.amount + self.vat_amount
                
               
            if selected_currency:
                # Set exchange_rate to the currency's value
                self.exchange_rate = Decimal(str(selected_currency.exchange_rate))
                
               
               
            # Calculate total_amount
          
            self.amount = Decimal(self.amount) * self.exchange_rate
            self.vat_amount = Decimal(self.vat_amount) * self.exchange_rate
            self.total_amount = self.amount + self.vat_amount
        
            # Fetch required accounts
            try:
                receivable_account = Account.objects.get(name='Accounts Receivable')
                revenue_account = Account.objects.get(name='Revenue')
                vat_account = Account.objects.get(name='VAT Payable')
                cash_account = Account.objects.get(name='Cash')                
            except Account.DoesNotExist as e:
                raise ValueError(f"Required account is missing: {e}")

            with transaction.atomic():
                if self.pk:  
    
                    original = Invoice.objects.get(pk=self.pk)                    

                    if original.status != self.status:
                        if self.status == 'paid': 
                            #receivable_account.balance -= self.total_amount
                            #cash_account.balance += self.total_amount
                            self.is_active=False
                            JournalEntry.objects.create(
                            date=timezone.now().date(),
                            description=f"Invoice {self.number} - Revenue",
                            debit_account=cash_account,  
                            credit_account=receivable_account,
                            amount=self.total_amount,
                            is_active=False,
                            )
                            
                     

                # Create journal entries (new invoice only)
                if not self.pk:
                                       
                    if self.status == 'paid':                   
                        JournalEntry.objects.create(
                            date=timezone.now().date(),
                            description=f"Invoice {self.number} - Revenue",
                            debit_account=cash_account,  
                            credit_account=revenue_account,
                            amount=self.amount,
                            is_active=False,
                        )
                        if self.vat_amount > 0:
                            JournalEntry.objects.create(
                                date=timezone.now().date(),
                                description=f"Invoice {self.number} - VAT",
                                debit_account=cash_account,  # Updated from receivable_account to cash_account
                                credit_account=vat_account,
                                amount=self.vat_amount,
                                is_active=False,
                            )
                        self.is_active=False
                    elif self.status == 'unpaid':
                        JournalEntry.objects.create(
                            date=timezone.now().date(),
                            description=f"Invoice {self.number} - Revenue",
                            debit_account=receivable_account,
                            credit_account=revenue_account,
                            amount=self.amount,
                            is_active=False,
                        )
                        if self.vat_amount > 0:
                            JournalEntry.objects.create(
                                date=timezone.now().date(),
                                description=f"Invoice {self.number} - VAT",
                                debit_account=receivable_account,
                                credit_account=vat_account,
                                amount=self.vat_amount,
                                is_active=False,
                            )
                            

            # Save the invoice
            super().save(*args, **kwargs)

        except Exception as e:
            raise ValueError(f"An error occurred while saving the invoice: {e}")
    def calculate_totals(self):
        """
        Calculate the subtotal, total tax, and grand total based on line items.
        """
        subtotal = Decimal('0.00')
        total_tax = Decimal('0.00')

        for item in self.line_items:
            quantity = Decimal(item.get('quantity', 0) or 0)
            unit_price = Decimal(item.get('unit_price', 0) or 0)
            discount = Decimal(item.get('discount', 0) or 0)
            tax_rate = Decimal(item.get('tax_rate', 0) or 0)

            # Calculate the item total
            item_total = (quantity * unit_price) - discount
            item_tax = item_total * (tax_rate / 100)

            subtotal += item_total
            total_tax += item_tax

        return subtotal, total_tax

    def __str__(self):
        return f"Invoice {self.number} - {self.client_name}"


class Expense(models.Model):
    number = models.CharField(max_length=50, unique=True,default='EXP-0001')
    name = models.CharField(max_length=255, null=True, blank=True)  
    email = models.EmailField(blank=True, null=True)  
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(default=timezone.now)
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('utilities', 'Utilities'),
        ('office', 'Office Expenses'),
        ('employee', 'Employee Costs'),
        ('travel', 'Travel and Transport'),
        ('marketing', 'Marketing'),
        ('professional', 'Professional Services'),
        ('vat', 'VAT'),
        ('miscellaneous', 'Miscellaneous'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    is_active = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        try:
            # Fetch required accounts
            expense_account = Account.objects.get(name='Expenses')
            cash_account = Account.objects.get(name='Cash')
            payable_account = Account.objects.get(name='Accounts Payable')
        except Account.DoesNotExist as e:
            raise ValueError(f"Required account is missing: {e}")

        with transaction.atomic():   
            
            if self.pk:  # Editing an existing expense
                original = Expense.objects.get(pk=self.pk)

                # Reverse the original transaction
                if original.status == 'unpaid':
                    JournalEntry.objects.create(
                        date=self.date,
                        description=f"Expense: {self.description}",
                        debit_account=payable_account,
                        credit_account=cash_account,
                        amount=self.amount,
                        is_active=False,
                    )

            # Create journal entries (new invoice only)
            if not self.pk:
                # Create a new journal entry
                if self.status == 'paid': 
                    self.is_active= False
                    JournalEntry.objects.create(
                        date=self.date,
                        description=f"Expense: {self.description}",
                        debit_account=expense_account,
                        credit_account=cash_account,
                        amount=self.amount,
                        is_active=False,
                    )
                elif self.status == 'unpaid':
                    
                        JournalEntry.objects.create(
                            date=self.date,
                            description=f"Expense: {self.description}",
                            debit_account=expense_account,
                            credit_account=payable_account,
                            amount=self.amount,
                            is_active=False,
                        )
          
            super().save(*args, **kwargs)







# models.py
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_name} - {self.action} by {self.user or 'System'} on {self.timestamp}"

    @staticmethod
    def log_audit(user, model_name, object_id, action, description):
        AuditLog.objects.create(
            user=user,
            model_name=model_name,
            object_id=object_id,
            action=action,
            description=description,
        )
