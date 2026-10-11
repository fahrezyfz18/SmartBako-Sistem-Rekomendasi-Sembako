
from django.urls import path
from . import views

app_name = "smartbako"

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("katalog/", views.katalog, name="katalog"),
    path(
        "produk/<int:produk_id>/",
        views.detail_produk,
        name="detail_produk",
    ),
]
