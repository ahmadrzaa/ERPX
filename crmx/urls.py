from django.urls import path
from . import views

app_name = 'crmx'

urlpatterns = [
    path('', views.crm_list, name='crm_list'),
    path('new/', views.crm_create, name='crm_create'),
    path('<int:pk>/edit/', views.crm_edit, name='crm_edit'),
    path('<int:pk>/delete/', views.crm_delete, name='crm_delete'),
]
