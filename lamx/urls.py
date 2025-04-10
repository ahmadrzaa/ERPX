from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import create_invoice_from_contract 



app_name = 'lamx'



urlpatterns = [
    # Contracts URLs
    path('contracts/', views.contract_list, name='contract_list'),
    path('contracts/new/', views.contract_create, name='contract_create'),
    path('contracts/<str:pk>/edit/', views.contract_edit, name='contract_edit'),
    path('contracts/<str:pk>/delete/', views.contract_delete, name='contract_delete'),
    path('contracts/<str:pk>/', views.contract_detail, name='contract_detail'),
    path('contracts/<str:pk>/pdf/', views.generate_contract_pdf, name='contract_pdf'),
    path('contracts/<str:pk>/evacuation_pdf/', views.generate_evacuation_pdf, name='generate_evacuation_pdf'),
    path("contracts/<str:contract_id>/create-invoice/", create_invoice_from_contract, name="create_invoice"),
    path('contracts/<str:contract_number>/invoices/', views.contract_invoices, name='contract_invoices'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
