# Generated by Django 4.2 on 2024-12-19 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lamx', '0012_contracts_increment_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contracts',
            name='increment_id',
        ),
        migrations.AlterField(
            model_name='contracts',
            name='contract_number',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, unique=True),
        ),
    ]
