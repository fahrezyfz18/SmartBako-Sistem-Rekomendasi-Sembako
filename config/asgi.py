
"""
Pengaturan ASGI untuk proyek SmartBako.

File ini digunakan untuk menjalankan aplikasi
Django melalui server yang mendukung ASGI.
"""

import os

from django.core.asgi import get_asgi_application


# Menghubungkan Django dengan file settings.py.
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

# Membuat aplikasi ASGI.
application = get_asgi_application()
