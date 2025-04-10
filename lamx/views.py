from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Contracts, BusinessIncubator
from .forms import ContractsForm
from django.urls import reverse
import os  
from django.conf import settings  # Import settings
from django.http import HttpResponse
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
import requests
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics  
from googletrans import Translator
from datetime import datetime
from finx.views import create_invoice_function, generate_recurring_invoices
from finx.models import Invoice
from django.utils import timezone
from datetime import timedelta
import json  



import arabic_reshaper
from bidi.algorithm import get_display

def translate_text(text, dest_language='en'):
    """
    Translate a given text to the target language.
    
    :param text: The text to be translated.
    :param dest_language: The target language (default is English 'en').
    :return: Translated text.
    """
    if not text:
        return "No text provided"

    translator = Translator()
    try:
        translated = translator.translate(text, dest=dest_language)
        return translated.text
    except Exception as e:
        return f"Translation error: {str(e)}"

def contract_form(request, pk=None):
    contract = get_object_or_404(Contracts, pk=pk) if pk else None

    if request.method == 'POST':
        form = ContractsForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, "Contract saved successfully.")
            return redirect('lamx:contract_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContractsForm(instance=contract)

    return render(request, 'lamx/contract_form.html', {'form': form, 'contract': contract})



def contract_edit(request, pk):
    contract = get_object_or_404(Contracts, pk=pk)  # Fetch the contract object
     
    assigned_incubator = BusinessIncubator.get_incubator_by_contract(contract.contract_number)
   
  
    basic_attachments, extra_attachments = fetch_attachments_by_id(contract.contract_number)

    

    if request.method == 'POST':
        form = ContractsForm(request.POST, request.FILES, instance=contract)  # Include request.FILES for file uploads
        if form.is_valid():
            form.save()
            messages.success(request, "Contract updated successfully.")
            if  contract.status == 0:
                contract.status = 1
                contract.save()
            return redirect('lamx:contract_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContractsForm(instance=contract)

    # Pass both the form and the contract object to the template
    return render(request, 'lamx/contract_form.html', {
        'form': form,
        'contract': contract,  # Include the contract object for file URLs
        'assigned_incubator': assigned_incubator,
        'editing': True,
        'basic_attachments': basic_attachments,
        'extra_attachments': extra_attachments,
        
    })



def fetch_attachments_by_id(person_id):
    """
    Fetch attachments for a specific person_id from the API.
    Returns two separate values:
    - Basic attachments (dict)
    - Extra attachments (list)
    """
    api_url = "https://lamx.intermid.net/api"
    key = "9543287642dawefqwj65fagdsa4hfdsxgdg4535423"

    headers = {
        "User-Agent": "PostmanRuntime/7.43.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(f"{api_url}?key={key}", headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success" and "data" in data:
            for record in data["data"]:
                if str(record.get("id")) == str(person_id):  # Match the requested ID
                    
                    # Get basic attachments (as a dictionary)
                    basic_attachments = record.get("data", {}).get("attachments", {})

                    # Get extra attachments (comma-separated string)
                    extra_attachments_str = record.get("extra_attachments", "").strip(",")

                    # Convert extra attachments into a list (if not empty)
                    extra_attachments = extra_attachments_str.split(",") if extra_attachments_str else []

                    return basic_attachments, extra_attachments  # Return both separately

            return {}, []  # Return empty values if ID not found
        else:
            return {}, []  # Return empty values in case of error
    except requests.exceptions.RequestException as e:
        return {}, []  # Return empty values on request error

def contract_delete(request, pk):
    # Get the contract object
    contract = get_object_or_404(Contracts, pk=pk)

    # Free up the business incubator
    if contract.business_incubator_number:
        BusinessIncubator.free_up_incubator(contract.contract_number)
    
    # API parameters
    api_url = "https://lamx.intermid.net/api"
    api_key = "9543287642dawefqwj65fagdsa4hfdsxgdg4535423"
    payload = {
        "key": api_key,
        "id": contract.contract_number,
        "st": 1,  # Status to update
    }
    headers = {
            "User-Agent": "PostmanRuntime/7.43.0",  # Mimic Postman user agent
            "Accept": "application/json",          # Specify you want JSON response
            "Accept-Encoding": "gzip, deflate, br",  # Handle compression
            "Connection": "keep-alive",            # Maintain persistent connection
        }

    # Perform the API call to update status
    try:
        response = requests.get(api_url, params=payload, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        api_response = response.json()

        if api_response.get("status") == "success":
            messages.success(request, "Status updated successfully via API.")
        else:
            messages.error(request, f"Failed to update status via API: {api_response.get('message', 'Unknown error')}")
    except requests.RequestException as e:
        messages.error(request, f"Error during API call: {str(e)}")

    # Delete the contract
    contract.delete()
    messages.success(request, "Contract deleted successfully.")
    return redirect(reverse('lamx:contract_list'))

def contract_list(request):
    # Fetch and save data from the API
    result = fetch_api_data()

    # Retrieve query parameters for filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    package = request.GET.get('package')

    # Base queryset for contracts
    contracts = Contracts.objects.all()

    # Apply filters based on user selection
    if start_date:
        contracts = contracts.filter(contract_effective_date__gte=start_date)
    if end_date:
        contracts = contracts.filter(contract_expiration_date__lte=end_date)
    if status:
        contracts = contracts.filter(status=status)
    if package:
        contracts = contracts.filter(package=package)

    # Get unique package choices
    package_choices = Contracts.objects.values_list('package', flat=True).distinct()

    # Get contract statistics
    total_contracts = Contracts.objects.count()
    active_contracts = Contracts.objects.filter(contract_expiration_date__gte=timezone.now().date()).count()
    expired_contracts = Contracts.objects.filter(contract_expiration_date__lt=timezone.now().date()).count()

    context = {
        'contracts': contracts,
        'total_contracts': total_contracts,
        'active_contracts': active_contracts,
        'expired_contracts': expired_contracts,
        'fetch_result': result,
        'status_choices': Contracts.STATUS_CHOICES,  # Pass status choices to template
        'package_choices': package_choices,  # Pass unique package choices
    }

    return render(request, 'lamx/contract_list.html', context)

def contract_detail(request, pk):
    contract = get_object_or_404(Contracts, pk=pk)
    context = {'contract': contract}
    return render(request, 'lamx/contract_detail.html', context)


def contract_create(request):
    if request.method == 'POST':
        form = ContractsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contract created successfully.")
            return redirect('lamx:contract_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContractsForm()
    return render(request, 'lamx/contract_form.html', {'form': form})


# def generate_contract_pdf(request, pk):
#     from PyPDF2.errors import PdfReadError

#     # Get contract data
#     try:
#         contract = Contracts.objects.get(pk=pk)
#     except Contracts.DoesNotExist:
#         return HttpResponse("Contract not found.", status=404)

#     # Template and output file paths
#     template_path = os.path.join(settings.BASE_DIR, 'templates', 'pdf_templates', 'Platform _Agreement.pdf')

#     if not os.path.exists(template_path):
#         return HttpResponse("PDF template not found.", status=404)

#     output = BytesIO()

#     # Create a writable PDF
#     try:
#         reader = PdfReader(template_path)
#     except PdfReadError:
#         return HttpResponse("Failed to read the PDF template.", status=500)

#     writer = PdfWriter()

#     # Validate the number of pages
#     total_pages = len(reader.pages)
#     if total_pages != 6:
#         return HttpResponse(f"Unexpected number of pages in template. Expected 6, got {total_pages}.", status=500)


#     font_path = os.path.join(settings.BASE_DIR, 'static/fonts', 'NotoNaskhArabic-Regular.ttf')
#     pdfmetrics.registerFont(TTFont('Arabic', font_path))
    
#     font_path = os.path.join(settings.BASE_DIR, 'static/fonts', 'Calibri.ttf')
#     # Register the font with ReportLab
#     pdfmetrics.registerFont(TTFont('Calibri', font_path))
    
#     # Fill data into the template
#     for page_number in range(total_pages):
#         packet = BytesIO()
#         # In the provided Python code snippet, `can` is an instance of the
#         # `reportlab.pdfgen.canvas.Canvas` class. It is used to draw text and shapes onto a PDF page.
#         # The `can` object is created for each page of the PDF template, and text is added to specific
#         # coordinates on each page using the `drawString` method.
        
        
#         can = canvas.Canvas(packet)
       
       
    
#         # Add data to specific pages
#         can.setFont("Calibri", 10) 
#         if page_number == 0: 
#              can.drawString(117, 253, f"{contract.package} ("f"{contract.payment_interval})")
      
#              can.setFont("Arabic", 10) 
#              can.drawString(345, 260, "( "+ translate_text(contract.payment_interval,"ar")+" ) " + translate_text(contract.package, "ar"))
#              can.setFont("Calibri", 10)
#         elif page_number == 1: 
#             #can.drawString(138, 382, f"{contract.second_party_commercial_name.upper()} (" f"{contract.second_party_commercial_registry_number} )")
#              can.drawString(138, 382, f"{contract.second_party_commercial_name.upper()}")
#              can.setFont("Arabic", 10) 
#              if contract.second_party_commercial_name_ar:
#                 #can.drawString(355, 372, f"( {contract.second_party_commercial_registry_number} )"f" {contract.second_party_commercial_name_ar}")    
#                 can.drawString(300, 365,contract.second_party_commercial_name_ar)    
#              can.setFont("Calibri", 10)
             
#              can.drawString(150, 237, f"{contract.contract_duration} Months")
             
#              can.setFont("Arabic", 10) 
             
#              can.drawString(350, 237, f"{contract.contract_duration}" + translate_text("Months", "ar"))
             
#              can.setFont("Calibri", 10)
             
#              can.drawString(175, 214, f"{contract.contract_effective_date}")
#              can.drawString(350, 214, f"{contract.contract_effective_date}")
#              can.drawString(180, 188, f"{contract.contract_expiration_date}")
#              can.drawString(350, 188, f"{contract.contract_expiration_date}")
#         elif page_number == 2:  
#              can.drawString(100, 750, " ")
#         elif page_number == 3:  # Page 4
#              can.drawString(100, 750, " ")
#         elif page_number == 4:  # Page 5
#             can.drawString(110, 488, f"[ BHD {contract.monthly_rent_fee} ]")
#             can.drawString(302, 510, f"[BHD {contract.monthly_rent_fee}]")
            
#             can.setFont("Calibri", 11)
            
#             can.drawString(140, 243, f"{contract.second_party_signatory_name.title()}")
            
#             can.setFont("Arabic", 10)   
#             if contract.second_party_signatory_name_ar:                                          
#                can.drawString(370, 239, contract.second_party_signatory_name_ar)
               
#             can.setFont("Calibri", 11)            
#             can.drawString(190, 220, f"{contract.second_party_title}")
#             can.setFont("Arabic", 10) 
#             if contract.second_party_title_ar:
#                #contract.second_party_title_ar=  translate_text(contract.second_party_title, "ar")        
#                can.drawString(370, 220, f"{contract.second_party_title_ar}")
            
#             can.drawString(190, 200, f"{contract.second_party_personal_id}")
#             can.drawString(370, 200, f"{contract.second_party_personal_id}")
#             can.drawString(130, 175, f"{contract.second_party_commercial_name.upper()}")
            
#             can.setFont("Arabic", 10) 
#             if contract.second_party_commercial_name_ar:                  
#                can.drawString(370, 180, contract.second_party_commercial_name_ar )   
            
#             can.setFont("Calibri", 10)
            
#             can.drawString(190, 155, f"{contract.second_party_commercial_registry_number}")
#             can.drawString(370, 155, f"{contract.second_party_commercial_registry_number}")               
#             can.drawString(190, 110, f"{contract.second_party_signature_date}")
#             can.drawString(370, 100, f"{contract.second_party_signature_date}")
            
#         elif page_number == 5:  # Page 6
#             can.setFont("Calibri", 11)
#             can.drawString(145, 518, f"{contract.first_party_signatory_name.title()}")
#             can.setFont("Arabic", 10) 
#             if contract.first_party_signatory_name_ar=="":
#                contract.first_party_signatory_name_ar=  translate_text(contract.first_party_signatory_name, "ar") 
               
#             can.drawString(390, 518, f"{contract.first_party_signatory_name_ar}")
#             can.setFont("Calibri", 10)
#             can.drawString(145, 500, f"{contract.first_party_designation}")
            
#             can.setFont("Arabic", 10) 
#             if contract.first_party_designation_ar=="":
#                contract.first_party_designation_ar=  translate_text(contract.first_party_designation, "ar") 
#             can.drawString(390, 500, f"{contract.first_party_designation_ar}")
#             can.setFont("Calibri", 10)
            
#             can.drawString(90, 460, f"{contract.first_party_signature_date}")
#             can.drawString(390, 450, f"{contract.first_party_signature_date}")
            
#             can.drawString(90, 415, f"{contract.business_incubator_number}")
#             can.drawString(390, 420, f"{contract.business_incubator_number}")
#             can.drawString(140, 380, f"BHD {contract.monthly_rent_fee}")
#             can.drawString(390, 380, f"BHD {contract.monthly_rent_fee}")

#         can.save()
#         packet.seek(0)
#         new_pdf = PdfReader(packet)

#         # Merge the new page with the original
#         try:
#             reader.pages[page_number].merge_page(new_pdf.pages[0])
#         except IndexError:
#             continue  # Skip if the page does not exist
#         writer.add_page(reader.pages[page_number])

#     writer.write(output)
#     output.seek(0)

#     # Return the PDF as a response
#     response = HttpResponse(output, content_type="application/pdf")
#     response["Content-Disposition"] = f"inline; filename=contract_{contract.contract_number}.pdf"
#     return response


# Function to convert English numbers to Arabic numbers
def convert_to_arabic_numbers(number):
    arabic_digits = {'0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
                     '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'}
    return ''.join(arabic_digits[digit] if digit in arabic_digits else digit for digit in str(number))



def generate_contract_pdf(request, pk):
    from PyPDF2.errors import PdfReadError

    # Get contract data
    try:
        contract = Contracts.objects.get(pk=pk)
    except Contracts.DoesNotExist:
        return HttpResponse("Contract not found.", status=404)

    # Template and output file paths
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'pdf_templates', 'Platform _Agreement.pdf')

    if not os.path.exists(template_path):
        return HttpResponse("PDF template not found.", status=404)

    output = BytesIO()

    # Create a writable PDF
    try:
        reader = PdfReader(template_path)
    except PdfReadError:
        return HttpResponse("Failed to read the PDF template.", status=500)

    writer = PdfWriter()

    # Validate the number of pages
    total_pages = len(reader.pages)
    if total_pages != 6:
        return HttpResponse(f"Unexpected number of pages in template. Expected 6, got {total_pages}.", status=500)

    # Register fonts
    font_path_ar = os.path.join(settings.BASE_DIR, 'static/fonts', 'NotoNaskhArabic-Regular.ttf')
    pdfmetrics.registerFont(TTFont('Arabic', font_path_ar))
    
    font_path_en = os.path.join(settings.BASE_DIR, 'static/fonts', 'Calibri.ttf')
    pdfmetrics.registerFont(TTFont('Calibri', font_path_en))

    # Fill data into the template
    for page_number in range(total_pages):
        packet = BytesIO()
        can = canvas.Canvas(packet)

        # Add data to specific pages
        can.setFont("Calibri", 10) 
        
        if page_number == 0: 
            # Reshape Arabic Text
            reshaped_package = get_display(arabic_reshaper.reshape(translate_text(contract.package, "ar")))
            reshaped_payment_interval = get_display(arabic_reshaper.reshape(translate_text(contract.payment_interval, "ar")))

            can.drawString(117, 253, f"{contract.package} ({contract.payment_interval})")
            can.setFont("Arabic", 10) 
            can.drawString(345, 260, f"( {reshaped_payment_interval} ) {reshaped_package}")
            can.setFont("Calibri", 10)

        elif page_number == 1: 
            can.drawString(138, 382, f"{contract.second_party_commercial_name.upper()}")

            if contract.second_party_commercial_name_ar:
                reshaped_name_ar = get_display(arabic_reshaper.reshape(contract.second_party_commercial_name_ar))
                can.setFont("Arabic", 10) 
                can.drawString(300, 365, reshaped_name_ar)    

            can.setFont("Calibri", 10)
            can.drawString(150, 237, f"{contract.contract_duration} Months")

            reshaped_months = get_display(arabic_reshaper.reshape(translate_text("Months", "ar")))
            can.setFont("Arabic", 10) 
            can.drawString(350, 237, f"{contract.contract_duration} {reshaped_months}")

            can.setFont("Calibri", 10)
            can.drawString(175, 214, f"{contract.contract_effective_date}")
            can.drawString(350, 214, f"{contract.contract_effective_date}")
            can.drawString(180, 188, f"{contract.contract_expiration_date}")
            can.drawString(350, 188, f"{contract.contract_expiration_date}")

        elif page_number == 2:  
            can.drawString(100, 750, " ")
        elif page_number == 3:  
            can.drawString(100, 750, " ")
        elif page_number == 4:  
            can.drawString(110, 488, f"[ BHD {contract.monthly_rent_fee} ]")
            can.drawString(302, 510, f"[BHD {contract.monthly_rent_fee}]")
            can.setFont("Calibri", 11)
            can.drawString(140, 243, f"{contract.second_party_signatory_name.title()}")

            if contract.second_party_signatory_name_ar:                                          
                reshaped_signatory_name = get_display(arabic_reshaper.reshape(contract.second_party_signatory_name_ar))
                can.setFont("Arabic", 10)   
                can.drawString(370, 239, reshaped_signatory_name)
               
            can.setFont("Calibri", 11)            
            can.drawString(190, 220, f"{contract.second_party_title}")

            if contract.second_party_title_ar:
                reshaped_title = get_display(arabic_reshaper.reshape(contract.second_party_title_ar))
                can.setFont("Arabic", 10) 
                can.drawString(370, 220, reshaped_title)
            
            can.setFont("Calibri", 10)
            can.drawString(190, 200, f"{contract.second_party_personal_id}")
            can.drawString(370, 200, f"{contract.second_party_personal_id}")
            can.drawString(130, 175, f"{contract.second_party_commercial_name.upper()}")

            if contract.second_party_commercial_name_ar:                  
                reshaped_commercial_name = get_display(arabic_reshaper.reshape(contract.second_party_commercial_name_ar))
                can.setFont("Arabic", 10) 
                can.drawString(370, 180, reshaped_commercial_name)   

            can.setFont("Calibri", 10)
            can.drawString(190, 155, f"{contract.second_party_commercial_registry_number}")
            can.drawString(370, 155, f"{contract.second_party_commercial_registry_number}")               
            can.drawString(190, 110, f"{contract.second_party_signature_date}")
            can.drawString(370, 100, f"{contract.second_party_signature_date}")

        elif page_number == 5:  
            can.setFont("Calibri", 11)
            can.drawString(145, 518, f"{contract.first_party_signatory_name.title()}")

            if contract.first_party_signatory_name_ar:
                reshaped_signatory_name_first = get_display(arabic_reshaper.reshape(contract.first_party_signatory_name_ar))
                can.setFont("Arabic", 10) 
                can.drawString(390, 518, reshaped_signatory_name_first)

            can.setFont("Calibri", 10)
            can.drawString(145, 500, f"{contract.first_party_designation}")

            if contract.first_party_designation_ar:
                reshaped_designation = get_display(arabic_reshaper.reshape(contract.first_party_designation_ar))
                can.setFont("Arabic", 10) 
                can.drawString(390, 500, reshaped_designation)

            can.setFont("Calibri", 10)
            can.drawString(90, 460, f"{contract.first_party_signature_date}")
            can.drawString(390, 450, f"{contract.first_party_signature_date}")
            can.drawString(90, 415, f"{contract.business_incubator_number}")
            can.drawString(390, 420, f"{contract.business_incubator_number}")
            can.drawString(140, 380, f"BHD {contract.monthly_rent_fee}")
            can.drawString(390, 380, f"BHD {contract.monthly_rent_fee}")

        can.save()
        packet.seek(0)
        new_pdf = PdfReader(packet)
        reader.pages[page_number].merge_page(new_pdf.pages[0])
        writer.add_page(reader.pages[page_number])

    writer.write(output)
    output.seek(0)
    response = HttpResponse(output, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=contract_{contract.contract_number}.pdf"
    return response













def generate_evacuation_pdf(request, pk):
    from PyPDF2.errors import PdfReadError

    # Get contract data
    try:
        contract = Contracts.objects.get(pk=pk)
    except Contracts.DoesNotExist:
        return HttpResponse("Contract not found.", status=404)

    # Template and output file paths
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'pdf_templates', 'Platform_evacuation.pdf')

    if not os.path.exists(template_path):
        return HttpResponse("PDF template not found.", status=404)

    output = BytesIO()

    # Create a writable PDF
    try:
        reader = PdfReader(template_path)
    except PdfReadError:
        return HttpResponse("Failed to read the PDF template.", status=500)

    writer = PdfWriter()

    # Validate the number of pages
    total_pages = len(reader.pages)
    if total_pages != 2:
        return HttpResponse(f"Unexpected number of pages in template. Expected 6, got {total_pages}.", status=500)


    font_path = os.path.join(settings.BASE_DIR, 'static/fonts', 'NotoNaskhArabic-Regular.ttf')
    pdfmetrics.registerFont(TTFont('Arabic', font_path))
    
    font_path = os.path.join(settings.BASE_DIR, 'static/fonts', 'Calibri.ttf')
    # Register the font with ReportLab
    pdfmetrics.registerFont(TTFont('Calibri', font_path))
    
    # Fill data into the template
    for page_number in range(total_pages):
        packet = BytesIO()
        # In the provided Python code snippet, `can` is an instance of the
        # `reportlab.pdfgen.canvas.Canvas` class. It is used to draw text and shapes onto a PDF page.
        # The `can` object is created for each page of the PDF template, and text is added to specific
        # coordinates on each page using the `drawString` method.
        
        
        can = canvas.Canvas(packet)
        today_date = datetime.today().strftime('%Y-%m-%d')
       
    
        # Add data to specific pages
        can.setFont("Calibri", 11) 
        if page_number == 0: 
             can.drawString(164, 465, f"{contract.business_incubator_number}")
             can.drawString(258, 433, f"{contract.contract_expiration_date}")

             can.drawString(307, 277, f"{contract.business_incubator_number}")
             can.drawString(130, 233, f"{contract.contract_expiration_date}")
           
        elif page_number == 1: 
           
             can.drawString(240, 516, f"{contract.second_party_signatory_name}")  # First Line
             can.drawString(240, 495, f"{contract.second_party_title}")  # 518 - 23
             can.drawString(240, 465, f"{contract.second_party_personal_id}")  # 495 - 23
             can.drawString(240, 433, f"{contract.second_party_commercial_name}")  # 472 - 23
             can.drawString(240, 400, f"{contract.second_party_commercial_registry_number}")  # 449 - 23
             can.drawString(240, 368, f"{contract.business_incubator_number}")  # 426 - 23
             can.drawString(240, 343, f"{contract.contract_duration}")  # 403 - 23
             can.drawString(240, 320, f"{contract.contract_effective_date}")  # No change
             can.drawString(240, 295, f"{contract.contract_expiration_date}")  # No change           
             can.drawString(240, 245, today_date)
             can.drawString(240, 195, f"{contract.first_party_signatory_name}")
             can.drawString(240, 170, f"{contract.first_party_designation}")
             can.drawString(240, 120, today_date)
          
       
        

        can.save()
        packet.seek(0)
        new_pdf = PdfReader(packet)

        # Merge the new page with the original
        try:
            reader.pages[page_number].merge_page(new_pdf.pages[0])
        except IndexError:
            continue  # Skip if the page does not exist
        writer.add_page(reader.pages[page_number])

    writer.write(output)
    output.seek(0)

    # Return the PDF as a response
    response = HttpResponse(output, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=contract_{contract.contract_number}.pdf"
    return response

def fetch_api_data():
    api_url = "https://lamx.intermid.net/api"
    key = "9543287642dawefqwj65fagdsa4hfdsxgdg4535423"

    headers = {
        "User-Agent": "PostmanRuntime/7.43.0",  # Mimic Postman user agent
        "Accept": "application/json",          # Specify you want JSON response
        "Accept-Encoding": "gzip, deflate, br",  # Handle compression
        "Connection": "keep-alive",            # Maintain persistent connection
    }

    try:
        #print("Fetching data from the API...")
        response = requests.get(f"{api_url}?key={key}", headers=headers)
        #print("API Response Status Code:", response.status_code)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        
        
        #print("API Response Data:", data)
        if data.get("status") == "success" and "data" in data:
            for record in data["data"]:
               
                save_contract_from_api(record)  # Save data to the database
            return f"Successfully processed {len(data['data'])} records."
        else:
            return f"Error: {data.get('error', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        print("Request Exception:", e)
        return f"Request Error: {e}"
    
    
def save_contract_from_api(record):
    try:
        data = record.get("data", {})
        attachments = data.get("attachments", {})
        user_details = data.get("user_details", {})
        contract_details = data.get("contract_details", {})
        
        # Attempt to create the contract, but skip if it already exists
        contract, created = Contracts.objects.get_or_create(
            contract_number=record.get("id"),  # Use "id" from the API as the contract number
            defaults={
                "business_incubator_number": None,
                "package": data.get("package", ""),
                "contract_duration": contract_details.get("contract_duration", 1),
                "payment_interval": contract_details.get("payment_interval", "monthly"),
                "company_type": contract_details.get("company_type", "startup"),
                "need_more_assistance": contract_details.get("need_more_assistance", ""),
                
                # Attachments
                "cpr_copy": attachments.get("cpr_copy", ""),
                "cr_copy": attachments.get("cr_copy", ""),
                "cr_extract": attachments.get("cr_extract", ""),
                "business_brief": attachments.get("business_brief", ""),

                # User Details
                "second_party_signatory_name": user_details.get("full_name", {}).get("en", ""),
                "second_party_signatory_name_ar": user_details.get("full_name", {}).get("ar", ""),
                "second_party_title": user_details.get("title", {}).get("en", ""),
                "second_party_title_ar": user_details.get("title", {}).get("ar", ""),
                "second_party_personal_id": user_details.get("personal_id", ""),
                "second_party_phone_number": user_details.get("phone_number", ""),
                "second_party_email": user_details.get("email", ""),
                "second_party_commercial_name": user_details.get("commercial_name", {}).get("en", ""),
                "second_party_commercial_name_ar": user_details.get("commercial_name", {}).get("ar", ""),
                "second_party_commercial_registry_number": user_details.get("commercial_registry_number", ""),
            }
        )
        
        # Print message for logging
        if created:
            print(f"Contract created: {contract.contract_number}")
        else:
            print(f"Contract already exists, skipping: {contract.contract_number}")

    except Exception as e:
        print(f"Error saving contract: {e}")





    

def create_invoice_from_contract(request, contract_id):
    contract = get_object_or_404(Contracts, contract_number=contract_id)
    if contract.status != 1:
        messages.error(request, "❌ Invoice cannot be created.")
        return redirect("lamx:contract_list")      
    due_date = contract.contract_effective_date 

    last_invoice = Invoice.objects.order_by('-id').first()
    next_number="INV-0001"
    try:
        if last_invoice and '-' in last_invoice.number:
            prefix, num = last_invoice.number.split('-')
            next_number = f"{prefix}-{int(num) + 1:04d}"
        else:
            next_number = "INV-0001"  # Default to the first number
    except Exception:
        next_number = "INV-0001"  # Fallback in case of malformed data
     
    interval= contract.payment_interval
    total_amount=contract.monthly_rent_fee; 
    quantity=1     
    if interval == 'monthly':
       quantity=1     
      
    elif interval == 'quarterly':
       quantity=3   
    elif interval == 'yearly':
       quantity=12  
    
    total_amount=total_amount*quantity
    
    invoice_data = {
        "number": next_number,
        "reference": contract_id,
        "client_name": contract.second_party_signatory_name or "Unknown Client",
        "client_email": contract.second_party_email or "unknown@example.com",
        "amount": contract.monthly_rent_fee or 0.0,
        "due_date": due_date,
        "issue_date": timezone.now().date(),
        "status": "unpaid",
        "is_recurring": True,
        "recurrence_interval": contract.payment_interval or "monthly",
        "recurrence_end_date": contract.contract_expiration_date,
        "vat_exempt": False,
        "currency": "BHD",
        "vat_rate": 10,
        "line_items": json.dumps([ 
            {
                "item": f"Rental Payment for {contract.business_incubator_number or 'N/A'}",
                "quantity": quantity,
                "unit_price": float(contract.monthly_rent_fee or 0.0),
                "line_total": float(total_amount or 0.0)  
            }
        ]),
    }

    print("✅ Creating Invoice with Data:", invoice_data)  

    # Call `create_invoice_function` from `finx`
    invoice = create_invoice_function(request, invoice_data)

    if invoice:
        generate_recurring_invoices(15)
        messages.success(request, f"✅ Invoice {invoice.number} created successfully.")
        contract.status=2
        contract.save()
    else:
        messages.error(request, "❌ Failed to create invoice. Check logs for errors.")

    return redirect("lamx:contract_list")


def contract_invoices(request, contract_number):
    """
    Fetch all invoices related to the contract number.
    """
    contract = get_object_or_404(Contracts, contract_number=contract_number)
    invoices = Invoice.objects.filter(reference=contract_number)

    # Count Paid and Unpaid Invoices
    total_invoices = invoices.count()
    paid_invoices = invoices.filter(status='paid').count()
    unpaid_invoices = invoices.filter(status='unpaid').count()

    return render(request, 'lamx/contract_invoices.html', {
        'contract': contract,
        'invoices': invoices,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'unpaid_invoices': unpaid_invoices
    })
