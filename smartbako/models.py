
from django.db import models


class Kategori(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    deskripsi = models.TextField(blank=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class Produk(models.Model):
    nama = models.CharField(max_length=150)
    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.PROTECT,
        related_name="produk"
    )
    merek = models.CharField(max_length=100, blank=True)
    harga = models.DecimalField(max_digits=12, decimal_places=2)
    ukuran = models.DecimalField(max_digits=10, decimal_places=2)
    satuan = models.CharField(max_length=30)
    deskripsi = models.TextField(blank=True)
    tanggal_dibuat = models.DateTimeField(auto_now_add=True)
    tanggal_diperbarui = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produk"
        verbose_name_plural = "Produk"
        ordering = ["nama"]

    def __str__(self):
        return self.nama
