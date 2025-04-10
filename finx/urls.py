from django.urls import path
from . import views

app_name = 'finx'

urlpatterns = [
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='home'),
    # Accounts
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/new/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),

    # Journal Entries
    path('journal_entries/', views.journal_entry_list, name='journal_entry_list'),
    path('journal_entries/new/', views.journal_entry_create, name='journal_entry_create'),
    path('journal_entries/<int:pk>/edit/', views.journal_entry_edit, name='journal_entry_edit'),
    
    path('journal_entry/<int:pk>/reverse/', views.journal_entry_reverse, name='journal_entry_reverse'),
    

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/new/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/mark_paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('invoice/<int:pk>/set-payment-date/', views.set_payment_date, name='set_payment_date'),
    
    
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/new/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/<int:pk>/mark_paid/', views.mark_expense_paid, name='mark_expense_paid'),
    
    
    #Exporting
    path('invoices/export/', views.export_invoices, name='export_invoices'),
    path('expenses/export/', views.export_expenses, name='export_expenses'),
    path('journal_entries/export/', views.export_journal_entries, name='export_journal_entries'),
    
    
    
    #print
    path('invoices/<int:invoice_id>/print/', views.print_invoice, name='print_invoice'),
    path('receipts/<int:receipt_id>/print/', views.print_receipt, name='print_receipt'),



]
