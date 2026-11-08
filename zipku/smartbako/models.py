"""Model data aplikasi SmartBako."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

# Stok di bawah atau sama dengan angka ini ditampilkan "Terbatas".
BATAS_STOK_TERBATAS = 10


class Kategori(models.Model):
    """Kategori produk sembako, misalnya Beras, Minyak, Gula."""

    nama = models.CharField("nama kategori", max_length=100, unique=True)
    deskripsi = models.TextField("deskripsi", blank=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class Produk(models.Model):
    """Produk sembako yang dapat direkomendasikan ke pengguna."""

    nama = models.CharField("nama produk", max_length=200)
    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.PROTECT,
        related_name="produk",
        verbose_name="kategori",
    )
    merek = models.CharField("merek", max_length=100, blank=True, default="")
    harga = models.DecimalField(
        "harga",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    ukuran = models.DecimalField(
        "ukuran",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    satuan = models.CharField("satuan", max_length=30, blank=True, default="")
    stok = models.PositiveIntegerField("stok", default=0)
    deskripsi = models.TextField("deskripsi", blank=True)
    gambar = models.ImageField(
        "gambar",
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

    @property
    def tersedia(self):
        """True jika stok produk masih ada."""
        return self.stok > 0

    @property
    def status_stok(self):
        """'habis', 'terbatas', atau 'tersedia' (untuk label di tampilan)."""
        if self.stok <= 0:
            return "habis"
        if self.stok <= BATAS_STOK_TERBATAS:
            return "terbatas"
        return "tersedia"

    @property
    def harga_per_satuan(self):
        """Harga dibagi ukuran, mis. Rp 82.000 / 5 kg = Rp 16.400 per kg."""
        if not self.ukuran:
            return None
        return self.harga / self.ukuran


class Preferensi(models.Model):
    """Kebutuhan yang diisi pengguna sebagai dasar rekomendasi."""

    pengguna = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferensi",
        verbose_name="pengguna",
    )
    kategori = models.ForeignKey(
        Kategori,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="preferensi",
        verbose_name="kategori",
    )
    budget_min = models.DecimalField(
        "anggaran minimum",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    budget_max = models.DecimalField(
        "anggaran maksimum",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    ukuran = models.DecimalField(
        "ukuran",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    satuan = models.CharField("satuan", max_length=30, blank=True)
    merek = models.CharField("merek", max_length=100, blank=True)
    kebutuhan_tambahan = models.TextField("kebutuhan tambahan", blank=True)
    tanggal_input = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Preferensi"
        verbose_name_plural = "Preferensi"
        ordering = ["-tanggal_input"]

    def __str__(self):
        return f"Preferensi #{self.pk} - {self.pengguna}"


class Rekomendasi(models.Model):
    """Satu kali proses rekomendasi untuk sebuah preferensi."""

    preferensi = models.ForeignKey(
        Preferensi,
        on_delete=models.CASCADE,
        related_name="rekomendasi",
        verbose_name="preferensi",
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
    """Produk hasil rekomendasi beserta skor dan peringkatnya."""

    rekomendasi = models.ForeignKey(
        Rekomendasi,
        on_delete=models.CASCADE,
        related_name="detail",
        verbose_name="rekomendasi",
    )
    produk = models.ForeignKey(
        Produk,
        on_delete=models.PROTECT,
        related_name="detail_rekomendasi",
        verbose_name="produk",
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
        return f"{self.produk.nama} - peringkat {self.peringkat}"