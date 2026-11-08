
"""URL untuk halaman panel admin SmartBako."""

from django.urls import path

from . import views_admin as views


urlpatterns = [
    # ==============================
    # DASHBOARD ADMIN
    # ==============================

    path(
        "admin-dashboard/",
        views.dashboard_admin,
        name="dashboard_admin",
    ),

    # ==============================
    # KELOLA KATEGORI
    # ==============================

    path(
        "panel-admin/kategori/",
        views.daftar_kategori,
        name="daftar_kategori",
    ),
    path(
        "panel-admin/kategori/tambah/",
        views.tambah_kategori,
        name="tambah_kategori",
    ),
    path(
        "panel-admin/kategori/edit/<int:id>/",
        views.edit_kategori,
        name="edit_kategori",
    ),
    path(
        "panel-admin/kategori/hapus/<int:id>/",
        views.hapus_kategori,
        name="hapus_kategori",
    ),

    # ==============================
    # KELOLA PRODUK
    # ==============================

    path(
        "panel-admin/produk/",
        views.daftar_produk,
        name="daftar_produk",
    ),
    path(
        "panel-admin/produk/tambah/",
        views.tambah_produk,
        name="tambah_produk",
    ),
    path(
        "panel-admin/produk/<int:id>/",
        views.detail_produk_admin,
        name="detail_produk_admin",
    ),
    path(
        "panel-admin/produk/edit/<int:id>/",
        views.edit_produk,
        name="edit_produk",
    ),
    path(
        "panel-admin/produk/hapus/<int:id>/",
        views.hapus_produk,
        name="hapus_produk",
    ),

    # ==============================
    # KELOLA PENGGUNA
    # ==============================

    path(
        "panel-admin/pengguna/",
        views.daftar_pengguna,
        name="daftar_pengguna",
    ),
    path(
        "panel-admin/pengguna/<int:id>/",
        views.detail_pengguna,
        name="detail_pengguna",
    ),
    path(
        "panel-admin/pengguna/status/<int:id>/",
        views.ubah_status_pengguna,
        name="ubah_status_pengguna",
    ),
    path(
        "panel-admin/pengguna/hapus/<int:id>/",
        views.hapus_pengguna,
        name="hapus_pengguna",
    ),

    # ==============================
    # RIWAYAT PREFERENSI
    # ==============================

    path(
        "panel-admin/riwayat-preferensi/",
        views.riwayat_preferensi,
        name="riwayat_preferensi",
    ),
    path(
        "panel-admin/riwayat-preferensi/<int:id>/",
        views.detail_preferensi,
        name="detail_preferensi",
    ),

    # ==============================
    # LOGOUT ADMIN
    # ==============================

    path(
        "panel-admin/keluar/",
        views.logout_admin,
        name="logout_admin",
    ),
]
