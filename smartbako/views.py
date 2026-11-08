"""View halaman publik dan autentikasi SmartBako."""

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CustomUserCreationForm
from .models import Kategori, Produk

User = get_user_model()


# ==================================================
# FUNGSI PENDUKUNG
# ==================================================

def filter_katalog(request, produk_list):
    """Filter katalog berdasarkan kata kunci (?q=) dan kategori (?kategori=)."""
    kata_kunci = request.GET.get("q", "").strip()
    kategori_id = request.GET.get("kategori", "").strip()

    if kata_kunci:
        produk_list = produk_list.filter(
            Q(nama__icontains=kata_kunci)
            | Q(merek__icontains=kata_kunci)
            | Q(deskripsi__icontains=kata_kunci)
        )

    # Nilai non-angka diabaikan agar tidak memicu error 500.
    if kategori_id.isdigit():
        produk_list = produk_list.filter(kategori_id=int(kategori_id))
    else:
        kategori_id = ""

    return produk_list, kata_kunci, kategori_id


def halaman_awal_pengguna(user):
    """Nama URL tujuan setelah login sesuai peran pengguna."""
    if user.is_staff:
        return "smartbako:dashboard_admin"
    return "smartbako:beranda"


# ==================================================
# HALAMAN PUBLIK
# ==================================================

def landing_page(request):
    context = {
        "produk_terbaru": (
            Produk.objects
            .filter(stok__gt=0)
            .select_related("kategori")
            .order_by("-tanggal_dibuat")[:8]
        ),
        "total_produk": Produk.objects.count(),
        "total_kategori": Kategori.objects.count(),
    }
    return render(request, "smartbako/landing_page/beranda.html", context)


def fitur_publik(request):
    return render(request, "smartbako/landing_page/fitur.html")


def katalog_publik(request):
    produk_list = Produk.objects.filter(stok__gt=0).select_related("kategori")
    produk_list, kata_kunci, kategori_id = filter_katalog(request, produk_list)

    context = {
        "produk_list": produk_list,
        "kategori_list": Kategori.objects.all(),
        "kata_kunci": kata_kunci,
        "kategori_terpilih": kategori_id,
    }
    return render(request, "smartbako/landing_page/produk.html", context)


def tentang_kami(request):
    return render(request, "smartbako/landing_page/tentang_kami.html")


# ==================================================
# AUTENTIKASI
# ==================================================

def login_pengguna(request):
    """
    Login memakai email dan kata sandi.
    Parameter ?next= dihormati selama mengarah ke situs ini sendiri.
    """
    if request.user.is_authenticated:
        return redirect(halaman_awal_pengguna(request.user))

    # Halaman tujuan setelah login: dari form (POST) atau dari URL (?next=).
    tujuan = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = None

        # Tabel User Django mengautentikasi lewat username, jadi username
        # pemilik email dicari dulu. Pengguna tidak perlu mengetahuinya.
        pemilik = User.objects.filter(email__iexact=email).first() if email else None
        if pemilik is not None:
            user = authenticate(
                request,
                username=pemilik.get_username(),
                password=password,
            )

        if user is not None:
            login(request, user)

            if tujuan and url_has_allowed_host_and_scheme(
                tujuan,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(tujuan)

            return redirect(halaman_awal_pengguna(user))

        # ModelBackend mengembalikan None untuk akun nonaktif,
        # sehingga pesan ini mencakup kedua kondisi.
        messages.error(
            request,
            "Email atau kata sandi salah, atau akun tidak aktif.",
        )

    return render(
        request,
        "smartbako/auth/login.html",
        {"tujuan": tujuan},
    )


def registrasi_pengguna(request):
    if request.user.is_authenticated:
        return redirect(halaman_awal_pengguna(request.user))

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

    return render(request, "smartbako/auth/register.html", {"form": form})


@require_POST
def logout_pengguna(request):
    logout(request)
    messages.success(request, "Kamu berhasil keluar dari akun.")
    return redirect("smartbako:landing_page")