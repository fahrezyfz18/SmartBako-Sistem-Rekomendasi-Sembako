"""Form aplikasi SmartBako (pengguna dan panel admin)."""

import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Kategori, Preferensi, Produk

User = get_user_model()

# Batas ukuran gambar produk (2 MB).
BATAS_UKURAN_GAMBAR = 2 * 1024 * 1024

# Kelas CSS input form.
KELAS_INPUT_PENGGUNA = "form-control"
KELAS_SELECT_PENGGUNA = "form-select"
KELAS_INPUT_ADMIN = "form-control"      # Bootstrap 5
KELAS_SELECT_ADMIN = "form-select"      # Bootstrap 5


# ==========================================================
# FORM REGISTRASI PENGGUNA
# ==========================================================

def buat_username_unik(email):
    """
    Membuat username otomatis dari email, misalnya budi@gmail.com -> budi.
    Jika sudah dipakai, ditambah angka: budi1, budi2, dst.
    Username tetap dibutuhkan tabel User bawaan Django, tetapi tidak
    pernah diketik pengguna karena login memakai email.
    """
    dasar = re.sub(r"[^\w.+-]", "", email.split("@")[0])[:140] or "pengguna"
    username = dasar
    nomor = 1

    while User.objects.filter(username__iexact=username).exists():
        username = f"{dasar}{nomor}"
        nomor += 1

    return username


class CustomUserCreationForm(UserCreationForm):
    """
    Form pendaftaran akun pengguna biasa (bukan admin).
    Pengguna cukup mengisi nama, email, dan kata sandi.
    """

    first_name = forms.CharField(
        label="Nama Lengkap",
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Masukkan nama lengkap",
            "autocomplete": "name",
        }),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "nama@email.com",
            "autocomplete": "email",
        }),
    )
    password1 = forms.CharField(
        label="Kata Sandi",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Minimal 8 karakter",
            "autocomplete": "new-password",
        }),
    )
    password2 = forms.CharField(
        label="Konfirmasi Kata Sandi",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Masukkan ulang kata sandi",
            "autocomplete": "new-password",
        }),
    )

    class Meta:
        model = User
        fields = ("first_name", "email")

    def clean_first_name(self):
        nama = self.cleaned_data["first_name"].strip()
        if not nama:
            raise ValidationError("Nama lengkap wajib diisi.")
        return nama

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email sudah terdaftar. Gunakan email lain.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.email = self.cleaned_data["email"]
        user.username = buat_username_unik(user.email)
        # Akun dari halaman registrasi selalu pengguna biasa.
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True

        if commit:
            user.save()
        return user


# ==========================================================
# FORM PREFERENSI PENGGUNA
# ==========================================================

class PreferensiForm(forms.ModelForm):
    """
    Form isian kebutuhan pengguna untuk proses rekomendasi.
    Sesuai wireframe "Cari Rekomendasi Produk" dan US-05/US-06:
    kategori dan budget wajib; ukuran, satuan, merek, kebutuhan opsional.
    """

    PILIHAN_JUMLAH = [(5, "5 produk"), (10, "10 produk")]

    # Bukan kolom tabel; hanya mengatur banyaknya hasil (US-05 AC3: 5–10).
    jumlah_rekomendasi = forms.TypedChoiceField(
        label="Jumlah rekomendasi",
        choices=PILIHAN_JUMLAH,
        coerce=int,
        initial=5,
        widget=forms.Select(attrs={"class": KELAS_SELECT_PENGGUNA}),
    )

    class Meta:
        model = Preferensi
        fields = [
            "kategori",
            "budget_min",
            "budget_max",
            "ukuran",
            "satuan",
            "merek",
            "kebutuhan_tambahan",
        ]
        labels = {
            "kategori": "Kategori produk",
            "budget_min": "Budget minimum (Rp)",
            "budget_max": "Budget maksimum (Rp)",
            "ukuran": "Ukuran atau jumlah",
            "satuan": "Satuan",
            "merek": "Merek yang disukai",
            "kebutuhan_tambahan": "Kebutuhan tambahan",
        }
        widgets = {
            "kategori": forms.Select(attrs={"class": KELAS_SELECT_PENGGUNA}),
            "budget_min": forms.NumberInput(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "placeholder": "0",
                "min": "0",
                "step": "500",
            }),
            "budget_max": forms.NumberInput(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "placeholder": "Contoh: 100000",
                "min": "0",
                "step": "500",
            }),
            "ukuran": forms.NumberInput(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "placeholder": "Contoh: 5",
                "min": "0",
                "step": "0.01",
            }),
            "satuan": forms.TextInput(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "placeholder": "kg, liter, pcs",
                "list": "daftar-satuan",
            }),
            "merek": forms.TextInput(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "placeholder": "Opsional",
                "list": "daftar-merek",
            }),
            "kebutuhan_tambahan": forms.Textarea(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "rows": 3,
                "placeholder": "Contoh: beras pulen untuk nasi uduk",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Wireframe: kategori dan budget wajib diisi.
        self.fields["kategori"].required = True
        self.fields["kategori"].empty_label = "Pilih kategori"
        self.fields["budget_max"].required = True

    def clean_satuan(self):
        return self.cleaned_data["satuan"].strip().lower()

    def clean_merek(self):
        return self.cleaned_data["merek"].strip()

    def clean(self):
        cleaned_data = super().clean()
        budget_min = cleaned_data.get("budget_min")
        budget_max = cleaned_data.get("budget_max")

        if (
            budget_min is not None
            and budget_max is not None
            and budget_min > budget_max
        ):
            self.add_error(
                "budget_min",
                "Budget minimum tidak boleh melebihi budget maksimum.",
            )
        return cleaned_data


class FilterKatalogForm(forms.Form):
    """Pencarian, filter, dan urutan halaman Daftar Produk (FR-08–FR-10)."""

    URUTAN = [
        ("nama", "Nama A–Z"),
        ("termurah", "Harga termurah"),
        ("termahal", "Harga termahal"),
        ("terbaru", "Terbaru"),
    ]

    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Cari nama, merek, atau deskripsi produk",
            "type": "search",
        }),
    )
    kategori = forms.ModelChoiceField(
        queryset=Kategori.objects.all(),
        required=False,
        empty_label="Semua kategori",
        widget=forms.Select(attrs={"class": KELAS_SELECT_PENGGUNA}),
    )
    merek = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Semua merek",
            "list": "daftar-merek",
        }),
    )
    harga_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Min",
            "step": "500",
        }),
    )
    harga_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Maks",
            "step": "500",
        }),
    )
    ukuran = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Contoh: 5",
            "step": "0.01",
        }),
    )
    urutkan = forms.ChoiceField(
        required=False,
        choices=URUTAN,
        widget=forms.Select(attrs={"class": KELAS_SELECT_PENGGUNA}),
    )


# ==========================================================
# FORM PROFIL DAN KATA SANDI PENGGUNA
# ==========================================================

class ProfilForm(forms.ModelForm):
    """Form ubah nama dan email pengguna."""

    class Meta:
        model = User
        fields = ["first_name", "email"]
        labels = {
            "first_name": "Nama Lengkap",
            "email": "Email",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "placeholder": "Nama lengkap",
                "autocomplete": "name",
            }),
            "email": forms.EmailInput(attrs={
                "class": KELAS_INPUT_PENGGUNA,
                "placeholder": "nama@email.com",
                "autocomplete": "email",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Field bawaan User boleh kosong; di SmartBako keduanya wajib.
        self.fields["first_name"].required = True
        self.fields["email"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        sudah_dipakai = (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if sudah_dipakai:
            raise ValidationError("Email sudah digunakan oleh pengguna lain.")
        return email


class PasswordPenggunaForm(PasswordChangeForm):
    """Form ubah kata sandi dengan label dan gaya SmartBako."""

    old_password = forms.CharField(
        label="Kata Sandi Lama",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Masukkan kata sandi lama",
            "autocomplete": "current-password",
        }),
    )
    new_password1 = forms.CharField(
        label="Kata Sandi Baru",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Masukkan kata sandi baru",
            "autocomplete": "new-password",
        }),
    )
    new_password2 = forms.CharField(
        label="Konfirmasi Kata Sandi Baru",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": KELAS_INPUT_PENGGUNA,
            "placeholder": "Ulangi kata sandi baru",
            "autocomplete": "new-password",
        }),
    )


# ==========================================================
# FORM PANEL ADMIN
# ==========================================================

class KategoriForm(forms.ModelForm):
    """Form tambah/edit kategori di panel admin (Bootstrap)."""

    class Meta:
        model = Kategori
        fields = ["nama", "deskripsi"]
        labels = {
            "nama": "Nama Kategori",
            "deskripsi": "Deskripsi",
        }
        widgets = {
            "nama": forms.TextInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "placeholder": "Contoh: Beras",
            }),
            "deskripsi": forms.Textarea(attrs={
                "class": KELAS_INPUT_ADMIN,
                "rows": 4,
                "placeholder": "Deskripsi singkat kategori (opsional)",
            }),
        }

    def clean_nama(self):
        nama = self.cleaned_data["nama"].strip()
        sudah_ada = (
            Kategori.objects
            .filter(nama__iexact=nama)
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if sudah_ada:
            raise ValidationError("Kategori dengan nama ini sudah ada.")
        return nama


class ProdukForm(forms.ModelForm):
    """
    Form tambah/edit produk di panel admin (Bootstrap).
    Kolom mengikuti Product Backlog US-03 dan wireframe Tambah/Ubah Produk:
    nama, kategori, merek, harga, ukuran, satuan, stok, deskripsi, foto.
    """

    class Meta:
        model = Produk
        fields = [
            "nama",
            "kategori",
            "merek",
            "harga",
            "ukuran",
            "satuan",
            "stok",
            "deskripsi",
            "gambar",
        ]
        labels = {
            "nama": "Nama Produk",
            "kategori": "Kategori",
            "merek": "Merek",
            "harga": "Harga (Rp)",
            "ukuran": "Ukuran",
            "satuan": "Satuan",
            "stok": "Stok",
            "deskripsi": "Deskripsi",
            "gambar": "Foto Produk",
        }
        widgets = {
            "nama": forms.TextInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "placeholder": "Contoh: Beras Pandan Wangi 5 kg",
            }),
            "kategori": forms.Select(attrs={"class": KELAS_SELECT_ADMIN}),
            "merek": forms.TextInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "placeholder": "Contoh: Topi Koki",
            }),
            "harga": forms.NumberInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "placeholder": "Contoh: 75000",
                "min": "0",
                "step": "1",
            }),
            "ukuran": forms.NumberInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "placeholder": "Contoh: 5",
                "min": "0",
                "step": "0.01",
            }),
            "satuan": forms.TextInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "placeholder": "kg, gram, liter, ml, pcs, butir",
                "list": "daftar-satuan",
            }),
            "stok": forms.NumberInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "placeholder": "Jumlah stok",
                "min": "0",
            }),
            "deskripsi": forms.Textarea(attrs={
                "class": KELAS_INPUT_ADMIN,
                "rows": 4,
                "placeholder": "Kegunaan, keunggulan, dan informasi penting produk",
            }),
            # FileInput biasa agar tampilan rapi; gambar lama tetap dipakai
            # bila kolom ini dikosongkan saat mengubah produk.
            "gambar": forms.FileInput(attrs={
                "class": KELAS_INPUT_ADMIN,
                "accept": "image/png,image/jpeg,image/webp",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kategori"].empty_label = "Pilih kategori"
        # Wajib sesuai US-03 AC1 (merek, ukuran, satuan dipakai rekomendasi).
        for nama_field in ("merek", "ukuran", "satuan"):
            self.fields[nama_field].required = True

    def clean_nama(self):
        return self.cleaned_data["nama"].strip()

    def clean_merek(self):
        return self.cleaned_data["merek"].strip()

    def clean_satuan(self):
        return self.cleaned_data["satuan"].strip().lower()

    def clean_gambar(self):
        gambar = self.cleaned_data.get("gambar")
        # `size` hanya ada pada file yang baru diunggah.
        if gambar and hasattr(gambar, "size") and gambar.size > BATAS_UKURAN_GAMBAR:
            raise ValidationError("Ukuran gambar maksimal 2 MB.")
        return gambar


class FilterPreferensiForm(forms.Form):
    """Filter halaman Riwayat Preferensi admin (US-13 AC2: tanggal & kategori)."""

    q = forms.CharField(
        required=False,
        label="Cari",
        widget=forms.TextInput(attrs={
            "class": KELAS_INPUT_ADMIN,
            "placeholder": "Nama atau email pengguna",
        }),
    )
    kategori = forms.ModelChoiceField(
        queryset=Kategori.objects.all(),
        required=False,
        empty_label="Semua kategori",
        widget=forms.Select(attrs={"class": KELAS_SELECT_ADMIN}),
    )
    tanggal_awal = forms.DateField(
        required=False,
        label="Dari tanggal",
        widget=forms.DateInput(attrs={"class": KELAS_INPUT_ADMIN, "type": "date"}),
    )
    tanggal_akhir = forms.DateField(
        required=False,
        label="Sampai tanggal",
        widget=forms.DateInput(attrs={"class": KELAS_INPUT_ADMIN, "type": "date"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        awal = cleaned_data.get("tanggal_awal")
        akhir = cleaned_data.get("tanggal_akhir")
        if awal and akhir and awal > akhir:
            self.add_error("tanggal_akhir", "Tanggal akhir tidak boleh sebelum tanggal awal.")
        return cleaned_data