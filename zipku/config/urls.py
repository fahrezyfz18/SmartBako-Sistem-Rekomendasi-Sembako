"""Konfigurasi URL utama proyek SmartBako."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin bawaan Django (untuk superuser/pengembang).
    path("admin/", admin.site.urls),

    # Semua URL SmartBako memakai namespace, dipanggil di template
    # sebagai {% url 'smartbako:nama_url' %}.
    path("", include("smartbako.urls")),
]

# Menyajikan file media (gambar produk) hanya saat pengembangan.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )