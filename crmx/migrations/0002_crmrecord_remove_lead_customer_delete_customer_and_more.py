# Generated by Django 4.2 on 2024-12-21 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crmx', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CRMRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=15)),
                ('company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('industry', models.CharField(blank=True, choices=[('it', 'IT'), ('finance', 'Finance'), ('manufacturing', 'Manufacturing'), ('healthcare', 'Healthcare'), ('education', 'Education')], max_length=50, null=True)),
                ('contact_person', models.CharField(max_length=255)),
                ('contact_person_role', models.CharField(blank=True, max_length=255, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('status', models.CharField(choices=[('new', 'New'), ('contacted', 'Contacted'), ('qualified', 'Qualified'), ('closed', 'Closed'), ('inactive', 'Inactive')], default='new', max_length=20)),
                ('lead_source', models.CharField(blank=True, max_length=255, null=True)),
                ('assigned_to', models.CharField(blank=True, max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='lead',
            name='customer',
        ),
        migrations.DeleteModel(
            name='Customer',
        ),
        migrations.DeleteModel(
            name='Lead',
        ),
    ]
