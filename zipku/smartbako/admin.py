"""Registrasi model ke admin bawaan Django (/admin/)."""

from django.contrib import admin

from .models import DetailRekomendasi, Kategori, Preferensi, Produk, Rekomendasi


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ("id", "nama", "deskripsi")
    search_fields = ("nama",)


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
        "stok",
        "tanggal_dibuat",
    )
    list_filter = ("kategori",)
    search_fields = ("nama", "merek", "deskripsi")
    list_editable = ("harga", "stok")
    list_select_related = ("kategori",)


@admin.register(Preferensi)
class PreferensiAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pengguna",
        "kategori",
        "budget_min",
        "budget_max",
        "merek",
        "tanggal_input",
    )
    list_filter = ("kategori",)
    search_fields = ("pengguna__username", "merek", "kebutuhan_tambahan")
    list_select_related = ("pengguna", "kategori")


class DetailRekomendasiInline(admin.TabularInline):
    model = DetailRekomendasi
    extra = 0
    readonly_fields = ("produk", "skor_kecocokan", "peringkat", "alasan_rekomendasi")
    can_delete = False


@admin.register(Rekomendasi)
class RekomendasiAdmin(admin.ModelAdmin):
    list_display = ("id", "preferensi", "jumlah_hasil", "tanggal_rekomendasi")
    list_select_related = ("preferensi", "preferensi__pengguna")
    inlines = [DetailRekomendasiInline]