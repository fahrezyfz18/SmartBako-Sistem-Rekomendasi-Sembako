from django.urls import path
from . import views

urlpatterns = [
    # Dashboard pengguna
    path('', views.beranda, name='beranda'),

    # Dashboard admin
    path('admin-dashboard/', views.dashboard_admin, name='dashboard_admin'),

    # Kelola kategori
    path('admin/kategori/', views.daftar_kategori, name='daftar_kategori'),
    path('admin/kategori/tambah/', views.tambah_kategori, name='tambah_kategori'),
    path('admin/kategori/<int:id>/edit/', views.edit_kategori, name='edit_kategori'),
    path('admin/kategori/<int:id>/hapus/', views.hapus_kategori, name='hapus_kategori'),

    # Kelola produk
    path('admin/produk/', views.daftar_produk, name='daftar_produk'),
    path('admin/produk/tambah/', views.tambah_produk, name='tambah_produk'),
    path('admin/produk/<int:id>/edit/', views.edit_produk, name='edit_produk'),
    path('admin/produk/<int:id>/hapus/', views.hapus_produk, name='hapus_produk'),

    # Kelola pengguna
    path('admin/pengguna/', views.daftar_pengguna, name='daftar_pengguna'),
    path('admin/pengguna/<int:id>/status/', views.ubah_status_pengguna, name='ubah_status_pengguna'),
    path('admin/pengguna/<int:id>/hapus/', views.hapus_pengguna, name='hapus_pengguna'),

    path('admin/logout/', views.logout_admin, name='logout_admin'),
]