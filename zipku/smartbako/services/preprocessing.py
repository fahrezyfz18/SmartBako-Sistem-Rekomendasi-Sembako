
import re
import unicodedata

STOPWORDS = {
    "dan", "atau", "yang", "di", "ke",
    "dari", "untuk", "dengan", "pada",
    "adalah", "ini", "itu", "dalam",
    "serta", "agar", "lebih", "sangat",
    "dapat", "bisa", "saya", "ingin",
    "butuh", "mencari", "produk"
}


def preprocessing_teks(teks):
    """
    Membersihkan teks produk dan preferensi
    tanpa menghilangkan informasi ukuran.
    """

    if not teks:
        return ""

    # Normalisasi karakter
    teks = unicodedata.normalize("NFKC", str(teks))

    # Mengubah huruf menjadi lowercase
    teks = teks.lower()

    # Mempertahankan huruf, angka, dan desimal
    teks = re.sub(r"[^a-z0-9.,]+", " ", teks)

    # Menghapus spasi berlebihan
    teks = re.sub(r"\s+", " ", teks).strip()

    # Tokenisasi dan penghapusan stopword
    token = teks.split()

    token = [
        kata for kata in token
        if kata not in STOPWORDS
    ]

    return " ".join(token)
