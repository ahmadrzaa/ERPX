from django.db import models

class CRMRecord(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('closed', 'Closed'),
        ('inactive', 'Inactive'),
        ('in_progress', 'In Progress'),
        ('follow_up', 'Follow Up'),
        ('awaiting_response', 'Awaiting Response'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    INDUSTRY_CHOICES = [
        ('it', 'IT'),
        ('finance', 'Finance'),
        ('manufacturing', 'Manufacturing'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('real_estate', 'Real Estate'),
        ('hospitality', 'Hospitality'),
        ('transportation', 'Transportation'),
        ('retail', 'Retail'),
        ('construction', 'Construction'),
        ('technology', 'Technology'),
        ('energy', 'Energy'),
        ('consulting', 'Consulting'),
        ('pharmaceutical', 'Pharmaceutical'),
        ('media', 'Media'),
        ('telecommunications', 'Telecommunications'),
    ]


    customer_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, blank=True, null=True)
    contact_person = models.CharField(max_length=255)
    contact_person_role = models.CharField(max_length=255, blank=True, null=True)

    # Bahrain-Specific Address Fields
    building = models.CharField(max_length=50, blank=True, null=True, help_text="Building number")
    road = models.CharField(max_length=50, blank=True, null=True, help_text="Road number")
    block = models.CharField(max_length=50, blank=True, null=True, help_text="Block number")
    area = models.CharField(max_length=100, blank=True, null=True, help_text="Area name")
    city = models.CharField(max_length=100, default="Manama", help_text="City name (e.g., Manama, Muharraq)")

    country = models.CharField(max_length=100, default="Bahrain", help_text="Default is Bahrain")
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    lead_source = models.CharField(max_length=255, blank=True, null=True)
    assigned_to = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.customer_name
