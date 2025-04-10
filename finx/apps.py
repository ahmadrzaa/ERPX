from django.apps import AppConfig
from django.db.utils import IntegrityError
import threading

class FinxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finx'

    def ready(self):
        
        from .scheduler import start_scheduler
        thread = threading.Thread(target=start_scheduler)
        thread.daemon = True  # Ensures it runs in the background
        thread.start()   
        
        from .models import Account
        default_accounts = [
            {'name': 'Accounts Receivable', 'account_type': 'asset', 'balance': 0},
            {'name': 'Revenue', 'account_type': 'revenue', 'balance': 0},
            {'name': 'VAT Payable', 'account_type': 'liability', 'balance': 0},
            {'name': 'Cash', 'account_type': 'asset', 'balance': 0},
         
            {'name': 'Expenses', 'account_type': 'expense', 'balance': 0, 'currency': 'BHD'},
            {'name': 'Accounts Payable', 'account_type': 'liability', 'balance': 0},  

        ]
        for account in default_accounts:
            try:
                Account.objects.get_or_create(name=account['name'], account_type=account['account_type'], defaults={'balance': account['balance'], 'currency': account.get('currency', 'BHD')})
            except IntegrityError:
                continue

        

