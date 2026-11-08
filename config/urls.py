"""Konfigurasi URL utama proyek SmartBako."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin bawaan Django (untuk superuser/pengembang).
    path("admin/", admin.site.urls),

    # Semua URL SmartBako dengan namespace, dipanggil sebagai
    # {% url 'smartbako:nama_url' %}.
    path("", include("smartbako.urls")),

    # Template panel admin versi lama memanggil URL tanpa namespace,
    # misalnya {% url 'dashboard_admin' %}. Baris ini mendaftarkan URL
    # admin yang sama tanpa namespace agar template tersebut tidak perlu
    # diubah. Alamat dan view-nya tetap sama, jadi tidak ada duplikasi fitur.
    path("", include("smartbako.urls_admin")),
]

# Menyajikan file media (gambar produk) hanya saat pengembangan.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )