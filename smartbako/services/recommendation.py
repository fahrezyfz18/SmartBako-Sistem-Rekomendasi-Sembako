
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import preprocessing_teks


def buat_dokumen_produk(produk):
    """Menggabungkan atribut produk menjadi satu dokumen teks."""

    return " ".join([
        produk.nama or "",
        produk.merek or "",
        produk.kategori.nama if produk.kategori else "",
        produk.deskripsi or "",
        produk.satuan or "",
    ])


def hitung_rekomendasi(preferensi, daftar_produk):
    """
    Menghitung kemiripan produk dengan preferensi
    menggunakan TF-IDF dan Cosine Similarity.

    Hasil:
        [(produk, skor_kecocokan), ...]
    """

    produk_terpilih = []

    # Filter anggaran, kategori, merek, ukuran, dan satuan.
    for produk in daftar_produk:

        if produk.harga > preferensi.budget_max:
            continue

        if (
            preferensi.budget_min is not None
            and produk.harga < preferensi.budget_min
        ):
            continue

        if (
            preferensi.kategori_id
            and produk.kategori_id != preferensi.kategori_id
        ):
            continue

        if (
            preferensi.merek
            and preferensi.merek.lower() not in (produk.merek or "").lower()
        ):
            continue

        if (
            preferensi.ukuran is not None
            and produk.ukuran != preferensi.ukuran
        ):
            continue

        if (
            preferensi.satuan
            and preferensi.satuan.lower() != (produk.satuan or "").lower()
        ):
            continue

        produk_terpilih.append(produk)

    if not produk_terpilih:
        return []

    # Preprocessing dokumen produk.
    dokumen_produk = [
        preprocessing_teks(buat_dokumen_produk(produk))
        for produk in produk_terpilih
    ]

    # Membentuk teks preferensi.
    teks_preferensi = " ".join([
        preferensi.kategori.nama if preferensi.kategori else "",
        preferensi.merek or "",
        str(preferensi.ukuran or ""),
        preferensi.satuan or "",
        preferensi.kebutuhan_tambahan or "",
    ])

    teks_preferensi = preprocessing_teks(teks_preferensi)

    # Menghapus dokumen produk yang kosong.
    data_valid = [
        (produk, dokumen)
        for produk, dokumen in zip(produk_terpilih, dokumen_produk)
        if dokumen.strip()
    ]

    if not data_valid or not teks_preferensi.strip():
        return []

    produk_valid = [item[0] for item in data_valid]
    dokumen_valid = [item[1] for item in data_valid]

    # Menghitung bobot TF-IDF.
    vectorizer = TfidfVectorizer(
        token_pattern=r"(?u)\b\w+\b"
    )

    seluruh_dokumen = dokumen_valid + [teks_preferensi]

    try:
        matriks_tfidf = vectorizer.fit_transform(seluruh_dokumen)
    except ValueError:
        return []

    # Menghitung Cosine Similarity.
    vektor_produk = matriks_tfidf[:-1]
    vektor_preferensi = matriks_tfidf[-1]

    skor = cosine_similarity(
        vektor_preferensi,
        vektor_produk,
    ).flatten()

    hasil = list(zip(produk_valid, skor))

    # Mengurutkan dari skor tertinggi.
    hasil.sort(key=lambda item: item[1], reverse=True)

    return hasil[:10]
