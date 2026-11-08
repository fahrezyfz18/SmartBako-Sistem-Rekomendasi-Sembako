<<<<<<< HEAD
"""View halaman publik dan autentikasi SmartBako."""
=======
from decimal import Decimal, InvalidOperation
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d

from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
<<<<<<< HEAD
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
=======
from django.shortcuts import render, redirect, get_object_or_404

from .models import Kategori, Produk
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d


# ==========================================
# PEMBATASAN AKSES ADMIN
# ==========================================

def cek_admin(user):
    return user.is_authenticated and user.is_staff


admin_required = user_passes_test(
    cek_admin,
    login_url='/admin/login/'
)


# ==========================================
# DASHBOARD PENGGUNA
# ==========================================

def beranda(request):
    return render(
        request,
        'smartbako/panel_pengguna/dashboard.html'
    )


# ==========================================
# DASHBOARD ADMIN
# ==========================================

@admin_required
def dashboard_admin(request):
    context = {
<<<<<<< HEAD
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
=======
        'total_produk': Produk.objects.count(),
        'total_kategori': Kategori.objects.count(),
        'total_pengguna': User.objects.count(),
        'total_rekomendasi': 0,
        'grafik_rekomendasi': [],
        'kategori_populer': [],
        'produk_populer': [],
    }

    return render(
        request,
        'smartbako/panel_admin/dashboard.html',
        context
    )


# ==========================================
# KELOLA KATEGORI
# ==========================================
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d

@admin_required
def daftar_kategori(request):
    kategori = Kategori.objects.all()

<<<<<<< HEAD
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
=======
    context = {
        'kategori': kategori,
        'total_kategori': kategori.count(),
    }

    return render(
        request,
        'smartbako/panel_admin/kelola_kategori/daftar.html',
        context
    )


@admin_required
def tambah_kategori(request):
    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        deskripsi = request.POST.get('deskripsi', '').strip()
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d

        if not nama:
            messages.error(request, 'Nama kategori wajib diisi.')

        elif Kategori.objects.filter(nama__iexact=nama).exists():
            messages.error(request, 'Nama kategori sudah tersedia.')

<<<<<<< HEAD
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
=======
        else:
            Kategori.objects.create(
                nama=nama,
                deskripsi=deskripsi
            )

            messages.success(request, 'Kategori berhasil ditambahkan.')
            return redirect('daftar_kategori')

    return render(
        request,
        'smartbako/panel_admin/kelola_kategori/tambah.html'
    )


@admin_required
def edit_kategori(request, id):
    kategori = get_object_or_404(Kategori, id=id)

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        deskripsi = request.POST.get('deskripsi', '').strip()

        if not nama:
            messages.error(request, 'Nama kategori wajib diisi.')

        elif Kategori.objects.filter(
            nama__iexact=nama
        ).exclude(id=id).exists():
            messages.error(request, 'Nama kategori sudah digunakan.')

        else:
            kategori.nama = nama
            kategori.deskripsi = deskripsi
            kategori.save()

            messages.success(request, 'Kategori berhasil diperbarui.')
            return redirect('daftar_kategori')

    context = {
        'kategori': kategori,
    }

    return render(
        request,
        'smartbako/panel_admin/kelola_kategori/edit.html',
        context
    )


@admin_required
def hapus_kategori(request, id):
    kategori = get_object_or_404(Kategori, id=id)

    if request.method == 'POST':
        try:
            kategori.delete()
            messages.success(request, 'Kategori berhasil dihapus.')

        except Exception:
            messages.error(
                request,
                'Kategori tidak dapat dihapus karena masih digunakan oleh produk.'
            )
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d

    return redirect('daftar_kategori')


# ==========================================
# KELOLA PRODUK
# ==========================================

@admin_required
def daftar_produk(request):
    return render(
        request,
<<<<<<< HEAD
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
=======
        'smartbako/panel_admin/kelola_produk/daftar.html'
    )


@admin_required
def tambah_produk(request):
    kategori = Kategori.objects.all()

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        kategori_id = request.POST.get('kategori', '')
        deskripsi = request.POST.get('deskripsi', '').strip()
        harga = request.POST.get('harga', '').strip()
        stok = request.POST.get('stok', '').strip()
        gambar = request.FILES.get('gambar')

        if not nama or not kategori_id or not harga or not stok:
            messages.error(
                request,
                'Nama, kategori, harga, dan stok wajib diisi.'
            )

        else:
            try:
                kategori_obj = Kategori.objects.get(id=kategori_id)
                harga_decimal = Decimal(harga)
                stok_integer = int(stok)

                if harga_decimal < 0 or stok_integer < 0:
                    messages.error(
                        request,
                        'Harga dan stok tidak boleh bernilai negatif.'
                    )

                else:
                    Produk.objects.create(
                        nama=nama,
                        kategori=kategori_obj,
                        deskripsi=deskripsi,
                        harga=harga_decimal,
                        stok=stok_integer,
                        gambar=gambar
                    )

                    messages.success(
                        request,
                        'Produk berhasil ditambahkan.'
                    )

                    return redirect('daftar_produk')

            except Kategori.DoesNotExist:
                messages.error(
                    request,
                    'Kategori yang dipilih tidak ditemukan.'
                )

            except (InvalidOperation, ValueError):
                messages.error(
                    request,
                    'Harga atau stok yang dimasukkan tidak valid.'
                )

    context = {
        'kategori': kategori,
    }

    return render(
        request,
        'smartbako/panel_admin/kelola_produk/tambah.html',
        context
    )


@admin_required
def edit_produk(request, id):
    produk = get_object_or_404(Produk, id=id)
    kategori = Kategori.objects.all()

    if request.method == 'POST':
        nama = request.POST.get('nama', '').strip()
        kategori_id = request.POST.get('kategori', '')
        deskripsi = request.POST.get('deskripsi', '').strip()
        harga = request.POST.get('harga', '').strip()
        stok = request.POST.get('stok', '').strip()
        gambar = request.FILES.get('gambar')

        if not nama or not kategori_id or not harga or not stok:
            messages.error(
                request,
                'Nama, kategori, harga, dan stok wajib diisi.'
            )

        else:
            try:
                kategori_obj = Kategori.objects.get(id=kategori_id)
                harga_decimal = Decimal(harga)
                stok_integer = int(stok)

                if harga_decimal < 0 or stok_integer < 0:
                    messages.error(
                        request,
                        'Harga dan stok tidak boleh bernilai negatif.'
                    )

                else:
                    produk.nama = nama
                    produk.kategori = kategori_obj
                    produk.deskripsi = deskripsi
                    produk.harga = harga_decimal
                    produk.stok = stok_integer

                    if gambar:
                        produk.gambar = gambar

                    produk.save()

                    messages.success(
                        request,
                        'Produk berhasil diperbarui.'
                    )

                    return redirect('daftar_produk')

            except Kategori.DoesNotExist:
                messages.error(
                    request,
                    'Kategori yang dipilih tidak ditemukan.'
                )

            except (InvalidOperation, ValueError):
                messages.error(
                    request,
                    'Harga atau stok yang dimasukkan tidak valid.'
                )

    context = {
        'produk': produk,
        'kategori': kategori,
    }

    return render(
        request,
        'smartbako/panel_admin/kelola_produk/edit.html',
        context
    )


@admin_required
def hapus_produk(request, id):
    produk = get_object_or_404(Produk, id=id)

    if request.method == 'POST':
        produk.delete()

        messages.success(
            request,
            'Produk berhasil dihapus.'
        )

    return redirect('daftar_produk')


# ==========================================
# KELOLA PENGGUNA
# ==========================================

@admin_required
def daftar_pengguna(request):
    pengguna = User.objects.all().order_by('-date_joined')

    context = {
        'pengguna': pengguna,
        'total_pengguna': pengguna.count(),
    }

    return render(
        request,
        'smartbako/panel_admin/kelola_pengguna/daftar.html',
        context
    )


@admin_required
def ubah_status_pengguna(request, id):
    pengguna = get_object_or_404(User, id=id)

    if request.method == 'POST':
        if pengguna.is_superuser:
            messages.error(
                request,
                'Status akun superuser tidak dapat diubah melalui halaman ini.'
            )

        else:
            pengguna.is_active = not pengguna.is_active
            pengguna.save(update_fields=['is_active'])

            if pengguna.is_active:
                messages.success(
                    request,
                    'Akun pengguna berhasil diaktifkan.'
                )
            else:
                messages.success(
                    request,
                    'Akun pengguna berhasil dinonaktifkan.'
                )

    return redirect('daftar_pengguna')


@admin_required
def hapus_pengguna(request, id):
    pengguna = get_object_or_404(User, id=id)

    if request.method == 'POST':
        if pengguna.is_superuser:
            messages.error(
                request,
                'Akun superuser tidak dapat dihapus melalui halaman ini.'
            )

        elif request.user.is_authenticated and pengguna.id == request.user.id:
            messages.error(
                request,
                'Kamu tidak dapat menghapus akun yang sedang digunakan.'
            )

        else:
            pengguna.delete()
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d
            messages.success(
                request,
                'Akun pengguna berhasil dihapus.'
            )

<<<<<<< HEAD
    return render(request, "smartbako/auth/register.html", {"form": form})


@require_POST
def logout_pengguna(request):
    logout(request)
    messages.success(request, "Kamu berhasil keluar dari akun.")
    return redirect("smartbako:landing_page")
=======
    return redirect('daftar_pengguna')


# ==========================================
# LOGOUT ADMIN
# ==========================================

@admin_required
def logout_admin(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/admin/login/')

    return redirect('dashboard_admin')
>>>>>>> 7bba253e0cd0a7244ef1e96482bef6ce7916ed0d
