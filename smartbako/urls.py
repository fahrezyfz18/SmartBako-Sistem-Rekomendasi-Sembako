
"""URL utama aplikasi SmartBako."""

from django.urls import path

from . import views

# Mengambil daftar URL dari file lain.
from .urls_admin import urlpatterns as admin_urls
from .urls_pengguna import urlpatterns as pengguna_urls


# Namespace untuk semua URL aplikasi SmartBako.
app_name = "smartbako"


urlpatterns = [
    # ==============================
    # HALAMAN PUBLIK
    # ==============================

    path("", views.landing_page, name="landing_page"),
    path("fitur/", views.fitur_publik, name="fitur"),
    path("produk-publik/", views.katalog_publik, name="produk_publik"),
    path("tentang-kami/", views.tentang_kami, name="tentang_kami"),

    # ==============================
    # LOGIN DAN REGISTRASI
    # ==============================

    path("masuk/", views.login_pengguna, name="login"),
    path("daftar/", views.registrasi_pengguna, name="registrasi"),
    path("keluar/", views.logout_pengguna, name="logout"),
]

# Menggabungkan URL pengguna dan admin ke URL utama.
urlpatterns += pengguna_urls
urlpatterns += admin_urls
