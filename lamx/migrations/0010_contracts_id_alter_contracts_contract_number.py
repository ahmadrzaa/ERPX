# Generated by Django 4.2 on 2024-12-19 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lamx', '0009_remove_contracts_id_alter_contracts_contract_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='contracts',
            name='id',
            field=models.BigAutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contracts',
            name='contract_number',
            field=models.CharField(default='', max_length=50, unique=True),
        ),
    ]
