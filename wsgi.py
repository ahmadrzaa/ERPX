import os
from django.core.wsgi import get_wsgi_application

# Set the default settings module for your Django project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BSTD.settings')

application = get_wsgi_application()
