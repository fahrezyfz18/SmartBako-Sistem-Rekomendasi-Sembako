
from django.contrib import admin
from .models import Kategori, Produk


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ("id", "nama", "deskripsi")
    search_fields = ("nama",)
    ordering = ("nama",)


@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nama",
        "kategori",
        "merek",
        "harga",
        "ukuran",
        "satuan",
    )
    list_filter = ("kategori", "merek")
    search_fields = ("nama", "merek", "deskripsi")
    list_select_related = ("kategori",)
    ordering = ("nama",)
