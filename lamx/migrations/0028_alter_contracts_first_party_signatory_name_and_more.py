# Generated by Django 4.2.11 on 2025-02-10 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lamx', '0027_contracts_first_party_designation_ar_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contracts',
            name='first_party_signatory_name',
            field=models.CharField(choices=[('John Doe', 'John Doe'), ('Jane Smith', 'Jane Smith'), ('Ali Ahmed', 'Ali Ahmed'), ('Fatima Hassan', 'Fatima Hassan')], default='John Doe', max_length=255),
        ),
        migrations.AlterField(
            model_name='contracts',
            name='first_party_signatory_name_ar',
            field=models.CharField(choices=[('جون دو', 'جون دو'), ('جين سميث', 'جين سميث'), ('علي أحمد', 'علي أحمد'), ('فاطمة حسن', 'فاطمة حسن')], default='جون دو', max_length=255),
        ),
    ]
