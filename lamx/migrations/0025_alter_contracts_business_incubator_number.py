# Generated by Django 4.2 on 2025-01-30 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lamx', '0024_remove_businessincubator_contract_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contracts',
            name='business_incubator_number',
            field=models.CharField(blank=True, choices=[('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'), ('05', '05'), ('06', '06'), ('07', '07'), ('08', '08'), ('09', '09'), ('010', '010'), ('011', '011'), ('012', '012'), ('013', '013'), ('014', '014'), ('015', '015'), ('016', '016'), ('017', '017'), ('018', '018'), ('019', '019'), ('020', '020'), ('021', '021'), ('022', '022'), ('023', '023'), ('024', '024'), ('025', '025'), ('026', '026'), ('027', '027'), ('028', '028'), ('029', '029'), ('030', '030'), ('031', '031'), ('032', '032'), ('033', '033'), ('034', '034'), ('035', '035'), ('036', '036'), ('037', '037'), ('038', '038'), ('039', '039'), ('040', '040'), ('041', '041'), ('042', '042'), ('043', '043'), ('044', '044'), ('045', '045'), ('046', '046'), ('047', '047'), ('048', '048'), ('049', '049'), ('050', '050'), ('051', '051'), ('052', '052'), ('053', '053'), ('054', '054'), ('055', '055'), ('056', '056'), ('057', '057'), ('058', '058'), ('059', '059'), ('060', '060'), ('061', '061'), ('062', '062'), ('063', '063')], max_length=20, null=True),
        ),
    ]
