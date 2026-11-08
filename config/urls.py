<<<<<<< HEAD
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
=======
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('smartbako.urls')),
    path('admin/', admin.site.urls),
]

# Menampilkan file gambar yang diunggah selama development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d
