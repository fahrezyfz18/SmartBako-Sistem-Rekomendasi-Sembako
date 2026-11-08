
"""Preprocessing teks untuk sistem rekomendasi SmartBako."""

import re
import unicodedata


# Kata-kata yang tidak terlalu berpengaruh dalam pencarian produk.
# Kata ini akan dihapus agar sistem lebih fokus pada informasi penting.
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
    Membersihkan teks produk dan preferensi pengguna.

    Tahapannya:
    1. Menyamakan bentuk teks.
    2. Mengubah huruf menjadi huruf kecil.
    3. Menghapus karakter yang tidak diperlukan.
    4. Memisahkan kata.
    5. Menghapus kata yang tidak penting.
    """

    # Jika teks kosong, langsung mengembalikan string kosong.
    if not teks:
        return ""

    # Menyamakan bentuk karakter dan mengubah huruf menjadi kecil.
    teks = unicodedata.normalize("NFKC", str(teks)).lower()

    # Mengubah koma desimal menjadi titik.
    # Contoh: 2,5 menjadi 2.5.
    teks = re.sub(r"(?<=\d),(?=\d)", ".", teks)

    # Mempertahankan huruf, angka, dan titik desimal.
    teks = re.sub(r"[^a-z0-9.]+", " ", teks)

    # Menghapus titik yang bukan bagian dari angka.
    teks = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", teks)

    # Memisahkan teks menjadi beberapa kata.
    # Kata yang termasuk stopwords tidak dimasukkan.
    token = [
        kata
        for kata in teks.split()
        if kata not in STOPWORDS
    ]

    # Menggabungkan kembali kata-kata yang sudah dibersihkan.
    return " ".join(token)
