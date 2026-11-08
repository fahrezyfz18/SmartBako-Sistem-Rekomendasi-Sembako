
"""
View panel pengguna SmartBako.

File ini mengatur halaman yang digunakan oleh pengguna,
seperti melihat produk, mencari rekomendasi, membandingkan produk,
melihat riwayat, dan mengelola profil.
"""

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    FilterKatalogForm,
    PasswordPenggunaForm,
    PreferensiForm,
    ProfilForm,
)
from .models import DetailRekomendasi, Kategori, Preferensi, Produk, Rekomendasi
from .services.recommendation import simpan_rekomendasi


# Jumlah produk yang ditampilkan dalam satu halaman.
PRODUK_PER_HALAMAN = 12

# Jumlah riwayat yang ditampilkan dalam satu halaman.
RIWAYAT_PER_HALAMAN = 10

# Maksimal produk yang dapat dibandingkan sekaligus.
BATAS_BANDINGKAN = 3

# Jumlah produk yang ditampilkan pada tabel perbandingan hasil rekomendasi.
JUMLAH_PERBANDINGAN_HASIL = 3


# ==================================================
# FUNGSI PENDUKUNG
# ==================================================

def daftar_merek(produk_queryset):
    """Mengambil daftar merek produk yang tidak kosong."""
    return (
        produk_queryset
        .exclude(merek="")
        .order_by("merek")
        .values_list("merek", flat=True)
        .distinct()
    )


def rekomendasi_milik(user):
    """Mengambil rekomendasi berdasarkan pengguna yang sedang login."""
    return Rekomendasi.objects.filter(preferensi__pengguna=user)


# ==================================================
# BERANDA PENGGUNA
# ==================================================

@login_required
def beranda(request):
    """Menampilkan halaman utama pengguna."""

    # Mengambil rekomendasi terakhir milik pengguna.
    rekomendasi_terakhir = (
        rekomendasi_milik(request.user)
        .select_related("preferensi", "preferensi__kategori")
        .first()
    )

    # Mengambil maksimal empat produk dari rekomendasi terakhir.
    produk_rekomendasi = (
        rekomendasi_terakhir.detail.select_related(
            "produk",
            "produk__kategori"
        )[:4]
        if rekomendasi_terakhir
        else []
    )

    # Data yang akan dikirim ke halaman HTML.
    context = {
        "kategori_list": Kategori.objects.annotate(
            jumlah_produk=Count("produk", filter=Q(produk__stok__gt=0))
        ),
        "rekomendasi_terakhir": rekomendasi_terakhir,
        "produk_rekomendasi": produk_rekomendasi,
        "total_produk": Produk.objects.filter(stok__gt=0).count(),
        "total_riwayat": rekomendasi_milik(request.user).count(),
    }

    return render(
        request,
        "smartbako/panel_pengguna/dashboard.html",
        context
    )


# ==================================================
# DAFTAR PRODUK
# ==================================================

@login_required
def katalog(request):
    """Menampilkan daftar produk yang masih tersedia."""

    # Mengambil produk dengan stok lebih dari nol.
    produk_list = (
        Produk.objects
        .filter(stok__gt=0)
        .select_related("kategori")
    )

    # Mengambil data filter dari form.
    form = FilterKatalogForm(request.GET or None)

    urutan = "nama"

    if form.is_valid():
        data = form.cleaned_data

        # Mencari produk berdasarkan nama, merek, atau deskripsi.
        if data["q"]:
            produk_list = produk_list.filter(
                Q(nama__icontains=data["q"])
                | Q(merek__icontains=data["q"])
                | Q(deskripsi__icontains=data["q"])
            )

        # Memfilter produk berdasarkan kategori.
        if data["kategori"]:
            produk_list = produk_list.filter(
                kategori=data["kategori"]
            )

        # Memfilter produk berdasarkan merek.
        if data["merek"]:
            produk_list = produk_list.filter(
                merek__icontains=data["merek"]
            )

        # Memfilter berdasarkan harga minimum.
        if data["harga_min"] is not None:
            produk_list = produk_list.filter(
                harga__gte=data["harga_min"]
            )

        # Memfilter berdasarkan harga maksimum.
        if data["harga_max"] is not None:
            produk_list = produk_list.filter(
                harga__lte=data["harga_max"]
            )

        # Memfilter berdasarkan ukuran produk.
        if data["ukuran"] is not None:
            produk_list = produk_list.filter(
                ukuran=data["ukuran"]
            )

        urutan = data["urutkan"] or "nama"

    # Mengatur urutan produk sesuai pilihan pengguna.
    produk_list = produk_list.order_by({
        "termurah": "harga",
        "termahal": "-harga",
        "terbaru": "-tanggal_dibuat",
    }.get(urutan, "nama"))

    # Membagi daftar produk menjadi beberapa halaman.
    page_obj = Paginator(
        produk_list,
        PRODUK_PER_HALAMAN
    ).get_page(request.GET.get("page"))

    context = {
        "form": form,
        "page_obj": page_obj,
        "merek_list": daftar_merek(
            Produk.objects.filter(stok__gt=0)
        ),
        "ada_filter": bool(
            request.GET.dict().keys() - {"page", "urutkan"}
        ),
    }

    return render(
        request,
        "smartbako/panel_pengguna/produk/daftar.html",
        context
    )


# ==================================================
# DETAIL PRODUK
# ==================================================

@login_required
def detail_produk(request, pk):
    """Menampilkan informasi lengkap produk."""

    # Mengambil produk berdasarkan ID.
    produk = (
        Produk.objects
        .select_related("kategori")
        .filter(pk=pk)
        .first()
    )

    # Jika produk tidak ditemukan, tampilkan halaman khusus.
    if produk is None:
        return render(
            request,
            "smartbako/panel_pengguna/produk/tidak_ditemukan.html",
            status=404,
        )

    # Mengambil produk lain yang memiliki kategori sama.
    produk_serupa = (
        Produk.objects
        .filter(kategori=produk.kategori, stok__gt=0)
        .exclude(pk=produk.pk)
        .select_related("kategori")[:4]
    )

    context = {
        "produk": produk,
        "produk_serupa": produk_serupa,
    }

    return render(
        request,
        "smartbako/panel_pengguna/produk/detail.html",
        context
    )


# ==================================================
# PREFERENSI DAN REKOMENDASI
# ==================================================

def nilai_awal_preferensi(request):
    """
    Mengambil nilai awal form preferensi.

    Data dapat berasal dari preferensi sebelumnya
    atau dari pilihan produk yang ingin dicari kembali.
    """

    id_ulangi = request.GET.get("ulangi", "")

    # Jika pengguna memilih tombol ulangi, ambil data preferensi lama.
    if id_ulangi.isdigit():
        lama = Preferensi.objects.filter(
            pk=int(id_ulangi),
            pengguna=request.user
        ).first()

        if lama:
            return {
                "kategori": lama.kategori_id,
                "budget_min": lama.budget_min,
                "budget_max": lama.budget_max,
                "ukuran": lama.ukuran,
                "satuan": lama.satuan,
                "merek": lama.merek,
                "kebutuhan_tambahan": lama.kebutuhan_tambahan,
            }

    # Mengambil data yang dikirim melalui URL.
    kunci = ("kategori", "budget_max", "ukuran", "satuan", "merek")

    return {
        k: request.GET[k]
        for k in kunci
        if request.GET.get(k)
    }


@login_required
def atur_preferensi(request):
    """Menyimpan preferensi pengguna dan membuat rekomendasi."""

    if request.method == "POST":
        # Mengambil data yang dikirim melalui form.
        form = PreferensiForm(request.POST)

        if form.is_valid():
            # Menyimpan preferensi dengan menghubungkannya ke akun pengguna.
            preferensi = form.save(commit=False)
            preferensi.pengguna = request.user
            preferensi.save()

            # Menghitung dan menyimpan hasil rekomendasi.
            simpan_rekomendasi(
                preferensi,
                batas=form.cleaned_data["jumlah_rekomendasi"],
            )

            return redirect(
                "smartbako:rekomendasi",
                pk=preferensi.pk
            )

        # Menampilkan pesan jika kategori atau anggaran belum diisi.
        if "kategori" in form.errors or "budget_max" in form.errors:
            messages.error(
                request,
                "Lengkapi data preferensi terlebih dahulu."
            )

    else:
        # Menampilkan form dengan nilai awal jika tersedia.
        form = PreferensiForm(
            initial=nilai_awal_preferensi(request)
        )

    context = {
        "form": form,
        "merek_list": daftar_merek(
            Produk.objects.filter(stok__gt=0)
        ),
    }

    return render(
        request,
        "smartbako/panel_pengguna/rekomendasi/atur_preferensi.html",
        context
    )


@login_required
def rekomendasi(request, pk):
    """Menampilkan hasil rekomendasi berdasarkan preferensi pengguna."""

    # Mengambil preferensi milik pengguna yang sedang login.
    preferensi = get_object_or_404(
        Preferensi.objects.select_related("kategori"),
        pk=pk,
        pengguna=request.user,
    )

    # Mengambil hasil rekomendasi yang sudah tersimpan.
    rekomendasi_obj = preferensi.rekomendasi.first()

    # Jika belum ada hasil rekomendasi, sistem akan menghitungnya.
    if rekomendasi_obj is None:
        rekomendasi_obj = simpan_rekomendasi(preferensi)

    # Mengambil daftar produk hasil rekomendasi.
    hasil_rekomendasi = list(
        rekomendasi_obj.detail.select_related(
            "produk",
            "produk__kategori"
        )
    )

    context = {
        "preferensi": preferensi,
        "rekomendasi": rekomendasi_obj,
        "hasil_rekomendasi": hasil_rekomendasi,
        "hasil_perbandingan": hasil_rekomendasi[
            :JUMLAH_PERBANDINGAN_HASIL
        ],
    }

    return render(
        request,
        "smartbako/panel_pengguna/rekomendasi/hasil.html",
        context
    )


# ==================================================
# RIWAYAT REKOMENDASI
# ==================================================

@login_required
def riwayat_rekomendasi(request):
    """Menampilkan riwayat rekomendasi milik pengguna."""

    riwayat = (
        rekomendasi_milik(request.user)
        .select_related("preferensi", "preferensi__kategori")
        .prefetch_related(
            Prefetch(
                "detail",
                queryset=DetailRekomendasi.objects.filter(
                    peringkat=1
                ).select_related("produk"),
                to_attr="produk_teratas",
            )
        )
        .order_by("-tanggal_rekomendasi")
    )

    # Membagi riwayat menjadi beberapa halaman.
    page_obj = Paginator(
        riwayat,
        RIWAYAT_PER_HALAMAN
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "smartbako/panel_pengguna/riwayat/daftar.html",
        {"page_obj": page_obj},
    )


# ==================================================
# PERBANDINGAN PRODUK
# ==================================================

@login_required
def bandingkan_produk(request):
    """Membandingkan beberapa produk yang dipilih pengguna."""

    # Mengambil ID produk dari URL.
    # Hanya ID berupa angka yang akan digunakan.
    daftar_id = [
        int(nilai)
        for nilai in request.GET.getlist("produk")
        if nilai.isdigit()
    ]

    # Menghilangkan ID yang sama dan membatasi jumlah produk.
    daftar_id = list(dict.fromkeys(daftar_id))[:BATAS_BANDINGKAN]

    # Mengambil data produk berdasarkan ID yang dipilih.
    produk_map = Produk.objects.select_related("kategori").in_bulk(
        daftar_id
    )

    produk_dipilih = [
        produk_map[i]
        for i in daftar_id
        if i in produk_map
    ]

    # Mengambil nilai kecocokan dari rekomendasi terakhir pengguna.
    skor_map = {}

    rekomendasi_terakhir = rekomendasi_milik(request.user).first()

    if rekomendasi_terakhir:
        skor_map = dict(
            rekomendasi_terakhir.detail
            .filter(produk_id__in=daftar_id)
            .values_list("produk_id", "skor_kecocokan")
        )

    # Menambahkan nilai kecocokan ke setiap produk yang dipilih.
    for produk in produk_dipilih:
        produk.skor_kecocokan = skor_map.get(produk.pk)

    context = {
        "produk_dipilih": produk_dipilih,
        "batas_bandingkan": BATAS_BANDINGKAN,
    }

    return render(
        request,
        "smartbako/panel_pengguna/produk/bandingkan.html",
        context
    )


# ==================================================
# PROFIL DAN KATA SANDI
# ==================================================

@login_required
def profil_pengguna(request):
    """Menampilkan dan mengubah informasi profil pengguna."""

    if request.method == "POST":
        # Mengambil data profil yang dikirim pengguna.
        form = ProfilForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Profil berhasil diperbarui."
            )

            return redirect("smartbako:profil")

        # Mengambil kembali data asli jika form tidak valid.
        request.user.refresh_from_db()

    else:
        # Menampilkan data profil yang sudah tersimpan.
        form = ProfilForm(instance=request.user)

    context = {
        "form": form,
        "total_riwayat": rekomendasi_milik(request.user).count(),
    }

    return render(
        request,
        "smartbako/panel_pengguna/profil/profil.html",
        context
    )


@login_required
def ubah_password(request):
    """Mengubah kata sandi akun pengguna."""

    if request.method == "POST":
        # Memeriksa kata sandi lama dan kata sandi baru.
        form = PasswordPenggunaForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():
            user = form.save()

            # Menjaga agar pengguna tetap login setelah mengganti kata sandi.
            update_session_auth_hash(request, user)

            messages.success(
                request,
                "Kata sandi berhasil diperbarui."
            )

            return redirect("smartbako:profil")

    else:
        # Menampilkan form perubahan kata sandi.
        form = PasswordPenggunaForm(user=request.user)

    return render(
        request,
        "smartbako/panel_pengguna/profil/ubah_password.html",
        {"form": form},
    )
