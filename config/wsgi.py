
"""
Pengaturan WSGI untuk proyek SmartBako.

File ini digunakan untuk menjalankan aplikasi
Django melalui server yang mendukung WSGI.
"""

import os

from django.core.wsgi import get_wsgi_application


# Menghubungkan Django dengan file settings.py.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

# Membuat aplikasi WSGI.
application = get_wsgi_application()
