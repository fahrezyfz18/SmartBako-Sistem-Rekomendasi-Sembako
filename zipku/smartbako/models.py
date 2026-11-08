from django.conf import settings
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
    nama = models.CharField(max_length=200)

    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.PROTECT,
        related_name="produk",
    )

    merek = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    harga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    ukuran = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    satuan = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    stok = models.PositiveIntegerField(default=0)
    deskripsi = models.TextField(blank=True)

    gambar = models.ImageField(
        upload_to="produk/",
        blank=True,
        null=True,
    )

    tanggal_dibuat = models.DateTimeField(auto_now_add=True)
    tanggal_diperbarui = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produk"
        verbose_name_plural = "Produk"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class Preferensi(models.Model):
    pengguna = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferensi",
    )

    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferensi",
    )

    budget_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    budget_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    ukuran = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    satuan = models.CharField(
        max_length=30,
        blank=True,
    )

    merek = models.CharField(
        max_length=100,
        blank=True,
    )

    kebutuhan_tambahan = models.TextField(blank=True)
    tanggal_input = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Preferensi"
        verbose_name_plural = "Preferensi"
        ordering = ["-tanggal_input"]

    def __str__(self):
        return f"Preferensi {self.pengguna.username}"


class Rekomendasi(models.Model):
    preferensi = models.ForeignKey(
        Preferensi,
        on_delete=models.CASCADE,
        related_name="rekomendasi",
    )

    tanggal_rekomendasi = models.DateTimeField(auto_now_add=True)
    jumlah_hasil = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Rekomendasi"
        verbose_name_plural = "Rekomendasi"
        ordering = ["-tanggal_rekomendasi"]

    def __str__(self):
        return f"Rekomendasi #{self.pk}"


class DetailRekomendasi(models.Model):
    rekomendasi = models.ForeignKey(
        Rekomendasi,
        on_delete=models.CASCADE,
        related_name="detail",
    )

    produk = models.ForeignKey(
        Produk,
        on_delete=models.PROTECT,
        related_name="detail_rekomendasi",
    )

    skor_kecocokan = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=0,
    )

    peringkat = models.PositiveIntegerField()
    alasan_rekomendasi = models.TextField(blank=True)

    class Meta:
        verbose_name = "Detail Rekomendasi"
        verbose_name_plural = "Detail Rekomendasi"
        ordering = ["peringkat"]
        constraints = [
            models.UniqueConstraint(
                fields=["rekomendasi", "produk"],
                name="unik_produk_dalam_rekomendasi",
            )
        ]

    def __str__(self):
        return (
            f"{self.produk.nama} - "
            f"peringkat {self.peringkat}"
        )