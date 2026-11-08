
"""
Layanan rekomendasi produk SmartBako.

Metode yang digunakan adalah Content-Based Filtering.

Tahapan:
1. Memilih produk berdasarkan stok dan anggaran.
2. Membersihkan teks produk dan preferensi.
3. Menghitung bobot kata menggunakan TF-IDF.
4. Menghitung kemiripan menggunakan Cosine Similarity.
5. Mengurutkan dan menyimpan hasil rekomendasi.
"""

from decimal import Decimal

from django.db import transaction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..models import DetailRekomendasi, Produk, Rekomendasi
from .preprocessing import preprocessing_teks


# Jumlah maksimal produk yang dapat direkomendasikan.
BATAS_REKOMENDASI = 10

# Pola untuk mempertahankan angka desimal dan angka yang memiliki satuan.
# Contoh: 2.5 dan 2.5kg tidak dipisahkan.
POLA_TOKEN = r"(?u)\b\d+(?:\.\d+)?[^\W\d_]*\b|\b\w+\b"


# ==================================================
# PEMBENTUKAN DOKUMEN TEKS
# ==================================================

def format_angka(nilai):
    """
    Mengubah angka Decimal menjadi bentuk yang lebih sederhana.

    Contoh:
    Decimal('5.00') menjadi '5'.
    """

    if nilai is None:
        return ""

    return f"{Decimal(nilai).normalize():f}"


def gabung_ukuran_satuan(ukuran, satuan):
    """
    Menggabungkan ukuran dan satuan produk.

    Contoh:
    Ukuran 5 dan satuan kg menjadi '5 kg 5kg'.

    Tujuannya agar penulisan '5 kg' dan '5kg'
    tetap dapat dikenali sebagai ukuran yang sama.
    """

    angka = format_angka(ukuran)
    satuan = (satuan or "").strip()

    if angka and satuan:
        return f"{angka} {satuan} {angka}{satuan}"

    return f"{angka} {satuan}".strip()


def buat_dokumen_produk(produk):
    """
    Menggabungkan informasi produk menjadi satu teks.

    Informasi yang digunakan meliputi:
    nama, merek, kategori, deskripsi, ukuran, dan satuan.
    """

    return " ".join([
        produk.nama or "",
        produk.merek or "",
        produk.kategori.nama if produk.kategori_id else "",
        produk.deskripsi or "",
        gabung_ukuran_satuan(produk.ukuran, produk.satuan),
    ])


def buat_dokumen_preferensi(preferensi):
    """
    Menggabungkan pilihan pengguna menjadi satu teks pencarian.

    Data yang digunakan berasal dari preferensi pengguna.
    """

    return " ".join([
        preferensi.kategori.nama if preferensi.kategori_id else "",
        preferensi.merek or "",
        gabung_ukuran_satuan(preferensi.ukuran, preferensi.satuan),
        preferensi.kebutuhan_tambahan or "",
    ])


# ==================================================
# PERHITUNGAN REKOMENDASI
# ==================================================

def ambil_kandidat_produk(preferensi):
    """
    Mengambil produk yang memenuhi syarat awal.

    Produk harus memiliki stok dan harganya
    berada dalam rentang anggaran pengguna.
    """

    produk = Produk.objects.filter(
        stok__gt=0,
        harga__lte=preferensi.budget_max,
    ).select_related("kategori")

    # Jika pengguna mengisi anggaran minimum,
    # produk yang lebih murah dari batas tersebut tidak diambil.
    if preferensi.budget_min is not None:
        produk = produk.filter(
            harga__gte=preferensi.budget_min
        )

    return produk


def hitung_rekomendasi(preferensi, daftar_produk, batas=BATAS_REKOMENDASI):
    """
    Menghitung tingkat kemiripan produk dengan preferensi pengguna.

    Hasil berupa pasangan produk dan skor kecocokan.
    Skor yang lebih tinggi menunjukkan kemiripan yang lebih besar.

    Jika pengguna hanya mengisi anggaran tanpa preferensi teks,
    produk tetap ditampilkan berdasarkan harga termurah.
    """

    # Memilih produk yang memenuhi stok dan anggaran.
    kandidat = [
        produk for produk in daftar_produk
        if produk.stok > 0
        and produk.harga <= preferensi.budget_max
        and (
            preferensi.budget_min is None
            or produk.harga >= preferensi.budget_min
        )
    ]

    # Jika tidak ada produk yang memenuhi syarat, hasilnya kosong.
    if not kandidat:
        return []

    # Membersihkan teks preferensi pengguna.
    dokumen_preferensi = preprocessing_teks(
        buat_dokumen_preferensi(preferensi)
    )

    # Membersihkan teks dari setiap produk.
    dokumen_produk = [
        preprocessing_teks(buat_dokumen_produk(produk))
        for produk in kandidat
    ]

    # Jika pengguna tidak mengisi preferensi teks,
    # produk diurutkan berdasarkan harga termurah.
    if not dokumen_preferensi:
        hasil = [(produk, 0.0) for produk in kandidat]
        hasil.sort(key=lambda item: item[0].harga)

        return hasil[:batas]

    try:
        # Mengubah teks menjadi angka menggunakan TF-IDF.
        vectorizer = TfidfVectorizer(
            token_pattern=POLA_TOKEN
        )

        matriks = vectorizer.fit_transform(
            dokumen_produk + [dokumen_preferensi]
        )

        # Menghitung kemiripan teks menggunakan Cosine Similarity.
        skor = cosine_similarity(
            matriks[-1],
            matriks[:-1]
        ).flatten().tolist()

    except ValueError:
        # Jika semua dokumen kosong, skor setiap produk menjadi 0.
        skor = [0.0] * len(kandidat)

    # Menggabungkan produk dengan skor kecocokannya.
    hasil = list(zip(kandidat, skor))

    # Mengurutkan dari skor tertinggi.
    # Jika skornya sama, produk termurah ditampilkan lebih dahulu.
    hasil.sort(
        key=lambda item: (-item[1], item[0].harga)
    )

    # Mengambil produk sesuai jumlah yang diminta.
    return hasil[:batas]


# ==================================================
# ALASAN REKOMENDASI
# ==================================================

def buat_alasan_rekomendasi(produk, preferensi):
    """
    Membuat penjelasan mengapa suatu produk direkomendasikan.

    Penjelasan dibuat berdasarkan kesesuaian atribut produk
    dengan preferensi yang diisi oleh pengguna.
    """

    alasan = []

    # Memeriksa kesesuaian kategori.
    if (
        preferensi.kategori_id
        and produk.kategori_id == preferensi.kategori_id
    ):
        alasan.append(
            "Kategori sesuai dengan preferensi."
        )

    # Memeriksa kesesuaian merek.
    if (
        preferensi.merek
        and produk.merek
        and preferensi.merek.lower() in produk.merek.lower()
    ):
        alasan.append(
            "Merek sesuai dengan preferensi."
        )

    # Memeriksa kesesuaian ukuran.
    if (
        preferensi.ukuran is not None
        and produk.ukuran == preferensi.ukuran
    ):
        alasan.append(
            "Ukuran produk sesuai."
        )

    # Memeriksa kesesuaian satuan.
    if (
        preferensi.satuan
        and produk.satuan
        and preferensi.satuan.lower() == produk.satuan.lower()
    ):
        alasan.append(
            "Satuan produk sesuai."
        )

    # Memeriksa kesesuaian harga dengan anggaran.
    if produk.harga <= preferensi.budget_max:
        alasan.append(
            "Harga sesuai dengan batas anggaran."
        )

    # Jika tidak ada alasan khusus, gunakan penjelasan umum.
    if not alasan:
        alasan.append(
            "Produk memiliki kemiripan atribut dengan kebutuhan pengguna."
        )

    return " ".join(alasan)


# ==================================================
# MENYIMPAN HASIL REKOMENDASI
# ==================================================

@transaction.atomic
def simpan_rekomendasi(preferensi, batas=BATAS_REKOMENDASI):
    """
    Menghitung dan menyimpan hasil rekomendasi ke database.

    Data disimpan ke dua tabel:
    1. Rekomendasi.
    2. DetailRekomendasi.

    Jika terjadi kesalahan saat penyimpanan,
    transaksi database dapat dibatalkan.
    """

    # Mengambil dan menghitung produk yang sesuai.
    hasil = hitung_rekomendasi(
        preferensi,
        ambil_kandidat_produk(preferensi),
        batas=batas,
    )

    # Membuat data utama rekomendasi.
    rekomendasi = Rekomendasi.objects.create(
        preferensi=preferensi,
        jumlah_hasil=len(hasil),
    )

    # Menyimpan detail produk, skor, peringkat, dan alasan.
    DetailRekomendasi.objects.bulk_create([
        DetailRekomendasi(
            rekomendasi=rekomendasi,
            produk=produk,
            skor_kecocokan=Decimal(
                str(round(float(skor), 8))
            ),
            peringkat=peringkat,
            alasan_rekomendasi=buat_alasan_rekomendasi(
                produk,
                preferensi
            ),
        )
        for peringkat, (produk, skor) in enumerate(
            hasil,
            start=1
        )
    ])

    return rekomendasi
