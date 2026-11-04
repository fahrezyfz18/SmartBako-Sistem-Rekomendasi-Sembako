
import re

STOPWORDS = {
    "dan", "atau", "yang", "di", "ke", "dari", "untuk",
    "dengan", "pada", "adalah", "ini", "itu", "dalam",
    "serta", "agar", "lebih", "sangat", "dapat", "bisa"
}


def preprocessing_teks(teks):
    """Membersihkan teks dan menghapus kata umum."""

    if not teks:
        return ""

    # Mengubah teks menjadi huruf kecil.
    teks = str(teks).lower()

    # Menghapus angka dan karakter khusus.
    teks = re.sub(r"[^a-zA-Z\s]", " ", teks)

    # Menghapus spasi berlebih.
    teks = re.sub(r"\s+", " ", teks).strip()

    # Tokenisasi.
    kata = teks.split()

    # Menghapus stopword.
    kata = [k for k in kata if k not in STOPWORDS]

    return " ".join(kata)
