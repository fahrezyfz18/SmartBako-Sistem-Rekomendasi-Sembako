
"""Pengaturan URL utama proyek SmartBako."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    # Halaman admin bawaan Django.
    path("admin/", admin.site.urls),

    # Menghubungkan semua URL dari aplikasi SmartBako.
    path("", include("smartbako.urls")),
]


# Menampilkan gambar dan file media saat pengembangan.
# Bagian ini hanya berjalan jika DEBUG bernilai True.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
