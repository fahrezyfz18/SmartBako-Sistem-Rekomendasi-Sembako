"""
Layanan rekomendasi produk SmartBako.

Metode: Content-Based Filtering
1. Filter produk berdasarkan stok dan anggaran.
2. Preprocessing teks produk dan preferensi.
3. Pembobotan TF-IDF.
4. Perhitungan Cosine Similarity.
"""

from decimal import Decimal

from django.db import transaction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..models import DetailRekomendasi, Produk, Rekomendasi
from .preprocessing import preprocessing_teks

# Jumlah maksimal produk yang ditampilkan dalam satu rekomendasi.
BATAS_REKOMENDASI = 10

# Angka desimal (2.5) dan angka+satuan (2.5kg) dipertahankan utuh.
POLA_TOKEN = r"(?u)\b\d+(?:\.\d+)?[^\W\d_]*\b|\b\w+\b"


# ==========================================================
# PEMBENTUKAN DOKUMEN TEKS
# ==========================================================

def format_angka(nilai):
    """Mengubah Decimal('5.00') menjadi '5' agar token lebih bersih."""
    if nilai is None:
        return ""
    return f"{Decimal(nilai).normalize():f}"


def gabung_ukuran_satuan(ukuran, satuan):
    """Menghasilkan '5 kg 5kg' agar penulisan '5kg' dan '5 kg' sama-sama cocok."""
    angka = format_angka(ukuran)
    satuan = (satuan or "").strip()

    if angka and satuan:
        return f"{angka} {satuan} {angka}{satuan}"
    return f"{angka} {satuan}".strip()


def buat_dokumen_produk(produk):
    """Menggabungkan atribut produk menjadi satu dokumen teks."""
    return " ".join([
        produk.nama or "",
        produk.merek or "",
        produk.kategori.nama if produk.kategori_id else "",
        produk.deskripsi or "",
        gabung_ukuran_satuan(produk.ukuran, produk.satuan),
    ])


def buat_dokumen_preferensi(preferensi):
    """Menggabungkan preferensi pengguna menjadi satu query teks."""
    return " ".join([
        preferensi.kategori.nama if preferensi.kategori_id else "",
        preferensi.merek or "",
        gabung_ukuran_satuan(preferensi.ukuran, preferensi.satuan),
        preferensi.kebutuhan_tambahan or "",
    ])


# ==========================================================
# PERHITUNGAN REKOMENDASI
# ==========================================================

def ambil_kandidat_produk(preferensi):
    """Produk yang stoknya ada dan harganya masuk rentang anggaran."""
    produk = Produk.objects.filter(
        stok__gt=0,
        harga__lte=preferensi.budget_max,
    ).select_related("kategori")

    if preferensi.budget_min is not None:
        produk = produk.filter(harga__gte=preferensi.budget_min)

    return produk


def hitung_rekomendasi(preferensi, daftar_produk, batas=BATAS_REKOMENDASI):
    """
    Mengembalikan list tuple (produk, skor) terurut dari skor tertinggi.

    Jika pengguna hanya mengisi anggaran (tidak ada teks preferensi),
    produk tetap dikembalikan dengan skor 0 dan diurutkan dari harga
    termurah, sehingga hasil rekomendasi tidak kosong.
    """
    kandidat = [
        produk for produk in daftar_produk
        if produk.stok > 0
        and produk.harga <= preferensi.budget_max
        and (
            preferensi.budget_min is None
            or produk.harga >= preferensi.budget_min
        )
    ]

    if not kandidat:
        return []

    dokumen_preferensi = preprocessing_teks(buat_dokumen_preferensi(preferensi))
    dokumen_produk = [
        preprocessing_teks(buat_dokumen_produk(produk))
        for produk in kandidat
    ]

    if not dokumen_preferensi:
        hasil = [(produk, 0.0) for produk in kandidat]
        hasil.sort(key=lambda item: item[0].harga)
        return hasil[:batas]

    try:
        vectorizer = TfidfVectorizer(token_pattern=POLA_TOKEN)
        matriks = vectorizer.fit_transform(dokumen_produk + [dokumen_preferensi])
        skor = cosine_similarity(matriks[-1], matriks[:-1]).flatten().tolist()
    except ValueError:
        # Terjadi bila seluruh dokumen kosong setelah preprocessing.
        skor = [0.0] * len(kandidat)

    hasil = list(zip(kandidat, skor))
    # Skor tertinggi lebih dulu; jika sama, harga termurah lebih dulu.
    hasil.sort(key=lambda item: (-item[1], item[0].harga))
    return hasil[:batas]


def buat_alasan_rekomendasi(produk, preferensi):
    """Menyusun penjelasan singkat mengapa produk direkomendasikan."""
    alasan = []

    if preferensi.kategori_id and produk.kategori_id == preferensi.kategori_id:
        alasan.append("Kategori sesuai dengan preferensi.")

    if (
        preferensi.merek
        and produk.merek
        and preferensi.merek.lower() in produk.merek.lower()
    ):
        alasan.append("Merek sesuai dengan preferensi.")

    if preferensi.ukuran is not None and produk.ukuran == preferensi.ukuran:
        alasan.append("Ukuran produk sesuai.")

    if (
        preferensi.satuan
        and produk.satuan
        and preferensi.satuan.lower() == produk.satuan.lower()
    ):
        alasan.append("Satuan produk sesuai.")

    if produk.harga <= preferensi.budget_max:
        alasan.append("Harga sesuai dengan batas anggaran.")

    if not alasan:
        alasan.append(
            "Produk memiliki kemiripan atribut dengan kebutuhan pengguna."
        )

    return " ".join(alasan)


@transaction.atomic
def simpan_rekomendasi(preferensi, batas=BATAS_REKOMENDASI):
    """
    Menghitung rekomendasi lalu menyimpannya ke tabel Rekomendasi dan
    DetailRekomendasi dalam satu transaksi.

    `batas` = jumlah produk yang diminta pengguna (5 atau 10).
    """
    hasil = hitung_rekomendasi(
        preferensi,
        ambil_kandidat_produk(preferensi),
        batas=batas,
    )

    rekomendasi = Rekomendasi.objects.create(
        preferensi=preferensi,
        jumlah_hasil=len(hasil),
    )

    DetailRekomendasi.objects.bulk_create([
        DetailRekomendasi(
            rekomendasi=rekomendasi,
            produk=produk,
            skor_kecocokan=Decimal(str(round(float(skor), 8))),
            peringkat=peringkat,
            alasan_rekomendasi=buat_alasan_rekomendasi(produk, preferensi),
        )
        for peringkat, (produk, skor) in enumerate(hasil, start=1)
    ])

    return rekomendasi