# Generated by Django 4.2.11 on 2025-03-03 12:14

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "account_type",
                    models.CharField(
                        choices=[
                            ("asset", "Asset"),
                            ("liability", "Liability"),
                            ("equity", "Equity"),
                            ("revenue", "Revenue"),
                            ("expense", "Expense"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "balance",
                    models.DecimalField(
                        decimal_places=2, default=Decimal("0.00"), max_digits=15
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[("BHD", "Bahraini Dinar"), ("USD", "US Dollar")],
                        default="BHD",
                        max_length=10,
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Configuration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "vat_rate",
                    models.DecimalField(
                        decimal_places=2,
                        default=10.0,
                        help_text="Set the VAT rate as a percentage (e.g., 10 for 10%)",
                        max_digits=5,
                    ),
                ),
                (
                    "api_key_exchange",
                    models.CharField(
                        default="",
                        help_text="API KEY for exchange rate (e.g., https://api.exchangerate.host/latest)",
                        max_length=150,
                    ),
                ),
            ],
            options={
                "verbose_name": "Configuration",
                "verbose_name_plural": "Configuration",
            },
        ),
        migrations.CreateModel(
            name="Currency",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        help_text="Currency code (e.g., USD, EUR, BHD)",
                        max_length=3,
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Currency name (e.g., US Dollar, Euro, Bahraini Dinar)",
                        max_length=50,
                    ),
                ),
                (
                    "exchange_rate",
                    models.DecimalField(
                        decimal_places=4,
                        help_text="Exchange rate relative to the base currency",
                        max_digits=10,
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Mark this currency as the default currency",
                    ),
                ),
                (
                    "last_updated",
                    models.DateTimeField(
                        blank=True,
                        help_text="When the exchange rate was last updated",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Currency",
                "verbose_name_plural": "Currencies",
            },
        ),
        migrations.CreateModel(
            name="Expense",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "number",
                    models.CharField(default="EXP-0001", max_length=50, unique=True),
                ),
                ("name", models.CharField(blank=True, max_length=255, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("description", models.CharField(max_length=255)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("date", models.DateField(default=django.utils.timezone.now)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("general", "General"),
                            ("utilities", "Utilities"),
                            ("office", "Office Expenses"),
                            ("employee", "Employee Costs"),
                            ("travel", "Travel and Transport"),
                            ("marketing", "Marketing"),
                            ("professional", "Professional Services"),
                            ("vat", "VAT"),
                            ("miscellaneous", "Miscellaneous"),
                            ("other", "Other"),
                        ],
                        default="general",
                        max_length=50,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("paid", "Paid"), ("unpaid", "Unpaid")],
                        default="unpaid",
                        max_length=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        choices=[
                            ("BHD", "Bahraini Dinar [1.0000]"),
                            ("USD", "US Dollar [0.0000]"),
                            ("INR", "Indian Rupees [0.0000]"),
                        ],
                        default="BHD",
                        max_length=10,
                    ),
                ),
                (
                    "exchange_rate",
                    models.DecimalField(
                        decimal_places=4,
                        default=1.0,
                        help_text="exchange rate",
                        max_digits=10,
                    ),
                ),
                (
                    "vat_rate",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=Decimal("10.00"),
                        max_digits=15,
                        null=True,
                    ),
                ),
                ("number", models.CharField(max_length=50, unique=True)),
                ("reference", models.CharField(blank=True, max_length=100, null=True)),
                ("issue_date", models.DateField(default=django.utils.timezone.now)),
                ("client_name", models.CharField(max_length=255)),
                ("client_email", models.EmailField(max_length=254)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                (
                    "vat_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=15, null=True
                    ),
                ),
                ("due_date", models.DateField(default=django.utils.timezone.now)),
                ("created_date", models.DateField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("unpaid", "Unpaid"), ("paid", "Paid")],
                        default="unpaid",
                        max_length=10,
                    ),
                ),
                ("vat_exempt", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "line_items",
                    models.JSONField(
                        default=list, help_text="List of line items as JSON"
                    ),
                ),
                (
                    "is_recurring",
                    models.BooleanField(
                        default=False, help_text="Mark this invoice as recurring"
                    ),
                ),
                (
                    "recurrence_interval",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                            ("quarterly", "Quarterly"),
                            ("yearly", "Yearly"),
                        ],
                        help_text="Recurrence interval for this invoice",
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    "recurrence_end_date",
                    models.DateField(
                        blank=True,
                        help_text="End date for recurring invoices",
                        null=True,
                    ),
                ),
                (
                    "payment_date",
                    models.DateField(
                        blank=True,
                        default=django.utils.timezone.now,
                        help_text="Manually entered payment date",
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="JournalEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "number",
                    models.CharField(default="JE-0001", max_length=50, unique=True),
                ),
                ("date", models.DateField()),
                ("description", models.TextField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("is_reversal", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "credit_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="credit_entries",
                        to="finx.account",
                    ),
                ),
                (
                    "debit_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debit_entries",
                        to="finx.account",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("model_name", models.CharField(max_length=50)),
                ("object_id", models.CharField(max_length=50)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("CREATE", "Create"),
                            ("UPDATE", "Update"),
                            ("DELETE", "Delete"),
                        ],
                        max_length=10,
                    ),
                ),
                ("description", models.TextField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
