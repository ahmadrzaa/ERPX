from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import CRMRecord
from .forms import CRMRecordForm



def crm_create(request):
    if request.method == 'POST':
        form = CRMRecordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "CRM record created successfully.")
            return redirect('crmx:crm_list')
    else:
        form = CRMRecordForm()
    return render(request, 'crmx/crm_form.html', {'form': form})

def crm_edit(request, pk):
    record = get_object_or_404(CRMRecord, pk=pk)
    if request.method == 'POST':
        form = CRMRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "CRM record updated successfully.")
            return redirect('crmx:crm_list')
    else:
        form = CRMRecordForm(instance=record)
    return render(request, 'crmx/crm_form.html', {'form': form})

def crm_delete(request, pk):
    record = get_object_or_404(CRMRecord, pk=pk)
    record.delete()
    messages.success(request, "CRM record deleted successfully.")
    return redirect('crmx:crm_list')

def crm_list(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # Start with all records
    records = CRMRecord.objects.all()

    # Apply search filter
    if search_query:
        records = records.filter(
            customer_name__icontains=search_query
        ) | records.filter(
            email__icontains=search_query
        ) | records.filter(
            phone__icontains=search_query
        )

    # Apply status filter
    if status_filter:
        records = records.filter(status=status_filter)

    # Render the template
    return render(request, 'crmx/crm_list.html', {'records': records})
