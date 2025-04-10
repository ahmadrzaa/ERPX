from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, F, Q, DecimalField
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone 
import csv
from .models import Account, JournalEntry, Invoice,Expense, AuditLog, Currency
from .forms import AccountForm, JournalEntryForm, InvoiceForm, ExpenseForm
from decimal import Decimal
from django.db import transaction
import logging
from django.http import HttpResponseForbidden
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from base.models import Company
import json
from datetime import datetime
from lamx.models import *


logger = logging.getLogger(__name__)  

#print

def render_to_pdf(template_src, context_dict):
    """
    Render the provided template with context as a PDF.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

def print_invoice(request, invoice_id):
    """
    Generate and return a PDF for the given invoice ID.
    """
    try:
        # Get the invoice
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        return HttpResponse("Invoice not found", status=404)

    # Get the current company (e.g., based on user or other logic)
    company = Company.objects.filter(hq=True).first()  # Modify logic as needed
    if not company:
        return HttpResponse("Company not found", status=404)
    base_url = f"{request.scheme}://{request.get_host()}"  # Generate base URL
    logo_url = f"{base_url}{company.icon.url}" if company.icon else f"{base_url}/static/images/logo.png"

    contract = Contracts.objects.filter(contract_number=invoice.reference).first()
    comp_name=""
    if contract:
          comp_name=contract.second_party_commercial_name  # This fetches the company na

    # Use line_items as a Python object (no need for json.loads)
    line_items = invoice.line_items if isinstance(invoice.line_items, list) else []
    subtotal = 0
    total_tax = 0

    for item in line_items:
        quantity = float(item.get('quantity', 0))
        unit_price = float(item.get('unit_price', 0))
        discount = float(item.get('discount', 0)) / 100
        tax_rate = float(item.get('tax_rate', 0)) / 100

        line_total_before_tax = quantity * unit_price * (1 - discount)
        line_tax = line_total_before_tax * tax_rate

        subtotal += line_total_before_tax
        total_tax += line_tax

    grand_total = subtotal + total_tax
    # Template context
    context = {
        'company_logo_url': logo_url,
        'company_name': company.company,
        'company_address': company.address,
        
        'company_email': company.email,  
        'company_phone': company.phone, 
        
        'invoice': {
            'number': invoice.number,
            'issue_date': invoice.created_date.strftime('%Y-%m-%d'),
            'due_date': invoice.due_date.strftime('%Y-%m-%d'),
            'client_name': invoice.client_name,
            'client_email': invoice.client_email,
            'amount': f"{Currency.get_default_currency()} {invoice.amount:.2f}",
            'vat_amount': f"{Currency.get_default_currency()} {invoice.vat_amount:.2f}" if invoice.vat_amount else "N/A",
            'total_amount': f"{Currency.get_default_currency()} {invoice.total_amount:.2f}" if invoice.total_amount else "N/A",
            'reference': invoice.reference if invoice.reference else "N/A",
            'status': invoice.status.capitalize(),
            'currency': invoice.currency,
            'subtotal': subtotal,
            'total_tax': total_tax,
            'grand_total': grand_total,
            'default_cur': Currency.get_default_currency(),
            'comp_name':comp_name,
            'line_items': [
                {
                    'item': item.get('item', ''),
                    'description': item.get('description', 0),
                    'quantity': f"{float(item.get('quantity', 0)):.2f}",
                    'unit_price': f"{float(item.get('unit_price', 0.0)):.2f}",
                    'discount': f"{float(item.get('discount', 0.0)):.2f}",
                    'tax_rate': f"{float(item.get('tax_rate', 0.0)):.2f}",
                    'line_total': f"{float(item.get('line_total', 0.0)):.2f}",
                   
                }
                for item in line_items
            ],
            
        }
    }

    pdf_content = render_to_pdf('finx/invoice_template.html', context)
    if pdf_content:
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=Invoice_{invoice.number}.pdf'
        return response
    return HttpResponse("Failed to generate invoice PDF", status=500)


def print_receipt(request, receipt_id):
    """
    Generate and return a PDF for the given receipt ID.
    """
    try:
        # Get the receipt (assuming Receipt model exists)
        receipt = Invoice.objects.get(id=receipt_id)  # Replace with your actual receipt model if different
    except Invoice.DoesNotExist:
        return HttpResponse("Receipt not found", status=404)

    # Get the current company (e.g., based on user or other logic)
    company = Company.objects.filter(hq=True).first()  # Modify logic as needed
    if not company:
        return HttpResponse("Company not found", status=404)
    base_url = f"{request.scheme}://{request.get_host()}"  # Generate base URL
    logo_url = f"{base_url}{company.icon.url}" if company.icon else f"{base_url}/static/images/logo.png"

    # Calculate amount paid including VAT
    amount_paid_including_vat = receipt.amount + (receipt.vat_amount or 0)
    
    
    contract = Contracts.objects.filter(contract_number=receipt.reference).first()
    comp_name=""
    if contract:
          comp_name=contract.second_party_commercial_name  # This fetches the company na
    # Prepare context
    context = {
        'company_logo_url': logo_url,
        'company_name': company.company,
        'company_address': company.address,
        'company_email': company.email,  
        'company_phone': company.phone,          
        'receipt': {
            'id': receipt.id,
            'payment_date': receipt.payment_date.strftime('%Y-%m-%d'),  # Adjust field for payment date
            'issue_date': receipt.created_date.strftime('%Y-%m-%d'),
            'client_name': receipt.client_name,
            'client_email': receipt.client_email,
            'amount_paid': f"{receipt.currency} {amount_paid_including_vat:.2f}",  # Updated to include VAT
            'amount_due': f"{receipt.currency} {(receipt.total_amount - amount_paid_including_vat):.2f}",
            'invoice_date': receipt.issue_date.strftime('%Y-%m-%d'),
            'reference': receipt.reference if receipt.reference else "N/A",
            'currency': receipt.currency,
            'comp_name':comp_name
            
        }
    }

    pdf_content = render_to_pdf('finx/receipt_template.html', context)
    if pdf_content:
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=Receipt_{receipt.id}.pdf'
        return response
    return HttpResponse("Failed to generate receipt PDF", status=500)


# Account Views
def account_list(request):
    accounts = Account.objects.all()

    # Get filters from request
    account_type_filter = request.GET.get('account_type')
    min_balance = request.GET.get('min_balance')
    max_balance = request.GET.get('max_balance')

    # Apply filters if present
    if account_type_filter:
        accounts = accounts.filter(account_type=account_type_filter)
    if min_balance:
        accounts = accounts.filter(balance__gte=float(min_balance))
    if max_balance:
        accounts = accounts.filter(balance__lte=float(max_balance))

    # Totals for summary
    total_assets = accounts.filter(account_type='asset').aggregate(total=Sum('balance'))['total'] or 0
    total_liabilities = accounts.filter(account_type='liability').aggregate(total=Sum('balance'))['total'] or 0
    total_revenue = accounts.filter(account_type='revenue').aggregate(total=Sum('balance'))['total'] or 0

    context = {
        'accounts': accounts,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_revenue': total_revenue,
    }
    return render(request, 'finx/account_list.html', context)

def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.save()
            messages.success(request, "Account created successfully.")
            return redirect('finx:account_list')
    else:
        form = AccountForm()
    return render(request, 'finx/account_form.html', {'form': form})

def account_edit(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, "Account updated successfully.")
            return redirect('finx:account_list')
    else:
        form = AccountForm(instance=account)
    return render(request, 'finx/account_form.html', {'form': form})

def account_delete(request, pk):
    account = get_object_or_404(Account, pk=pk)
    account.delete()
    messages.success(request, "Account deleted successfully.")
    return redirect('finx:account_list')


def journal_entry_list_1(request):
    journal_entries = JournalEntry.objects.all()

    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    account = request.GET.get('account')

    if start_date:
        journal_entries = journal_entries.filter(date__gte=start_date)
    if end_date:
        journal_entries = journal_entries.filter(date__lte=end_date)
    if account:
        journal_entries = journal_entries.filter(Q(debit_account_id=account) | Q(credit_account_id=account))

    # Summary
    total_debits = journal_entries.aggregate(total_debits=Sum('amount', filter=Q(debit_account__isnull=False)))['total_debits'] or Decimal(0)
    total_credits = journal_entries.aggregate(total_credits=Sum('amount', filter=Q(credit_account__isnull=False)))['total_credits'] or Decimal(0)

    # Unbalanced Entries: Check if the debit and credit amounts for each entry are equal
    unbalanced_entries_count = journal_entries.annotate(
        debit_total=F('amount'),  # Debit amount
        credit_total=F('amount')  # Credit amount
    ).filter(~Q(debit_total=F('credit_total'))).count()

    accounts = Account.objects.all()  # Needed for the filter dropdown

    context = {
        'journal_entries': journal_entries,
        'total_debits': total_debits,
        'total_credits': total_credits,
        'unbalanced_entries_count': unbalanced_entries_count,
        'accounts': accounts,
    }
    return render(request, 'finx/journal_entry_list.html', context)



def journal_entry_list(request):
    journal_entries = JournalEntry.objects.all()

    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    account = request.GET.get('account')

    if start_date:
        journal_entries = journal_entries.filter(date__gte=start_date)
    if end_date:
        journal_entries = journal_entries.filter(date__lte=end_date)
    if account:
        journal_entries = journal_entries.filter(Q(debit_account_id=account) | Q(credit_account_id=account))

    # Pagination
    paginator = Paginator(journal_entries, 9)  # Show 10 journal entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Summary
    total_debits = journal_entries.aggregate(total_debits=Sum('amount', filter=Q(debit_account__isnull=False)))['total_debits'] or Decimal(0)
    total_credits = journal_entries.aggregate(total_credits=Sum('amount', filter=Q(credit_account__isnull=False)))['total_credits'] or Decimal(0)

    # Unbalanced Entries: Check if the debit and credit amounts for each entry are equal
    unbalanced_entries_count = journal_entries.annotate(
        debit_total=F('amount'),  # Debit amount
        credit_total=F('amount')  # Credit amount
    ).filter(~Q(debit_total=F('credit_total'))).count()

    accounts = Account.objects.all()  # Needed for the filter dropdown

    context = {
        'journal_entries': page_obj,  # Use the paginated page object
        'total_debits': total_debits,
        'total_credits': total_credits,
        'unbalanced_entries_count': unbalanced_entries_count,
        'accounts': accounts,
    }
    return render(request, 'finx/journal_entry_list.html', context)

def journal_entry_create(request):
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    entry = form.save(commit=False)
                    
                    # Validate amount
                    if entry.amount <= 0:
                        messages.error(request, "The amount must be greater than zero.")
                        return render(request, 'finx/journal_entry_form.html', {'form': form})

                    # Ensure accounts are distinct
                    if entry.debit_account == entry.credit_account:
                        messages.error(request, "Debit and Credit accounts cannot be the same.")
                        return render(request, 'finx/journal_entry_form.html', {'form': form})

                    # Let the `JournalEntry.save()` handle balance updates
                    entry.save()

                messages.success(request, "Journal entry created successfully.")
                return redirect('finx:journal_entry_list')
            except ValidationError as e:
                messages.error(request, f"Validation error: {e}")
            except Exception as e:
                messages.error(request, f"Unexpected error occurred: {e}")
    else:
        form = JournalEntryForm()
    return render(request, 'finx/journal_entry_form.html', {'form': form})


def journal_entry_edit(request, pk):
    return HttpResponseForbidden("Editing journal entries is not allowed.")


def journal_entry_reverse(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk)
    
    try:
        with transaction.atomic():
            if entry.is_active:
                # Check if reversal is possible
                if entry.debit_account.balance < entry.amount:
                    raise ValidationError(
                        f"Cannot reverse journal entry: '{entry.debit_account.name}' does not have sufficient balance."
                    )
                if entry.credit_account.balance + entry.amount < 0:
                    raise ValidationError(
                        f"Cannot reverse journal entry: '{entry.credit_account.name}' balance cannot go negative."
                    )
                
                print (entry.amount,entry.debit_account.balance, entry.credit_account.balance)

                # Reverse the balances for the associated accounts
                entry.debit_account.balance -= entry.amount
                entry.credit_account.balance -= entry.amount

            
                print (entry.amount,entry.debit_account.balance, entry.credit_account.balance)

                
                # Save the updated accounts
                entry.debit_account.save()
                entry.credit_account.save()

                # Delete the journal entry
                entry.delete()
                messages.success(request, "Journal entry reversed successfully.")
            else:
                  messages.error(request, "Not Allowed To Delete.")

        
        return redirect('finx:journal_entry_list')

    except ValidationError as e:
        messages.error(request, f"An error occurred while deleting the journal entry: {e}")
        return redirect('finx:journal_entry_list')

    except Exception as e:
        messages.error(request, f"Unexpected error occurred: {e}")
        return redirect('finx:journal_entry_list')

    

def invoice_list_1(request):
    invoices = Invoice.objects.all()
    return render(request, 'finx/invoice_list.html', {'invoices': invoices})

def invoice_list(request):
    invoices = Invoice.objects.all()

    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')

    if start_date:
        invoices = invoices.filter(due_date__gte=start_date)
    if end_date:
        invoices = invoices.filter(due_date__lte=end_date)
    if status:
        invoices = invoices.filter(status=status)

    # Summary
    total_paid = invoices.filter(status='paid').aggregate(total_paid=Sum('total_amount'))['total_paid'] or 0
    total_unpaid = invoices.filter(status='unpaid').aggregate(total_unpaid=Sum('total_amount'))['total_unpaid'] or 0
    unpaid_count = invoices.filter(status='unpaid').count()
    total_vat = invoices.aggregate(total_vat=Sum('vat_amount'))['total_vat'] or 0
    total_invoices = invoices.count()

    # Pagination
    paginator = Paginator(invoices, 9)  # 9 invoices per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'finx/invoice_list.html', {
        'invoices': page_obj,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'unpaid_count': unpaid_count,
        'total_vat': total_vat,
        'total_invoices': total_invoices,
    })
    
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    invoice = form.save(commit=False)
                    invoice.save()
                    messages.success(request, "Invoice created successfully.")
                    return redirect('finx:invoice_list')
            except Exception as e:
                messages.error(request, f"Error creating invoice: {e}")
        else:
            messages.error(request, "Invalid form data.")
    else:
        form = InvoiceForm()
    return render(request, 'finx/invoice_form.html', {'form': form})


def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if  invoice.is_active:
            if form.is_valid():
                try:
                    with transaction.atomic():
                        invoice = form.save(commit=False)
                        invoice.save()
                        messages.success(request, "Invoice updated successfully.")
                        return redirect('finx:invoice_list')
                except Exception as e:
                    messages.error(request, f"Error updating invoice: {e}")
            else:
                messages.error(request, "Invalid form data.")
        else:
            messages.error(request, "Not Allowed to Edit Paid Invoice")
    else:
        form = InvoiceForm(instance=invoice)
    return render(request, 'finx/invoice_form.html', {'form': form})

def mark_invoice_paid(request, pk):
    """
    View to mark an invoice as paid and update related accounts and journal entries.
    """
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'paid':
        messages.warning(request, f"Invoice {invoice.number} is already marked as paid.")
        return redirect('finx:invoice_list')

    try:
        with transaction.atomic():
            # Update the invoice status to 'paid'
            invoice.status = 'paid'
            invoice.save()

            messages.success(request, f"Invoice {invoice.number} has been marked as paid.")
    except Exception as e:
        messages.error(request, f"An error occurred while marking the invoice as paid: {e}")
    
    return redirect('finx:invoice_list')

def invoice_delete_1(request, pk):
    try:
        # Retrieve the invoice
        invoice = get_object_or_404(Invoice, pk=pk)

        # Retrieve accounts
        receivable_account = Account.objects.get(name='Accounts Receivable')
        vat_account = Account.objects.get(name='VAT Payable')
        revenue_account = Account.objects.get(name='Revenue')
        cash_account = Account.objects.get(name='Cash')

        # Adjust account balances based on invoice status
        if invoice.status == 'paid':
            # Reverse cash account and reduce the receivable
            cash_account.balance -= invoice.total_amount
            receivable_account.balance += invoice.total_amount
            cash_account.save()
            receivable_account.save()

        elif invoice.status == 'unpaid':
            # Reverse receivable and VAT
            receivable_account.balance -= invoice.total_amount
            vat_account.balance -= invoice.vat_amount
            revenue_account.balance -= invoice.amount
            receivable_account.save()
            vat_account.save()
            revenue_account.save()

        # Delete associated journal entries
        JournalEntry.objects.filter(description__icontains=f"Invoice {invoice.number}").delete()

        # Delete the invoice
        invoice.delete()

        messages.success(request, "Invoice deleted successfully.")
    except Account.DoesNotExist as e:
        messages.error(request, f"Required account is missing: {str(e)}")
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the invoice: {e}")

    return redirect('finx:invoice_list')


def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    try:
        with transaction.atomic():
            # Fetch required accounts
            receivable_account = Account.objects.get(name='Accounts Receivable')
            vat_account = Account.objects.get(name='VAT Payable')
            revenue_account = Account.objects.get(name='Revenue')
            cash_account = Account.objects.get(name='Cash')

            # Reverse the financial impact of the invoice
            if invoice.status == 'paid':
                # For paid invoices: Reverse cash and receivable impact
                cash_account.update_balance(-invoice.total_amount)
                revenue_account.update_balance(+invoice.amount)
                vat_account.update_balance(+invoice.vat_amount)
            elif invoice.status == 'unpaid':
                # For unpaid invoices: Reverse receivable, VAT, and revenue impact
                receivable_account.update_balance(-invoice.total_amount)
                vat_account.update_balance(+invoice.vat_amount)
                revenue_account.update_balance(+invoice.amount)

            # Delete associated journal entries
            JournalEntry.objects.filter(description__icontains=f"Invoice {invoice.number}").delete()

            # Delete the invoice itself
            invoice.delete()

        messages.success(request, "Invoice deleted successfully.")
    except ValidationError as e:
        messages.error(request, f"Error deleting invoice: {e}")
    except Account.DoesNotExist as e:
        messages.error(request, f"Required account is missing: {e}")
    except Exception as e:
        messages.error(request, f"Unexpected error occurred: {e}")

    return redirect('finx:invoice_list')




def expense_list_1(request):
    expenses = Expense.objects.all()
    total_paid = expenses.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_unpaid = expenses.filter(status='unpaid').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'expenses': expenses,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
    }
    return render(request, 'finx/expense_list.html', context)


def expense_list(request):
    expenses = Expense.objects.all()

    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    category = request.GET.get('category')

    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)
    if status:
        expenses = expenses.filter(status=status)
    if category:
        expenses = expenses.filter(category=category)

    # Pagination
    paginator = Paginator(expenses, 9)  # Show 9 expenses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Summary Metrics
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_paid = expenses.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    total_unpaid = expenses.filter(status='unpaid').aggregate(total=Sum('amount'))['total'] or 0
    paid_count = expenses.filter(status='paid').count()
    unpaid_count = expenses.filter(status='unpaid').count()

    context = {
        'expenses': page_obj,  # Paginated data
        'total_expenses': total_expenses,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'categories': Expense.CATEGORY_CHOICES,  # For the category dropdown
    }
    return render(request, 'finx/expense_list.html', context)

def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()  # Accounting logic is handled in the model
                    messages.success(request, "Expense added successfully.")
                    return redirect('finx:expense_list')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Unexpected error: {e}")
    else:
        form = ExpenseForm()
    return render(request, 'finx/expense_form.html', {'form': form})




def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if  expense.is_active:
            if form.is_valid():
                try:
                    with transaction.atomic():
                        form.save()  # Accounting logic is handled in the model
                        messages.success(request, "Expense updated successfully.")
                        return redirect('finx:expense_list')
                except ValueError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    messages.error(request, f"Error updating expense: {e}")
        else:
             messages.error(request, "Not Allowed to Edit Paid Expense")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'finx/expense_form.html', {'form': form})






def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)

    try:
        with transaction.atomic():
            # Fetch required accounts
            expense_account = Account.objects.get(name='Expenses')
            cash_account = Account.objects.get(name='Cash')
            payable_account = Account.objects.get(name='Accounts Payable')

            # Reverse the financial impact of the expense
            if expense.status == 'paid':
                # For paid expenses: Reverse cash and expense impact
                expense_account.update_balance(-expense.amount)
                cash_account.update_balance(expense.amount)
            elif expense.status == 'unpaid':
                # For unpaid expenses: Reverse expense and payable impact
                expense_account.update_balance(-expense.amount)
                payable_account.update_balance(expense.amount)

            # Delete associated journal entries
            JournalEntry.objects.filter(description__icontains=f"Expense: {expense.description}").delete()

            # Delete the expense itself
            expense.delete()

        messages.success(request, "Expense deleted successfully.")
    except ValidationError as e:
        messages.error(request, f"Error deleting expense: {e}")
    except Account.DoesNotExist as e:
        messages.error(request, f"Required account is missing: {e}")
    except Exception as e:
        messages.error(request, f"Unexpected error occurred: {e}")

    return redirect('finx:expense_list')


def mark_expense_paid(request, pk):
    """
    View to mark an expense as paid and update related accounts and journal entries.
    """
    expense = get_object_or_404(Expense, pk=pk)

    if expense.status == 'paid':
        messages.warning(request, f"Expense {expense.description} is already marked as paid.")
        return redirect('finx:expense_list')

    try:
        with transaction.atomic():
          
            # Update the expense status to 'paid'
            expense.status = 'paid'
            expense.save()


            messages.success(request, f"Expense {expense.description} has been marked as paid.")
    except Account.DoesNotExist as e:
        messages.error(request, f"Required account is missing: {e}")
    except Exception as e:
        messages.error(request, f"An error occurred while marking the expense as paid: {e}")

    return redirect('finx:expense_list')


def dashboard(request):
    
    #Currency.update_exchange_rates()
    #print("TEST")
    # Revenue Trends
    revenue_data = (
        JournalEntry.objects.filter(credit_account__account_type="revenue")
        .values("date__month", "date__year")
        .annotate(total_revenue=Sum("amount", output_field=DecimalField()))
        .order_by("date__year", "date__month")
    )

    # Expense Trends
    expense_data = (
        JournalEntry.objects.filter(debit_account__account_type="expense")
        .values("date__month", "date__year")
        .annotate(total_expense=Sum("amount", output_field=DecimalField()))
        .order_by("date__year", "date__month")
    )

    # Total Revenue and Expenses
    revenue_total = (
        JournalEntry.objects.filter(credit_account__account_type="revenue")
        .aggregate(total_revenue=Sum("amount", output_field=DecimalField()))
        .get("total_revenue", Decimal(0)) or Decimal(0)
    )

    expense_total = (
        JournalEntry.objects.filter(debit_account__account_type="expense")
        .aggregate(total_expense=Sum("amount", output_field=DecimalField()))
        .get("total_expense", Decimal(0)) or Decimal(0)
    )

    # Net Profit
    net_profit = revenue_total - expense_total

    
    
     # Total Receivable
    total_receivable = Account.objects.filter(name='Accounts Receivable').aggregate(total=Sum('balance'))['total'] or 0

    # Total Payable
    total_payable = Account.objects.filter(name='Accounts Payable').aggregate(total=Sum('balance'))['total'] or 0

    # Trial Balance (Total Debits and Credits)
    total_debits = Account.objects.filter(account_type__in=['asset', 'expense']).aggregate(total=Sum('balance'))['total'] or 0
    total_credits = Account.objects.filter(account_type__in=['liability', 'revenue', 'equity']).aggregate(total=Sum('balance'))['total'] or 0
    
    # Accounts Receivable
    receivables = Invoice.objects.filter(status="unpaid").values(
        "due_date", "total_amount", "client_name", "client_email"
    )

    # Expense Breakdown by Category and Month
    expense_breakdown_data = (
        Expense.objects.values("category", "date__month", "date__year")
        .annotate(total=Sum("amount", output_field=DecimalField()))
        .order_by("date__year", "date__month", "category")
    )

    # Prepare category breakdown data for the chart
    category_data = {}
    for record in expense_breakdown_data:
        label = f"{record['date__month']}/{record['date__year']}"
        category = record["category"]
        amount = float(record["total"])
        if label not in category_data:
            category_data[label] = {}
        category_data[label][category] = category_data[label].get(category, 0) + amount

    # Flatten the data for the chart
    all_labels = sorted(category_data.keys())  # Get all unique month/year labels
    all_categories = {record["category"] for record in expense_breakdown_data}
    expense_chart_data = {
        category: [category_data[label].get(category, 0) for label in all_labels]
        for category in all_categories
    }

    # Accounts Payable
    payables = Expense.objects.filter(status="unpaid").values( "date",  "amount",  "description", "category",)

    
    # Revenue vs Expenses Chart
    revenue_labels = [f"{data['date__month']}/{data['date__year']}" for data in revenue_data]
    revenue_values = [float(data["total_revenue"]) for data in revenue_data]

    expense_labels = [f"{data['date__month']}/{data['date__year']}" for data in expense_data]
    expense_values = [float(data["total_expense"]) for data in expense_data]

    # Ensure consistent x-axis labels for Revenue vs Expenses
    unified_labels = sorted(set(revenue_labels + expense_labels))
    aligned_revenue = [revenue_values[revenue_labels.index(label)] if label in revenue_labels else 0 for label in unified_labels]
    aligned_expenses = [expense_values[expense_labels.index(label)] if label in expense_labels else 0 for label in unified_labels]

    quick_actions = {
        "add_invoice_url": "finx:invoice_create",
        "add_expense_url": "finx:expense_create",
        "add_journal_entry_url": "finx:journal_entry_create",
    }

    context = {
        "revenue_labels": unified_labels,
        "revenue_values": aligned_revenue,
        "expense_values": aligned_expenses,
        "expense_breakdown_labels": all_labels,
        "expense_breakdown_data": expense_chart_data,
        "net_profit": float(net_profit),
        "receivables": list(receivables),
        "total_revenue": float(revenue_total),
        "total_expenses": float(expense_total),
        "quick_actions": quick_actions,
        "payables": list(payables), 
        'total_receivable': total_receivable,
        'total_payable': total_payable,
        'total_debits': total_debits,
        'total_credits': total_credits,
    }
    return render(request, "finx/dashboard.html", context)



#Exporting

def export_invoices(request):
    # Create the HTTP response with the proper CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="invoices.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Invoice Number', 'Due Date', 'Client Name', 'Client Email', 'Amount (BHD)', 'VAT Amount (BHD)', 'Total Amount (BHD)',  'Status'])

    # Write the data rows
    for invoice in Invoice.objects.all():
        writer.writerow([
            invoice.number, 
            invoice.due_date, 
            invoice.client_name, 
            invoice.client_email, 
            invoice.amount, 
            invoice.vat_amount, 
            invoice.total_amount,    
            invoice.status, 
        ])

    return response

def export_expenses(request):
    # Create the HTTP response with the proper CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Exp No','Date', 'Description', 'Amount (BHD)',  'Category', 'Status'])

    # Write the data rows
    for expense in Expense.objects.all():
        writer.writerow([
            expense.number, 
            expense.date, 
            expense.description, 
            expense.amount,        
            expense.get_category_display(), 
            expense.status, 
        ])

    return response

def export_journal_entries(request):
    # Create the HTTP response with the proper CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="journal_entries.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Entry No', 'Date', 'Description', 'Debit Account', 'Credit Account', 'Amount (BHD)'])

    # Write the data rows
    for entry in JournalEntry.objects.all():
        writer.writerow([
            entry.number,
            entry.date,
            entry.description,
            entry.debit_account.name,
            entry.credit_account.name,
            entry.amount,
        ])

    return response



def create_invoice_function(request, form_data):
    """
    Function to create an invoice either from a request or programmatically.

    Args:
        request (HttpRequest): The request object (only required for messages).
        form_data (dict): Data for the invoice creation.

    Returns:
        Invoice object if successful, None otherwise.
    """
    form = InvoiceForm(form_data)
    
    if form.is_valid():
        try:
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.save()
                if request:
                    messages.success(request, "Invoice created successfully.")
                return invoice
        except Exception as e:
            if request:
                messages.error(request, f"Error creating invoice: {e}")
            logger.error(f"Error creating invoice: {e}")  # Log error
            return None
    else:
        if request:
            messages.error(request, "Invalid form data.")
        logger.error(f"Form errors: {form.errors}")  # Log form errors
        return None
    



def generate_recurring_invoices_working(days_before=10):
    """
    Generate recurring invoices only for the latest invoice of each contract.
    - Invoices are created `days_before` the due date.
    - Ensures invoices are generated until `recurrence_end_date`.
    - Updates due date correctly.

    :param days_before: Number of days before the due date to generate the invoice (default: 10)
    """
    today = timezone.now().date()

    # Get all unique contract IDs that have recurring invoices
    contract_ids = Invoice.objects.filter(is_recurring=True, recurrence_end_date__gte=today).values_list('reference', flat=True).distinct()

    invoices_generated = 0
    invoices_remaining = 0

    logger.info(f"🔍 Checking recurring invoices for {len(contract_ids)} contracts...")

    for contract_id in contract_ids:
        # Fetch the latest invoice for this contract
        invoice = Invoice.objects.filter(reference=contract_id, is_recurring=True).order_by('-due_date').first()
        
        if not invoice:
            continue  # Skip if no valid invoice found
        
        last_due_date = invoice.due_date  # Use last invoice's due date

        # Determine the next due date based on recurrence interval
        if invoice.recurrence_interval == 'daily':
            next_due_date = last_due_date + timedelta(days=1)
        elif invoice.recurrence_interval == 'weekly':
            next_due_date = last_due_date + timedelta(weeks=1)
        elif invoice.recurrence_interval == 'monthly':
            next_due_date = (last_due_date.replace(day=1) + timedelta(days=31)).replace(day=1)  # Move to next month's 1st
        elif invoice.recurrence_interval == 'quarterly':
            next_due_date = (last_due_date.replace(day=1) + timedelta(days=92)).replace(day=1)  # Move to next quarter's 1st
        elif invoice.recurrence_interval == 'yearly':
            next_due_date = last_due_date.replace(year=last_due_date.year + 1, day=1)  # Move to next year's 1st
        else:
            continue  # Skip if recurrence_interval is invalid

        generate_on = next_due_date - timedelta(days=days_before)  # Generate invoice `days_before` due date

        logger.info(f"📅 Contract {contract_id} - Invoice {invoice.number}:")
        logger.info(f"    Last Due Date → {last_due_date}")
        logger.info(f"    Next Due Date → {next_due_date}")
        logger.info(f"    Generate On → {generate_on}")
        logger.info(f"    Today → {today}")

        # If today is past or exactly the generation date, generate the next invoice
        if today >= generate_on and next_due_date <= invoice.recurrence_end_date:
            invoices_generated += 1

            logger.info(f"✅ Creating invoice for {next_due_date} (Generated on {today})")

            # Generate the next invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            next_number = "INV-0001"
            try:
                if last_invoice and '-' in last_invoice.number:
                    prefix, num = last_invoice.number.split('-')
                    next_number = f"{prefix}-{int(num) + 1:04d}"
            except Exception:
                next_number = "INV-0001"  # Fallback

            # Create the new invoice
            new_invoice = Invoice.objects.create(
                number=next_number,
                reference=invoice.reference,
                client_name=invoice.client_name,
                client_email=invoice.client_email,
                amount=invoice.amount,
                due_date=next_due_date,  # Correctly update the due date
                issue_date=today,
                status="unpaid",
                vat_exempt=invoice.vat_exempt,
                currency=invoice.currency,
                vat_rate=invoice.vat_rate,
                is_recurring=True,
                recurrence_interval=invoice.recurrence_interval,
                recurrence_end_date=invoice.recurrence_end_date,
                line_items=invoice.line_items,
            )

            # Update the due date for the next cycle in the new invoice
            new_invoice.due_date = next_due_date
            new_invoice.save()

            logger.info(f"🔄 Updated new invoice {new_invoice.number} due date to {new_invoice.due_date}")

        else:
            invoices_remaining += 1
            logger.info(f"🕒 Contract {contract_id} - Invoice {invoice.number} not yet due (waiting for {days_before}-day rule).")

    logger.info(f"🎯 Total invoices generated: {invoices_generated}")
    logger.info(f"📌 Total invoices remaining to be generated in future: {invoices_remaining}")

    return f"Recurring invoices generated: {invoices_generated}, Remaining: {invoices_remaining}"





def generate_recurring_invoices_2(days_before=15):
    """
    Generate all pending recurring invoices based on the correct recurrence interval.
    - Ensures invoices are generated `days_before` the due date.
    - Generates invoices for all past missed periods (monthly, quarterly, yearly).
    """

    today = timezone.now().date()
    contract_ids = Invoice.objects.filter(is_recurring=True, recurrence_end_date__gte=today).values_list('reference', flat=True).distinct()

    invoices_generated = 0
    invoices_remaining = 0

    logger.info(f"🔍 Checking recurring invoices for {len(contract_ids)} contracts...")

    for contract_id in contract_ids:
        invoice = Invoice.objects.filter(reference=contract_id, is_recurring=True).order_by('-due_date').first()
        
        if not invoice:
            continue  # Skip if no valid invoice found

        last_due_date = invoice.due_date
        recurrence_end_date = invoice.recurrence_end_date
        interval = invoice.recurrence_interval

        while last_due_date < recurrence_end_date:
            # Determine the correct interval jump
            if interval == 'daily':
                next_due_date = last_due_date + timedelta(days=1)
            elif interval == 'weekly':
                next_due_date = last_due_date + timedelta(weeks=1)
            elif interval == 'monthly':
                next_due_date = (last_due_date.replace(day=1) + timedelta(days=31)).replace(day=1)  # Move to next month's 1st
            elif interval == 'quarterly':
                next_due_date = (last_due_date.replace(day=1) + timedelta(days=92)).replace(day=1)  # Move to next quarter's 1st
            elif interval == 'yearly':
                next_due_date = last_due_date.replace(year=last_due_date.year + 1, day=1)  # Move to next year's 1st
            else:
                break  # Invalid recurrence interval

            # Only generate invoices up to the recurrence_end_date
            if next_due_date > recurrence_end_date:
                break

            # Check if the invoice is due for generation
            generate_on = next_due_date - timedelta(days=days_before)

            logger.info(f"📅 Contract {contract_id} - Invoice {invoice.number}:")
            logger.info(f"    Last Due Date → {last_due_date}")
            logger.info(f"    Next Due Date → {next_due_date}")
            logger.info(f"    Generate On → {generate_on}")
            logger.info(f"    Today → {today}")

            # If today is past or exactly the generation date, generate the next invoice
            if today >= generate_on:
                invoices_generated += 1

                logger.info(f"✅ Creating invoice for {next_due_date} (Generated on {today})")

                last_invoice = Invoice.objects.order_by('-id').first()
                next_number = "INV-0001"
                try:
                    if last_invoice and '-' in last_invoice.number:
                        prefix, num = last_invoice.number.split('-')
                        next_number = f"{prefix}-{int(num) + 1:04d}"
                except Exception:
                    next_number = "INV-0001"  # Fallback

                # Create the new invoice
                new_invoice = Invoice.objects.create(
                    number=next_number,
                    reference=invoice.reference,
                    client_name=invoice.client_name,
                    client_email=invoice.client_email,
                    amount=invoice.amount,
                    due_date=next_due_date,  # Correctly update the due date
                    issue_date=today,
                    status="unpaid",
                    vat_exempt=invoice.vat_exempt,
                    currency=invoice.currency,
                    vat_rate=invoice.vat_rate,
                    is_recurring=True,
                    recurrence_interval=invoice.recurrence_interval,
                    recurrence_end_date=invoice.recurrence_end_date,
                    line_items=invoice.line_items,
                )

                logger.info(f"🔄 Created new invoice {new_invoice.number} due date: {new_invoice.due_date}")

                # Move last_due_date forward for the next iteration
                last_due_date = next_due_date
            else:
                invoices_remaining += 1
                logger.info(f"🕒 Contract {contract_id} - Invoice {invoice.number} not yet due (waiting for {days_before}-day rule).")
                break  # Stop if future invoices are not due yet

    logger.info(f"🎯 Total invoices generated: {invoices_generated}")
    logger.info(f"📌 Total invoices remaining to be generated in future: {invoices_remaining}")

    return f"Recurring invoices generated: {invoices_generated}, Remaining: {invoices_remaining}"


def generate_recurring_invoices(days_before=15):
    """
    Generate all pending recurring invoices based on the correct recurrence interval.
    - Ensures invoices are generated `days_before` the due date.
    - Keeps the due date on the same day as the first invoice issue date.
    - Generates invoices for all past missed periods.
    """

    today = timezone.now().date()
    contract_ids = Invoice.objects.filter(is_recurring=True, recurrence_end_date__gte=today).values_list('reference', flat=True).distinct()

    invoices_generated = 0
    invoices_remaining = 0

    logger.info(f"🔍 Checking recurring invoices for {len(contract_ids)} contracts...")

    for contract_id in contract_ids:
        # Get the FIRST invoice for this contract (we need its issue date for correct scheduling)
        first_invoice = Invoice.objects.filter(reference=contract_id, is_recurring=True).order_by('issue_date').first()

        if not first_invoice:
            continue  # Skip if no valid invoice found

        first_due_date = first_invoice.due_date  # The first invoice's due date
        last_invoice = Invoice.objects.filter(reference=contract_id, is_recurring=True).order_by('-due_date').first()
        
        if not last_invoice:
            continue  # Skip if no valid invoice found

        last_due_date = last_invoice.due_date
        recurrence_end_date = last_invoice.recurrence_end_date
        interval = last_invoice.recurrence_interval

        while last_due_date < recurrence_end_date:
            # Get the exact day of the first invoice
            first_invoice_day = first_due_date.day  

            # Determine the next due date based on the first invoice's due date
            if interval == 'daily':
                next_due_date = last_due_date + timedelta(days=1)
            elif interval == 'weekly':
                next_due_date = last_due_date + timedelta(weeks=1)
            elif interval == 'monthly':
                next_due_date = (last_due_date + timedelta(days=31)).replace(day=first_invoice_day)
            elif interval == 'quarterly':
                next_due_date = (last_due_date + timedelta(days=92)).replace(day=first_invoice_day)
            elif interval == 'yearly':
                next_due_date = last_due_date.replace(year=last_due_date.year + 1, day=first_invoice_day)
            else:
                break  # Invalid recurrence interval

            # Ensure the due date is valid for that month (to handle short months like February)
            try:
                next_due_date = next_due_date.replace(day=first_invoice_day)
            except ValueError:
                # If the month doesn't have that day (e.g., Feb 30), default to the last day of the month
                next_due_date = next_due_date.replace(day=1) + timedelta(days=31)
                next_due_date = next_due_date.replace(day=1) - timedelta(days=1)

            # Only generate invoices up to the recurrence_end_date
            if next_due_date > recurrence_end_date:
                break

            # Check if the invoice is due for generation
            generate_on = next_due_date - timedelta(days=days_before)

            logger.info(f"📅 Contract {contract_id} - Invoice {last_invoice.number}:")
            logger.info(f"    Last Due Date → {last_due_date}")
            logger.info(f"    Next Due Date → {next_due_date}")
            logger.info(f"    Generate On → {generate_on}")
            logger.info(f"    Today → {today}")

            # If today is past or exactly the generation date, generate the next invoice
            if today >= generate_on:
                invoices_generated += 1

                logger.info(f"✅ Creating invoice for {next_due_date} (Generated on {today})")

                last_invoice = Invoice.objects.order_by('-id').first()
                next_number = "INV-0001"
                try:
                    if last_invoice and '-' in last_invoice.number:
                        prefix, num = last_invoice.number.split('-')
                        next_number = f"{prefix}-{int(num) + 1:04d}"
                except Exception:
                    next_number = "INV-0001"  # Fallback

                # Create the new invoice
                new_invoice = Invoice.objects.create(
                    number=next_number,
                    reference=last_invoice.reference,
                    client_name=last_invoice.client_name,
                    client_email=last_invoice.client_email,
                    amount=last_invoice.amount,
                    due_date=next_due_date,  # Keep the correct due date
                    issue_date=today,
                    status="unpaid",
                    vat_exempt=last_invoice.vat_exempt,
                    currency=last_invoice.currency,
                    vat_rate=last_invoice.vat_rate,
                    is_recurring=True,
                    recurrence_interval=last_invoice.recurrence_interval,
                    recurrence_end_date=last_invoice.recurrence_end_date,
                    line_items=last_invoice.line_items,
                )

                logger.info(f"🔄 Created new invoice {new_invoice.number} with due date: {new_invoice.due_date}")

                # Move last_due_date forward for the next iteration
                last_due_date = next_due_date
            else:
                invoices_remaining += 1
                logger.info(f"🕒 Contract {contract_id} - Invoice {last_invoice.number} not yet due (waiting for {days_before}-day rule).")
                break  # Stop if future invoices are not due yet

    logger.info(f"🎯 Total invoices generated: {invoices_generated}")
    logger.info(f"📌 Total invoices remaining to be generated in future: {invoices_remaining}")

    return f"Recurring invoices generated: {invoices_generated}, Remaining: {invoices_remaining}"


#For custom payment date 

def mark_invoice_paid(request, pk):
    """
    View to mark an invoice as paid and update related accounts and journal entries.
    """
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'paid':
        messages.warning(request, f"Invoice {invoice.number} is already marked as paid.")
        return redirect('finx:invoice_list')

    try:
        with transaction.atomic():
            # Update the invoice status to 'paid'
            invoice.status = 'paid'
            invoice.save()

            messages.success(request, f"Invoice {invoice.number} has been marked as paid.")
    except Exception as e:
        messages.error(request, f"An error occurred while marking the invoice as paid: {e}")
    
    return redirect('finx:invoice_list')


# ✅ PASTE HERE
def set_payment_date(request, pk):
    """
    View to update the payment date for a paid invoice.
    """
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == "POST":
        payment_date =  request.POST.get("payment_date")
        
        if payment_date:
            formatted_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
            invoice.payment_date = formatted_date
           
            invoice.save()
    
    return redirect("finx:invoice_list")
