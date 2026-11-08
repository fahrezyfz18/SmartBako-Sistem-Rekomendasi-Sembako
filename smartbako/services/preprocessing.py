"""Preprocessing teks untuk sistem rekomendasi SmartBako."""

import re
import unicodedata

STOPWORDS = {
    "dan", "atau", "yang", "di", "ke",
    "dari", "untuk", "dengan", "pada",
    "adalah", "ini", "itu", "dalam",
    "serta", "agar", "lebih", "sangat",
    "dapat", "bisa", "saya", "ingin",
    "butuh", "mencari", "produk",
}


def preprocessing_teks(teks):
    """
    Membersihkan teks produk/preferensi tanpa menghilangkan angka ukuran.

    Tahapan: normalisasi unicode, case folding, pembersihan karakter,
    tokenisasi, dan penghapusan stopword.
    """
    if not teks:
        return ""

    teks = unicodedata.normalize("NFKC", str(teks)).lower()

    # Koma desimal (2,5) diseragamkan menjadi titik (2.5).
    teks = re.sub(r"(?<=\d),(?=\d)", ".", teks)

    # Hanya huruf, angka, dan titik desimal yang dipertahankan.
    teks = re.sub(r"[^a-z0-9.]+", " ", teks)

    # Titik yang bukan bagian dari angka dibuang.
    teks = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", teks)

    token = [kata for kata in teks.split() if kata not in STOPWORDS]
    return " ".join(token)