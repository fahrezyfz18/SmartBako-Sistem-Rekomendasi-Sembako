
from django.urls import path
from . import views

app_name = "smartbako"

urlpatterns = [
    # Halaman pengguna
    path("", views.beranda, name="beranda"),
    path("katalog/", views.katalog, name="katalog"),
    path(
        "produk/<int:produk_id>/",
        views.detail_produk,
        name="detail_produk",
    ),

    # Kelola kategori admin
    path(
        "admin/kategori/",
        views.daftar_kategori,
        name="daftar_kategori",
    ),
    path(
        "admin/kategori/tambah/",
        views.tambah_kategori,
        name="tambah_kategori",
    ),
    path(
        "admin/kategori/<int:kategori_id>/edit/",
        views.edit_kategori,
        name="edit_kategori",
    ),
    path(
        "admin/kategori/<int:kategori_id>/hapus/",
        views.hapus_kategori,
        name="hapus_kategori",
    ),
]
