"""URL aplikasi SmartBako. Semua nama URL memakai namespace `smartbako:`."""

from django.urls import path

from . import views
from .urls_admin import urlpatterns as admin_urls
from .urls_pengguna import urlpatterns as pengguna_urls

app_name = "smartbako"

urlpatterns = [
    # Halaman publik
    path("", views.landing_page, name="landing_page"),
    path("fitur/", views.fitur_publik, name="fitur"),
    path("produk-publik/", views.katalog_publik, name="produk_publik"),
    path("tentang-kami/", views.tentang_kami, name="tentang_kami"),

    # Autentikasi
    path("masuk/", views.login_pengguna, name="login"),
    path("daftar/", views.registrasi_pengguna, name="registrasi"),
    path("keluar/", views.logout_pengguna, name="logout"),
]

urlpatterns += pengguna_urls
urlpatterns += admin_urls