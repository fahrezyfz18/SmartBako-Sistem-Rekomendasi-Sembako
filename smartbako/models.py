
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


# Batas stok produk yang dianggap terbatas
BATAS_STOK_TERBATAS = 10


# Tabel kategori produk
class Kategori(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    deskripsi = models.TextField(blank=True)

    class Meta:
        ordering = ["nama"]

    def __str__(self):
        return self.nama


# Tabel produk sembako
class Produk(models.Model):
    nama = models.CharField(max_length=200)

    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.PROTECT,
        related_name="produk"
    )

    merek = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    harga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))]
    )

    ukuran = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))]
    )

    satuan = models.CharField(
        max_length=30,
        blank=True,
        default=""
    )

    stok = models.PositiveIntegerField(default=0)
    deskripsi = models.TextField(blank=True)

    gambar = models.ImageField(
        upload_to="produk/",
        blank=True,
        null=True
    )

    tanggal_dibuat = models.DateTimeField(auto_now_add=True)
    tanggal_diperbarui = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nama"]

    def __str__(self):
        return self.nama

    @property
    def tersedia(self):
        return self.stok > 0

    @property
    def status_stok(self):
        if self.stok <= 0:
            return "habis"
        elif self.stok <= BATAS_STOK_TERBATAS:
            return "terbatas"
        else:
            return "tersedia"

    @property
    def harga_per_satuan(self):
        if not self.ukuran:
            return None

        return self.harga / self.ukuran


# Tabel preferensi pengguna
class Preferensi(models.Model):
    pengguna = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferensi"
    )

    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferensi"
    )

    budget_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))]
    )

    budget_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )

    ukuran = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))]
    )

    satuan = models.CharField(max_length=30, blank=True)
    merek = models.CharField(max_length=100, blank=True)
    kebutuhan_tambahan = models.TextField(blank=True)

    tanggal_input = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-tanggal_input"]

    def __str__(self):
        return f"Preferensi #{self.pk} - {self.pengguna}"


# Tabel riwayat rekomendasi
class Rekomendasi(models.Model):
    preferensi = models.ForeignKey(
        Preferensi,
        on_delete=models.CASCADE,
        related_name="rekomendasi"
    )

    tanggal_rekomendasi = models.DateTimeField(auto_now_add=True)
    jumlah_hasil = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-tanggal_rekomendasi"]

    def __str__(self):
        return f"Rekomendasi #{self.pk}"


# Tabel detail hasil rekomendasi
class DetailRekomendasi(models.Model):
    rekomendasi = models.ForeignKey(
        Rekomendasi,
        on_delete=models.CASCADE,
        related_name="detail"
    )

    produk = models.ForeignKey(
        Produk,
        on_delete=models.PROTECT,
        related_name="detail_rekomendasi"
    )

    skor_kecocokan = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=0
    )

    peringkat = models.PositiveIntegerField()
    alasan_rekomendasi = models.TextField(blank=True)

    class Meta:
        ordering = ["peringkat"]

        constraints = [
            models.UniqueConstraint(
                fields=["rekomendasi", "produk"],
                name="unik_produk_dalam_rekomendasi"
            )
        ]

    def __str__(self):
        return f"{self.produk.nama} - peringkat {self.peringkat}"
