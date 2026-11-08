
from django.contrib import admin
from .models import Kategori, Produk


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('id', 'nama', 'deskripsi')
    search_fields = ('nama',)


@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nama',
        'kategori',
        'harga',
        'stok',
        'tanggal_dibuat',
    )
    list_filter = ('kategori',)
    search_fields = ('nama', 'deskripsi')
    list_editable = ('harga', 'stok')
