
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q, Count, ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Kategori, Produk, Rekomendasi


# ==================================================
# HAK AKSES ADMIN
# ==================================================

def cek_admin(user):
    return user.is_authenticated and user.is_staff


admin_required = user_passes_test(
    cek_admin,
    login_url="/masuk/",
)


# ==================================================
# DASHBOARD ADMIN
# ==================================================

@admin_required
def dashboard_admin(request):
    context = {
        "total_produk": Produk.objects.count(),
        "total_kategori": Kategori.objects.count(),
        "total_pengguna": User.objects.filter(
            is_staff=False,
            is_superuser=False,
        ).count(),
        "total_rekomendasi": Rekomendasi.objects.count(),

        "produk_terbaru": Produk.objects.select_related(
            "kategori"
        ).order_by("-tanggal_dibuat")[:5],

        "pengguna_terbaru": User.objects.filter(
            is_staff=False,
            is_superuser=False,
        ).order_by("-date_joined")[:5],

        "kategori_populer": Kategori.objects.annotate(
            jumlah_produk=Count("produk")
        ).order_by("-jumlah_produk")[:5],
    }

    return render(
        request,
        "smartbako/panel_admin/dashboard.html",
        context,
    )


# ==================================================
# KELOLA KATEGORI
# ==================================================

@admin_required
def daftar_kategori(request):
    kategori_list = Kategori.objects.all()

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/daftar.html",
        {"kategori_list": kategori_list},
    )


@admin_required
def tambah_kategori(request):
    if request.method == "POST":
        nama = request.POST.get("nama", "").strip()
        deskripsi = request.POST.get("deskripsi", "").strip()

        if not nama:
            messages.error(
                request,
                "Nama kategori wajib diisi.",
            )
        elif Kategori.objects.filter(
            nama__iexact=nama
        ).exists():
            messages.error(
                request,
                "Kategori sudah tersedia.",
            )
        else:
            Kategori.objects.create(
                nama=nama,
                deskripsi=deskripsi,
            )

            messages.success(
                request,
                "Kategori berhasil ditambahkan.",
            )

            return redirect("smartbako:daftar_kategori")

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/tambah.html",
    )


@admin_required
def edit_kategori(request, id):
    kategori = get_object_or_404(
        Kategori,
        id=id,
    )

    if request.method == "POST":
        nama = request.POST.get("nama", "").strip()
        deskripsi = request.POST.get("deskripsi", "").strip()

        if not nama:
            messages.error(
                request,
                "Nama kategori wajib diisi.",
            )
        elif Kategori.objects.filter(
            nama__iexact=nama
        ).exclude(id=id).exists():
            messages.error(
                request,
                "Nama kategori sudah digunakan.",
            )
        else:
            kategori.nama = nama
            kategori.deskripsi = deskripsi
            kategori.save()

            messages.success(
                request,
                "Kategori berhasil diperbarui.",
            )

            return redirect("smartbako:daftar_kategori")

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/edit.html",
        {"kategori": kategori},
    )


@admin_required
@require_POST
def hapus_kategori(request, id):
    kategori = get_object_or_404(
        Kategori,
        id=id,
    )

    try:
        kategori.delete()
        messages.success(
            request,
            "Kategori berhasil dihapus.",
        )
    except ProtectedError:
        messages.error(
            request,
            "Kategori tidak dapat dihapus karena masih digunakan oleh produk.",
        )

    return redirect("smartbako:daftar_kategori")


# ==================================================
# KELOLA PRODUK
# ==================================================

@admin_required
def daftar_produk(request):
    produk_list = Produk.objects.select_related(
        "kategori"
    ).all()

    kata_kunci = request.GET.get("q", "").strip()

    if kata_kunci:
        produk_list = produk_list.filter(
            Q(nama__icontains=kata_kunci)
            | Q(merek__icontains=kata_kunci)
        )

    return render(
        request,
        "smartbako/panel_admin/kelola_produk/daftar.html",
        {
            "produk_list": produk_list,
            "kata_kunci": kata_kunci,
        },
    )


def simpan_data_produk(request, produk=None):
    nama = request.POST.get("nama", "").strip()
    kategori_id = request.POST.get("kategori", "").strip()
    merek = request.POST.get("merek", "").strip()
    harga_input = request.POST.get("harga", "").strip()
    ukuran_input = request.POST.get("ukuran", "").strip()
    satuan = request.POST.get("satuan", "").strip()
    stok_input = request.POST.get("stok", "").strip()
    deskripsi = request.POST.get("deskripsi", "").strip()

    if not nama:
        raise ValueError("Nama produk wajib diisi.")

    kategori = get_object_or_404(
        Kategori,
        id=kategori_id,
    )

    try:
        harga = Decimal(harga_input)
        stok = int(stok_input)
        ukuran = Decimal(ukuran_input) if ukuran_input else None
    except (InvalidOperation, ValueError):
        raise ValueError(
            "Harga, ukuran, atau stok memiliki format yang tidak valid."
        )

    if harga < 0 or stok < 0:
        raise ValueError(
            "Harga dan stok tidak boleh bernilai negatif."
        )

    if ukuran is not None and ukuran < 0:
        raise ValueError(
            "Ukuran tidak boleh bernilai negatif."
        )

    if produk is None:
        produk = Produk()

    produk.nama = nama
    produk.kategori = kategori
    produk.merek = merek
    produk.harga = harga
    produk.ukuran = ukuran
    produk.satuan = satuan
    produk.stok = stok
    produk.deskripsi = deskripsi

    gambar = request.FILES.get("gambar")

    if gambar:
        produk.gambar = gambar

    produk.full_clean()
    produk.save()

    return produk


@admin_required
def tambah_produk(request):
    if request.method == "POST":
        try:
            simpan_data_produk(request)

            messages.success(
                request,
                "Produk berhasil ditambahkan.",
            )

            return redirect("smartbako:daftar_produk")

        except (ValueError, ValidationError) as error:
            messages.error(request, str(error))

    return render(
        request,
        "smartbako/panel_admin/kelola_produk/tambah.html",
        {
            "kategori_list": Kategori.objects.all(),
        },
    )


@admin_required
def edit_produk(request, id):
    produk = get_object_or_404(
        Produk,
        id=id,
    )

    if request.method == "POST":
        try:
            simpan_data_produk(request, produk)

            messages.success(
                request,
                "Produk berhasil diperbarui.",
            )

            return redirect("smartbako:daftar_produk")

        except (ValueError, ValidationError) as error:
            messages.error(request, str(error))

    return render(
        request,
        "smartbako/panel_admin/kelola_produk/edit.html",
        {
            "produk": produk,
            "kategori_list": Kategori.objects.all(),
        },
    )


@admin_required
@require_POST
def hapus_produk(request, id):
    produk = get_object_or_404(
        Produk,
        id=id,
    )

    try:
        produk.delete()

        messages.success(
            request,
            "Produk berhasil dihapus.",
        )

    except ProtectedError:
        messages.error(
            request,
            "Produk tidak dapat dihapus karena masih tercatat dalam riwayat rekomendasi.",
        )

    return redirect("smartbako:daftar_produk")


# ==================================================
# KELOLA PENGGUNA
# ==================================================

@admin_required
def daftar_pengguna(request):
    pengguna_list = User.objects.filter(
        is_staff=False,
        is_superuser=False,
    ).order_by("-date_joined")

    kata_kunci = request.GET.get("q", "").strip()

    if kata_kunci:
        pengguna_list = pengguna_list.filter(
            Q(username__icontains=kata_kunci)
            | Q(first_name__icontains=kata_kunci)
            | Q(last_name__icontains=kata_kunci)
            | Q(email__icontains=kata_kunci)
        )

    return render(
        request,
        "smartbako/panel_admin/kelola_pengguna/daftar.html",
        {
            "pengguna_list": pengguna_list,
            "kata_kunci": kata_kunci,
        },
    )


@admin_required
@require_POST
def ubah_status_pengguna(request, id):
    pengguna = get_object_or_404(
        User,
        id=id,
        is_staff=False,
        is_superuser=False,
    )

    pengguna.is_active = not pengguna.is_active
    pengguna.save(update_fields=["is_active"])

    if pengguna.is_active:
        messages.success(
            request,
            "Akun pengguna berhasil diaktifkan.",
        )
    else:
        messages.success(
            request,
            "Akun pengguna berhasil dinonaktifkan.",
        )

    return redirect("smartbako:daftar_pengguna")


@admin_required
@require_POST
def hapus_pengguna(request, id):
    pengguna = get_object_or_404(
        User,
        id=id,
        is_staff=False,
        is_superuser=False,
    )

    pengguna.delete()

    messages.success(
        request,
        "Pengguna berhasil dihapus.",
    )

    return redirect("smartbako:daftar_pengguna")


# ==================================================
# LOGOUT ADMIN
# ==================================================

@admin_required
@require_POST
def logout_admin(request):
    logout(request)

    messages.success(
        request,
        "Admin berhasil keluar dari sistem.",
    )

    return redirect("smartbako:landing_page")
