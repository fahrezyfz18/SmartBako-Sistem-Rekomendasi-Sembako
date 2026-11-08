
"""URL untuk halaman panel pengguna SmartBako."""

from django.urls import path

from . import views_pengguna as views


urlpatterns = [
    # Halaman utama pengguna.
    path("dashboard/", views.beranda, name="beranda"),

    # Daftar dan detail produk.
    path("katalog/", views.katalog, name="katalog"),
    path(
        "produk/<int:pk>/",
        views.detail_produk,
        name="detail_produk",
    ),

    # Preferensi dan hasil rekomendasi.
    path(
        "preferensi/",
        views.atur_preferensi,
        name="atur_preferensi",
    ),
    path(
        "rekomendasi/<int:pk>/",
        views.rekomendasi,
        name="rekomendasi",
    ),

    # Riwayat dan perbandingan produk.
    path("riwayat/", views.riwayat_rekomendasi, name="riwayat"),
    path(
        "bandingkan/",
        views.bandingkan_produk,
        name="bandingkan_produk",
    ),

    # Profil dan perubahan kata sandi.
    path("profil/", views.profil_pengguna, name="profil"),
    path(
        "profil/ubah-password/",
        views.ubah_password,
        name="ubah_password",
    ),
]
