from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = "Fix inconsistent migration history for employee and erpx_audit"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations WHERE app = 'employee'")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'erpx_audit'")
        self.stdout.write(self.style.SUCCESS("Deleted migration records for 'employee' and 'erpx_audit'."))
