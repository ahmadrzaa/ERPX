# Generated by Django 4.2.11 on 2024-11-25 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0010_employee_grade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='grade',
            field=models.PositiveIntegerField(choices=[(0, 'Grade 1'), (322, 'Grade 2'), (327, 'Grade 3'), (348, 'Grade 4'), (377, 'Grade 5'), (420, 'Grade 6'), (467, 'Grade 7'), (526, 'Grade 8'), (616, 'Grade 9'), (768, 'Grade 10')], default=2),
        ),
    ]
