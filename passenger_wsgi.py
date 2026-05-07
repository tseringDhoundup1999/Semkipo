import os
import sys

sys.path.insert(0, "/home2/semkipoc/django_backend/Semkipo")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
