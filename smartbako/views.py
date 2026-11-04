
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import Produk, Kategori
from .forms import CustomUserCreationForm


# ==================================================
# HALAMAN PUBLIK
# ==================================================

def landing_page(request):
    context = {
        "produk_terbaru": Produk.objects.filter(
            stok__gt=0
        ).select_related("kategori").order_by("-tanggal_dibuat")[:8],
        "total_produk": Produk.objects.count(),
        "total_kategori": Kategori.objects.count(),
    }

    return render(
        request,
        "smartbako/landing_page/beranda.html",
        context,
    )


def fitur_publik(request):
    return render(
        request,
        "smartbako/landing_page/fitur.html",
    )


def katalog_publik(request):
    produk_list = Produk.objects.filter(
        stok__gt=0
    ).select_related("kategori")

    kata_kunci = request.GET.get("q", "").strip()
    kategori_id = request.GET.get("kategori", "").strip()

    if kata_kunci:
        produk_list = produk_list.filter(
            nama__icontains=kata_kunci
        ) | produk_list.filter(
            merek__icontains=kata_kunci
        ) | produk_list.filter(
            deskripsi__icontains=kata_kunci
        )

    if kategori_id:
        produk_list = produk_list.filter(
            kategori_id=kategori_id
        )

    return render(
        request,
        "smartbako/landing_page/produk.html",
        {
            "produk_list": produk_list,
            "kategori_list": Kategori.objects.all(),
            "kata_kunci": kata_kunci,
            "kategori_terpilih": kategori_id,
        },
    )


def tentang_kami(request):
    return render(
        request,
        "smartbako/landing_page/tentang_kami.html",
    )


# ==================================================
# AUTENTIKASI
# ==================================================

def login_pengguna(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("smartbako:dashboard_admin")
        return redirect("smartbako:beranda")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            if user.is_active:
                login(request, user)

                if user.is_staff:
                    return redirect("smartbako:dashboard_admin")

                return redirect("smartbako:beranda")

            messages.error(request, "Akun kamu sedang dinonaktifkan.")
        else:
            messages.error(
                request,
                "Nama pengguna atau kata sandi tidak sesuai.",
            )

    return render(
        request,
        "smartbako/auth/login.html",
    )


def registrasi_pengguna(request):
    if request.user.is_authenticated:
        return redirect("smartbako:beranda")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Registrasi berhasil. Silakan masuk ke akun kamu.",
            )
            return redirect("smartbako:login")
    else:
        form = CustomUserCreationForm()

    return render(
        request,
        "smartbako/auth/register.html",
        {"form": form},
    )


@require_POST
def logout_pengguna(request):
    logout(request)
    messages.success(request, "Kamu berhasil keluar dari akun.")
    return redirect("smartbako:landing_page")
