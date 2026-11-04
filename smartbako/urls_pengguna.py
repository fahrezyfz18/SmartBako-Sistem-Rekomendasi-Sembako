
from django.urls import path
from . import views_pengguna as views

urlpatterns = [
    path("dashboard/", views.beranda, name="beranda"),
    path("katalog/", views.katalog, name="katalog"),
    path("produk/<int:id>/", views.detail_produk, name="detail_produk"),
    path("preferensi/", views.atur_preferensi, name="atur_preferensi"),
    path("rekomendasi/<int:id>/", views.rekomendasi, name="rekomendasi"),
    path("riwayat/", views.riwayat_rekomendasi, name="riwayat"),
    path("bandingkan/", views.bandingkan_produk, name="bandingkan_produk"),
    path("profil/", views.profil_pengguna, name="profil"),
    path(
        "profil/ubah-password/",
        views.ubah_password,
        name="ubah_password",
    ),
]
