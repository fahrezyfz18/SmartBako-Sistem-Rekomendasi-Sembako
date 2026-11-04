
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordChangeForm,
)
from django.core.exceptions import ValidationError

from .models import Produk, Preferensi


# ==========================================================
# FORM REGISTRASI PENGGUNA
# ==========================================================

class CustomUserCreationForm(UserCreationForm):

    first_name = forms.CharField(
        label="Nama Lengkap",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan nama lengkap",
                "autocomplete": "name",
            }
        ),
    )

    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Buat username",
                "autocomplete": "username",
            }
        ),
    )

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "nama@email.com",
                "autocomplete": "email",
            }
        ),
    )

    password1 = forms.CharField(
        label="Kata Sandi",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Minimal 8 karakter",
                "autocomplete": "new-password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Konfirmasi Kata Sandi",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan ulang kata sandi",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "username",
            "email",
            "password1",
            "password2",
        )

    def clean_first_name(self):
        nama = self.cleaned_data["first_name"].strip()

        if not nama:
            raise ValidationError(
                "Nama lengkap wajib diisi."
            )

        return nama

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "Email sudah terdaftar. Gunakan email lain."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.email = self.cleaned_data["email"]
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

        widgets = {
            "kategori": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "budget_min": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Anggaran minimum",
                    "min": "0",
                }
            ),

            "budget_max": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Anggaran maksimum",
                    "min": "0",
                    "required": True,
                }
            ),

            "ukuran": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contoh: 5",
                    "min": "0",
                }
            ),

            "satuan": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contoh: kg, liter, pcs",
                }
            ),

            "merek": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Merek yang diinginkan",
                }
            ),

            "kebutuhan_tambahan": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Tuliskan kebutuhan tambahan",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        budget_min = cleaned_data.get("budget_min")
        budget_max = cleaned_data.get("budget_max")
        ukuran = cleaned_data.get("ukuran")

        if budget_max is not None and budget_max <= 0:
            self.add_error(
                "budget_max",
                "Anggaran maksimum harus lebih dari nol.",
            )

        if (
            budget_min is not None
            and budget_min < 0
        ):
            self.add_error(
                "budget_min",
                "Anggaran minimum tidak boleh negatif.",
            )

        if (
            budget_min is not None
            and budget_max is not None
            and budget_min > budget_max
        ):
            self.add_error(
                "budget_min",
                "Anggaran minimum tidak boleh melebihi anggaran maksimum.",
            )

        if ukuran is not None and ukuran <= 0:
            self.add_error(
                "ukuran",
                "Ukuran harus lebih dari nol.",
            )

        return cleaned_data


# ==========================================================
# FORM PROFIL PENGGUNA
# ==========================================================

class ProfilForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "first_name",
            "email",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nama lengkap",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "nama@email.com",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        pengguna_lain = User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        )

        if pengguna_lain.exists():
            raise ValidationError(
                "Email sudah digunakan oleh pengguna lain."
            )

        return email


# ==========================================================
# FORM UBAH KATA SANDI
# ==========================================================

class PasswordPenggunaForm(PasswordChangeForm):

    old_password = forms.CharField(
        label="Kata Sandi Lama",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan kata sandi lama",
                "autocomplete": "current-password",
            }
        ),
    )

    new_password1 = forms.CharField(
        label="Kata Sandi Baru",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan kata sandi baru",
                "autocomplete": "new-password",
            }
        ),
    )

    new_password2 = forms.CharField(
        label="Konfirmasi Kata Sandi Baru",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ulangi kata sandi baru",
                "autocomplete": "new-password",
            }
        ),
    )
