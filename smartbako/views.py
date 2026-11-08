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

# Fungsi untuk mencari dan memfilter produk.
def filter_katalog(request, produk_list):

    # Mengambil kata kunci pencarian dari pengguna.
    kata_kunci = request.GET.get("q", "").strip()

    # Mengambil ID kategori yang dipilih.
    kategori_id = request.GET.get("kategori", "").strip()

    # Jika pengguna memasukkan kata kunci.
    if kata_kunci:
        produk_list = produk_list.filter(
            Q(nama__icontains=kata_kunci)
            | Q(merek__icontains=kata_kunci)
            | Q(deskripsi__icontains=kata_kunci)
        )

    # Memeriksa apakah ID kategori berupa angka.
    if kategori_id.isdigit():
        produk_list = produk_list.filter(
            kategori_id=int(kategori_id)
        )
    else:
        kategori_id = ""

    # Mengembalikan hasil pencarian.
    return produk_list, kata_kunci, kategori_id


# Fungsi menentukan halaman setelah login.
def halaman_awal_pengguna(user):

    # Jika pengguna merupakan admin.
    if user.is_staff:
        return "smartbako:dashboard_admin"

    # Jika pengguna merupakan pengguna biasa.
    return "smartbako:beranda"


# ==================================================
# HALAMAN PUBLIK
# ==================================================

# Halaman utama SmartBako.
def landing_page(request):

    # Mengambil data produk yang masih tersedia.
    context = {
        "produk_terbaru": (
            Produk.objects
            .filter(stok__gt=0)
            .select_related("kategori")
            .order_by("-tanggal_dibuat")[:8]
        ),

        # Menghitung seluruh produk.
        "total_produk": Produk.objects.count(),

        # Menghitung seluruh kategori.
        "total_kategori": Kategori.objects.count(),
    }

    # Menampilkan halaman beranda.
    return render(
        request,
        "smartbako/landing_page/beranda.html",
        context
    )


# Halaman informasi fitur aplikasi.
def fitur_publik(request):
    return render(
        request,
        "smartbako/landing_page/fitur.html"
    )


# Halaman katalog produk.
def katalog_publik(request):

    # Mengambil produk yang memiliki stok.
    produk_list = Produk.objects.filter(
        stok__gt=0
    ).select_related("kategori")

    # Memproses pencarian dan filter produk.
    produk_list, kata_kunci, kategori_id = filter_katalog(
        request,
        produk_list
    )

    # Menyiapkan data untuk ditampilkan.
    context = {
        "produk_list": produk_list,
        "kategori_list": Kategori.objects.all(),
        "kata_kunci": kata_kunci,
        "kategori_terpilih": kategori_id,
    }

    # Menampilkan katalog produk.
    return render(
        request,
        "smartbako/landing_page/produk.html",
        context
    )


# Halaman tentang SmartBako.
def tentang_kami(request):
    return render(
        request,
        "smartbako/landing_page/tentang_kami.html"
    )


# ==================================================
# AUTENTIKASI
# ==================================================

# Fungsi login pengguna dan admin.
def login_pengguna(request):

    # Jika sudah login, arahkan sesuai peran.
    if request.user.is_authenticated:
        return redirect(
            halaman_awal_pengguna(request.user)
        )

    # Mengambil halaman tujuan setelah login.
    tujuan = request.POST.get("next") or request.GET.get("next", "")

    # Memeriksa apakah formulir dikirim.
    if request.method == "POST":

        # Mengambil email dan kata sandi.
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        user = None

        # Mencari akun berdasarkan email.
        pemilik = User.objects.filter(
            email__iexact=email
        ).first() if email else None

        # Memeriksa kata sandi menggunakan sistem Django.
        if pemilik is not None:
            user = authenticate(
                request,
                username=pemilik.get_username(),
                password=password,
            )

        # Jika login berhasil.
        if user is not None:

            # Menyimpan status login pengguna.
            login(request, user)

            # Memeriksa keamanan halaman tujuan.
            if tujuan and url_has_allowed_host_and_scheme(
                tujuan,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(tujuan)

            # Mengarahkan pengguna sesuai perannya.
            return redirect(
                halaman_awal_pengguna(user)
            )

        # Jika email atau kata sandi salah.
        messages.error(
            request,
            "Email atau kata sandi salah, atau akun tidak aktif.",
        )

    # Menampilkan halaman login.
    return render(
        request,
        "smartbako/auth/login.html",
        {"tujuan": tujuan},
    )


# Fungsi registrasi akun baru.
def registrasi_pengguna(request):

    # Jika sudah login, kembali ke halaman utama.
    if request.user.is_authenticated:
        return redirect(
            halaman_awal_pengguna(request.user)
        )

    # Memeriksa formulir yang dikirim pengguna.
    if request.method == "POST":

        # Mengambil data formulir.
        form = CustomUserCreationForm(request.POST)

        # Memeriksa apakah data sudah benar.
        if form.is_valid():

            # Menyimpan akun baru.
            form.save()

            # Menampilkan pesan keberhasilan.
            messages.success(
                request,
                "Registrasi berhasil. Silakan masuk ke akun kamu.",
            )

            # Mengarahkan pengguna ke halaman login.
            return redirect("smartbako:login")

    else:

        # Membuat formulir kosong.
        form = CustomUserCreationForm()

    # Menampilkan halaman registrasi.
    return render(
        request,
        "smartbako/auth/register.html",
        {"form": form}
    )


# Fungsi logout atau keluar dari akun.
@require_POST
def logout_pengguna(request):

    # Mengakhiri sesi login.
    logout(request)

    # Menampilkan pesan berhasil.
    messages.success(
        request,
        "Kamu berhasil keluar dari akun."
    )

    # Kembali ke halaman utama.
    return redirect("smartbako:landing_page")
