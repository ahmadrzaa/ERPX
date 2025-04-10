from django.db import models
from django.contrib.auth.models import User
from django.db.models import Index
from django.utils.timezone import now  # Import now function


class BusinessIncubator(models.Model):
    number = models.CharField(max_length=20, unique=True)
    is_occupied = models.BooleanField(default=False)
    contract_id = models.CharField(max_length=50, unique=True, editable=False, blank=True, null=True)  # Allow NULL

    def __str__(self):
        return f"{self.number} - {'Occupied' if self.is_occupied else 'Available'}"

    @staticmethod
    def populate_business_incubators():
        """Creates Business Incubators from 01 to 063 if they do not exist."""
        for i in range(1, 64):  # Create IDs 1 to 63
            obj, created = BusinessIncubator.objects.get_or_create(
                id=i,
                #defaults={'number': f'010{i}', 'is_occupied': False}
                defaults={'number': f'01{i:02d}', 'is_occupied': False} 
            )
            if created:
                print(f"Created Business Incubator BI-{i}")
                
    def get_available_incubators():
        """Fetch all available incubator numbers for select choices."""
        return [(incubator.number, incubator.number) for incubator in BusinessIncubator.objects.filter(is_occupied=False)]
    
    @staticmethod
    def get_incubator_by_contract(contract_id):
        try:
            incubator = BusinessIncubator.objects.get(contract_id=contract_id)
            return incubator.number
        except BusinessIncubator.DoesNotExist:
            return None

    @staticmethod
    def free_up_incubator(contract_id):
        """
        Free up the business incubator associated with a given contract ID.
        """
        try:
            incubator = BusinessIncubator.objects.get(contract_id=contract_id)
            incubator.is_occupied = False
            incubator.contract_id = None  # Remove contract reference
            incubator.save()
            print(f"Business Incubator {incubator.number} is now free.")
            return True
        except BusinessIncubator.DoesNotExist:
            print("No incubator found for this contract ID.")
            return False
                    
class Contracts(models.Model):
 # Contract Details
    
   

    contract_number = models.CharField(max_length=50, unique=True, primary_key=True, editable=False)
    package = models.CharField(max_length=255, default="")
    contract_duration = models.DecimalField(max_digits=100, decimal_places=0, blank=True, null=False, default=1)
    contract_effective_date = models.DateField(blank=True, null=True)
    contract_expiration_date = models.DateField(blank=True, null=True)
    actual_rent_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=False, default=0)
    # Property Details
    
    #business_incubator_number = models.CharField( max_length=20, choices= BusinessIncubator.get_available_incubators(), blank=True, null=True)
    business_incubator_number = models.CharField(max_length=20, blank=True, null=True)

    
    
    monthly_rent_fee = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
   
   
    FIRST_PARTY_CHOICES = [
        ("Dr. ABDULLA AL HAMED", "Dr. ABDULLA AL HAMED"),
        ("EYAD ABDULLA MOHAMED FAKHRI", "EYAD ABDULLA MOHAMED FAKHRI"),
    ]

    # Define Arabic equivalents
    FIRST_PARTY_CHOICES_AR = {
        "عبدالله ال حامد": "عبدالله ال حامد",
        "إياد عبد الله محمد فخري": "إياد عبد الله محمد فخري",
    }

    first_party_signatory_name = models.CharField(
        max_length=255,
        choices=FIRST_PARTY_CHOICES,  
        default="Dr. ABDULLA AL HAMED",
    )

    first_party_signatory_name_ar = models.CharField(
        max_length=255,
        choices= FIRST_PARTY_CHOICES_AR.items(),  
        default= "عبدالله ال حامد",
    )
        
    STATUS_CHOICES = [
        (0, "Under Review"),
        (1, "Pending"),
        (2, "Active"),
        (3, "Cancelled"),
        # (4, "Active With SME Regisration"),
    ]

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=0,
        help_text="Contract status (0=Pending, 1=Active, 2=Completed, 3=Cancelled)"
    )
     

    SME_REGISTRATION_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    sme_registration = models.CharField(
        max_length=20,
        choices=SME_REGISTRATION_CHOICES,
        default='pending',
        help_text="SME Registration Status (Pending, In Progress, Completed)"
    )
    

    
    
    
    # First Party Information
    #first_party_signatory_name = models.CharField(max_length=255, default="")
    #first_party_signatory_name_ar = models.CharField(max_length=255, default="")
    first_party_designation = models.CharField(max_length=100, default="Partner")
    first_party_designation_ar = models.CharField(max_length=100, default="شريك")
    first_party_signature_date = models.DateField(blank=True, null=True)

    
    # Second Party Information
    second_party_signatory_name = models.CharField(max_length=255, default="")
    second_party_title = models.CharField(max_length=100, default="")
    second_party_personal_id = models.CharField(max_length=50, blank=True, null=True)
    second_party_commercial_name = models.CharField(max_length=255, blank=True, null=True)
    second_party_commercial_registry_number = models.CharField(max_length=50, blank=True, null=True)
    second_party_signature_date = models.DateField(blank=True, null=True)
    
    second_party_signatory_name_ar = models.CharField(max_length=255, blank=True, null=True)  
    second_party_title_ar = models.CharField(max_length=100, blank=True, null=True) 
    second_party_phone_number = models.CharField(max_length=20, blank=True, null=True) 
    second_party_email = models.EmailField(blank=True, null=True)  
    second_party_commercial_name_ar = models.CharField(max_length=255, blank=True, null=True)  
    # Contract Details
    payment_interval = models.CharField(
        max_length=50,
        choices=[
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ],
        default="monthly",
    )  # Payment Interval

    company_type = models.CharField(
        max_length=50,
        choices=[
            ("startup", "Startup"),
            ("existing", "Existing"),
        ],
        default="startup",
    )  # Company Type

    need_more_assistance = models.TextField(blank=True, null=True)  # Need More Assistance Details

    # Attachments
    cpr_copy = models.FileField(upload_to="uploads/cpr_copy/", blank=True, null=True)  # CPR Copy of Owner
    cr_copy = models.FileField(upload_to="uploads/cr_copy/", blank=True, null=True)  # CR Copy
    cr_extract = models.FileField(upload_to="uploads/cr_extract/", blank=True, null=True)  # CR Extract
    business_brief = models.FileField(upload_to="uploads/business_brief/", blank=True, null=True)  # Business Brief
    
    
    
    class Meta:
        indexes = [
            Index(fields=['contract_number']),
            Index(fields=['second_party_signatory_name']),
        ]



    
    
    def save(self, *args, **kwargs):
        # Generate a contract number if missing
        if not self.contract_number:
            self.contract_number = f"CN-{now().strftime('%Y%m%d')}-{Contracts.objects.count() + 1}"
        
        is_new_contract = self._state.adding  # Check if it's a new contract before saving

        super().save(*args, **kwargs)  # First save to assign `self.pk`

        # Only process incubator updates if the contract is not new
        if not is_new_contract:
            existing_contract = Contracts.objects.get(pk=self.pk)

            # If the incubator number has changed, free the old incubator
            if existing_contract.business_incubator_number and existing_contract.business_incubator_number != self.business_incubator_number:
                old_incubator = BusinessIncubator.objects.filter(number=existing_contract.business_incubator_number).first()
                if old_incubator:
                    old_incubator.is_occupied = False
                    old_incubator.contract_id = None
                    old_incubator.save()
                    print(f"✅ Freed up incubator {old_incubator.number} from contract {existing_contract.contract_number}")

        # Assign new incubator if provided
        if self.business_incubator_number:
            incubator = BusinessIncubator.objects.filter(number=self.business_incubator_number).first()

            if incubator:
                # 🚨 Check if the incubator is already assigned to another contract
                if incubator.contract_id and incubator.contract_id != self.contract_number:
                    raise ValueError(f"❌ ERROR: Incubator {incubator.number} is already assigned to contract {incubator.contract_id}.")

                # Release previous contract's incubator before assigning the new one
                existing_contract_using_incubator = BusinessIncubator.objects.filter(contract_id=self.contract_number).first()
                if existing_contract_using_incubator:
                    existing_contract_using_incubator.is_occupied = False
                    existing_contract_using_incubator.contract_id = None
                    existing_contract_using_incubator.save()
                    print(f"✅ Released incubator {existing_contract_using_incubator.number} before reassigning.")

                # Assign the new incubator
                incubator.is_occupied = True
                incubator.contract_id = self.contract_number
                incubator.save()
                print(f"✅ Assigned incubator {incubator.number} to contract {self.contract_number}")

        # Save again to update incubator assignment changes
        super().save(update_fields=["business_incubator_number"])


    
    def __str__(self):
        return f"{self.contract_number}"
   
    def clean_contract_number(self):
        contract_number = self.cleaned_data.get('contract_number')
        instance = self.instance  
        if LeaseContract.objects.filter(contract_number=contract_number).exclude(pk=instance.pk).exists():
            raise forms.ValidationError("Lease contract with this Contract number already exists.")
        return contract_number
    

   

def contract_attachment_path(instance, filename):
    """Dynamically generate file path for contract attachments"""
    return f"uploads/contracts/{instance.contract_number}/{filename}"
              
#BusinessIncubator.populate_business_incubators()


