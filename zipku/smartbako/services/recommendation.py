
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import preprocessing_teks


def buat_dokumen_produk(produk):
    """
    Menggabungkan atribut produk menjadi satu dokumen teks.
    """

    return " ".join([
        produk.nama or "",
        produk.merek or "",
        produk.kategori.nama if produk.kategori else "",
        produk.deskripsi or "",
        str(produk.ukuran or ""),
        produk.satuan or "",
    ])


def buat_dokumen_preferensi(preferensi):
    """
    Menggabungkan preferensi pengguna menjadi query.
    """

    return " ".join([
        preferensi.kategori.nama if preferensi.kategori else "",
        preferensi.merek or "",
        str(preferensi.ukuran or ""),
        preferensi.satuan or "",
        preferensi.kebutuhan_tambahan or "",
    ])


def hitung_rekomendasi(preferensi, daftar_produk, batas=10):
    """
    Content-Based Filtering menggunakan:
    1. Preprocessing
    2. TF-IDF
    3. Cosine Similarity

    Produk difilter berdasarkan stok dan budget,
    kemudian diurutkan berdasarkan skor kemiripan.
    """

    # Filter produk yang tersedia dan sesuai anggaran
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

    # Preprocessing dokumen produk
    dokumen_produk = [
        preprocessing_teks(
            buat_dokumen_produk(produk)
        )
        for produk in kandidat
    ]

    # Preprocessing preferensi pengguna
    dokumen_preferensi = preprocessing_teks(
        buat_dokumen_preferensi(preferensi)
    )

    if not dokumen_preferensi:
        return []

    # Menghapus dokumen produk yang kosong
    data_valid = [
        (produk, dokumen)
        for produk, dokumen in zip(
            kandidat,
            dokumen_produk
        )
        if dokumen.strip()
    ]

    if not data_valid:
        return []

    produk_valid, dokumen_valid = zip(*data_valid)

    try:
        # Mengubah teks menjadi vektor TF-IDF
        vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b\w+\b"
        )

        matriks = vectorizer.fit_transform(
            list(dokumen_valid) + [dokumen_preferensi]
        )

        # Memisahkan vektor produk dan preferensi
        vektor_produk = matriks[:-1]
        vektor_preferensi = matriks[-1]

        # Menghitung Cosine Similarity
        skor = cosine_similarity(
            vektor_preferensi,
            vektor_produk
        ).flatten()

    except ValueError:
        return []

    # Menggabungkan produk dengan skor kecocokan
    hasil = list(zip(produk_valid, skor.tolist()))

    # Mengurutkan berdasarkan skor tertinggi
    hasil.sort(
        key=lambda item: (
            -item[1],
            item[0].harga
        )
    )

    # Mengambil maksimal 10 rekomendasi
    return hasil[:batas]
