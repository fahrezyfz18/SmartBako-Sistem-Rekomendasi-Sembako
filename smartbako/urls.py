from django.urls import path
from . import views

app_name = "smartbako"

urlpatterns = [    
    # 1. Rute Publik & Autentikasi
    path("", views.landing_page, name="landing_page"),
    path("fitur/", views.fitur_view, name="fitur"),
    path("produk-publik/", views.produk_publik_view, name="produk"),
    path("tentang-kami/", views.tentang_kami_view, name="tentang_kami"),
    path("masuk/", views.login_view, name="login"),
    path("daftar/", views.registrasi_view, name="registrasi"),
    path("keluar/", views.logout_view, name="logout"),
    path("lupa-password/", views.lupa_password_view, name="lupa_password"),
    
    # 2. Rute Panel Pengguna
    path("dashboard/", views.beranda, name="beranda"),
    path("katalog/", views.katalog, name="katalog"),
    path("produk/<int:produk_id>/", views.detail_produk, name="detail_produk"),
    path("rekomendasi/", views.rekomendasi, name="rekomendasi"), 
    
    # 3. Rute Panel Admin 
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/produk/", views.admin_kelola_produk, name="admin_kelola_produk"),
]