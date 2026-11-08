"""View panel pengguna SmartBako."""

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PasswordPenggunaForm, PreferensiForm, ProfilForm
from .models import Kategori, Preferensi, Produk, Rekomendasi
from .services.recommendation import simpan_rekomendasi
from .views import filter_katalog

# Jumlah maksimal produk pada halaman perbandingan
# (harus sama dengan data-max di compare_tray.html / pengguna.js).
BATAS_BANDINGKAN = 4


# ==================================================
# DASHBOARD PENGGUNA
# ==================================================

@login_required
def beranda(request):
    produk_tersedia = Produk.objects.filter(stok__gt=0)

    context = {
        "total_produk": produk_tersedia.count(),
        "total_kategori": Kategori.objects.count(),
        "total_riwayat": Rekomendasi.objects.filter(
            preferensi__pengguna=request.user
        ).count(),
        "preferensi_terakhir": (
            Preferensi.objects
            .filter(pengguna=request.user)
            .select_related("kategori")
            .first()
        ),
        "produk_terbaru": (
            produk_tersedia
            .select_related("kategori")
            .order_by("-tanggal_dibuat")[:6]
        ),
    }
    return render(request, "smartbako/panel_pengguna/dashboard.html", context)


# ==================================================
# KATALOG DAN DETAIL PRODUK
# ==================================================

@login_required
def katalog(request):
    produk_list = Produk.objects.filter(stok__gt=0).select_related("kategori")
    produk_list, kata_kunci, kategori_id = filter_katalog(request, produk_list)

    context = {
        "produk_list": produk_list,
        "kategori_list": Kategori.objects.all(),
        "kata_kunci": kata_kunci,
        "kategori_terpilih": kategori_id,
    }
    return render(request, "smartbako/panel_pengguna/katalog.html", context)


@login_required
def detail_produk(request, pk):
    produk = get_object_or_404(Produk.objects.select_related("kategori"), pk=pk)

    produk_terkait = (
        Produk.objects
        .filter(kategori=produk.kategori, stok__gt=0)
        .exclude(id=produk.id)
        .select_related("kategori")[:4]
    )

    context = {
        "produk": produk,
        "produk_terkait": produk_terkait,
    }
    return render(request, "smartbako/panel_pengguna/detail_produk.html", context)


# ==================================================
# PREFERENSI DAN REKOMENDASI
# ==================================================

@login_required
def atur_preferensi(request):
    """
    Menyimpan preferensi lalu langsung menghitung rekomendasi.
    Proses yang menulis ke database hanya terjadi pada POST.
    """
    if request.method == "POST":
        form = PreferensiForm(request.POST)
        if form.is_valid():
            preferensi = form.save(commit=False)
            preferensi.pengguna = request.user
            preferensi.save()

            simpan_rekomendasi(preferensi)

            messages.success(request, "Preferensi berhasil disimpan.")
            return redirect("smartbako:rekomendasi", pk=preferensi.pk)
    else:
        form = PreferensiForm()

    return render(
        request,
        "smartbako/panel_pengguna/preferensi/atur_preferensi.html",
        {"form": form},
    )


@login_required
def rekomendasi(request, pk):
    """
    Menampilkan hasil rekomendasi terakhir milik sebuah preferensi.

    Sebelumnya setiap kali halaman dibuka (termasuk dari menu Riwayat)
    data rekomendasi baru dibuat sehingga riwayat terus bertambah.
    Sekarang hasil yang sudah ada cukup ditampilkan ulang.
    """
    preferensi = get_object_or_404(
        Preferensi.objects.select_related("kategori"),
        pk=pk,
        pengguna=request.user,
    )

    rekomendasi_obj = preferensi.rekomendasi.first()
    if rekomendasi_obj is None:
        # Untuk data lama yang belum pernah dihitung.
        rekomendasi_obj = simpan_rekomendasi(preferensi)

    hasil_rekomendasi = rekomendasi_obj.detail.select_related(
        "produk",
        "produk__kategori",
    )

    context = {
        "preferensi": preferensi,
        "rekomendasi": rekomendasi_obj,
        "hasil_rekomendasi": hasil_rekomendasi,
    }
    return render(request, "smartbako/panel_pengguna/rekomendasi.html", context)


@login_required
def riwayat_rekomendasi(request):
    riwayat = (
        Rekomendasi.objects
        .filter(preferensi__pengguna=request.user)
        .select_related("preferensi", "preferensi__kategori")
        .order_by("-tanggal_rekomendasi")
    )
    return render(
        request,
        "smartbako/panel_pengguna/riwayat.html",
        {"riwayat": riwayat},
    )


# ==================================================
# PERBANDINGAN PRODUK
# ==================================================

@login_required
def bandingkan_produk(request):
    # Hanya ID berupa angka yang dipakai, maksimal BATAS_BANDINGKAN produk.
    daftar_id = [
        int(nilai)
        for nilai in request.GET.getlist("produk")
        if nilai.isdigit()
    ]
    daftar_id = list(dict.fromkeys(daftar_id))[:BATAS_BANDINGKAN]

    produk_dipilih = Produk.objects.filter(id__in=daftar_id).select_related(
        "kategori"
    )
    return render(
        request,
        "smartbako/panel_pengguna/bandingkan.html",
        {"produk_dipilih": produk_dipilih},
    )


# ==================================================
# PROFIL DAN KATA SANDI
# ==================================================

@login_required
def profil_pengguna(request):
    if request.method == "POST":
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil berhasil diperbarui.")
            return redirect("smartbako:profil")
    else:
        form = ProfilForm(instance=request.user)

    return render(
        request,
        "smartbako/panel_pengguna/profil/profil.html",
        {"form": form},
    )


@login_required
def ubah_password(request):
    if request.method == "POST":
        form = PasswordPenggunaForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Agar pengguna tidak otomatis logout setelah ganti kata sandi.
            update_session_auth_hash(request, user)
            messages.success(request, "Kata sandi berhasil diperbarui.")
            return redirect("smartbako:profil")
    else:
        form = PasswordPenggunaForm(user=request.user)

    return render(
        request,
        "smartbako/panel_pengguna/profil/ubah_password.html",
        {"form": form},
    )