
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .services.recommendation import hitung_rekomendasi

from .models import (
    Kategori,
    Produk,
    Preferensi,
    Rekomendasi,
    DetailRekomendasi,
)
from .forms import PreferensiForm, ProfilForm


# ==================================================
# FUNGSI PENDUKUNG SISTEM REKOMENDASI
# ==================================================

def buat_teks_produk(produk):
    return " ".join([
        produk.nama or "",
        produk.merek or "",
        produk.kategori.nama if produk.kategori else "",
        produk.deskripsi or "",
        str(produk.ukuran or ""),
        produk.satuan or "",
    ])


def buat_teks_preferensi(preferensi):
    return " ".join([
        preferensi.kategori.nama if preferensi.kategori else "",
        preferensi.merek or "",
        str(preferensi.ukuran or ""),
        preferensi.satuan or "",
        preferensi.kebutuhan_tambahan or "",
    ])


def hitung_rekomendasi(preferensi, produk_list):
    produk_list = list(produk_list)

    if not produk_list:
        return []

    semua_teks = [
        buat_teks_produk(produk)
        for produk in produk_list
    ]

    semua_teks.append(
        buat_teks_preferensi(preferensi)
    )

    try:
        vectorizer = TfidfVectorizer()
        matriks = vectorizer.fit_transform(semua_teks)

        vektor_produk = matriks[:-1]
        vektor_preferensi = matriks[-1]

        skor = cosine_similarity(
            vektor_preferensi,
            vektor_produk,
        ).flatten()

    except ValueError:
        skor = [0.0] * len(produk_list)

    hasil = list(zip(produk_list, skor))
    hasil.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return hasil


def buat_alasan_rekomendasi(produk, preferensi):
    alasan = []

    if (
        preferensi.kategori
        and produk.kategori_id == preferensi.kategori_id
    ):
        alasan.append("Kategori sesuai dengan preferensi.")

    if (
        preferensi.merek
        and produk.merek
        and preferensi.merek.lower() in produk.merek.lower()
    ):
        alasan.append("Merek sesuai dengan preferensi.")

    if (
        preferensi.ukuran is not None
        and produk.ukuran == preferensi.ukuran
    ):
        alasan.append("Ukuran produk sesuai.")

    if (
        preferensi.satuan
        and produk.satuan
        and preferensi.satuan.lower() == produk.satuan.lower()
    ):
        alasan.append("Satuan produk sesuai.")

    if produk.harga <= preferensi.budget_max:
        alasan.append("Harga sesuai dengan batas anggaran.")

    if not alasan:
        alasan.append(
            "Produk memiliki kemiripan atribut dengan kebutuhan pengguna."
        )

    return " ".join(alasan)


# ==================================================
# DASHBOARD PENGGUNA
# ==================================================

@login_required
def beranda(request):
    preferensi_terakhir = Preferensi.objects.filter(
        pengguna=request.user
    ).first()

    context = {
        "total_produk": Produk.objects.filter(
            stok__gt=0
        ).count(),

        "total_kategori": Kategori.objects.count(),

        "total_riwayat": Rekomendasi.objects.filter(
            preferensi__pengguna=request.user
        ).count(),

        "preferensi_terakhir": preferensi_terakhir,

        "produk_terbaru": Produk.objects.filter(
            stok__gt=0
        ).select_related("kategori").order_by(
            "-tanggal_dibuat"
        )[:6],
    }

    return render(
        request,
        "smartbako/panel_pengguna/dashboard.html",
        context,
    )


# ==================================================
# KATALOG PRODUK
# ==================================================

@login_required
def katalog(request):
    produk_list = Produk.objects.filter(
        stok__gt=0
    ).select_related("kategori")

    kata_kunci = request.GET.get("q", "").strip()
    kategori_id = request.GET.get("kategori", "").strip()

    if kata_kunci:
        produk_list = produk_list.filter(
            Q(nama__icontains=kata_kunci)
            | Q(merek__icontains=kata_kunci)
            | Q(deskripsi__icontains=kata_kunci)
        )

    if kategori_id:
        produk_list = produk_list.filter(
            kategori_id=kategori_id
        )

    return render(
        request,
        "smartbako/panel_pengguna/katalog.html",
        {
            "produk_list": produk_list,
            "kategori_list": Kategori.objects.all(),
            "kata_kunci": kata_kunci,
            "kategori_terpilih": kategori_id,
        },
    )


# ==================================================
# DETAIL PRODUK
# ==================================================

@login_required
def detail_produk(request, id):
    produk = get_object_or_404(
        Produk.objects.select_related("kategori"),
        id=id,
    )

    produk_terkait = Produk.objects.filter(
        kategori=produk.kategori,
        stok__gt=0,
    ).exclude(
        id=produk.id
    )[:4]

    return render(
        request,
        "smartbako/panel_pengguna/detail_produk.html",
        {
            "produk": produk,
            "produk_terkait": produk_terkait,
        },
    )


# ==================================================
# PREFERENSI PENGGUNA
# ==================================================

@login_required
def atur_preferensi(request):
    if request.method == "POST":
        form = PreferensiForm(request.POST)

        if form.is_valid():
            preferensi = form.save(commit=False)
            preferensi.pengguna = request.user
            preferensi.save()

            messages.success(
                request,
                "Preferensi berhasil disimpan.",
            )

            return redirect(
                "smartbako:rekomendasi",
                id=preferensi.id,
            )
    else:
        form = PreferensiForm()

    return render(
        request,
        "smartbako/panel_pengguna/preferensi/atur_preferensi.html",
        {"form": form},
    )


# ==================================================
# REKOMENDASI PRODUK
# ==================================================

@login_required
def rekomendasi(request, id):
    preferensi = get_object_or_404(
        Preferensi,
        id=id,
        pengguna=request.user,
    )

    produk_list = Produk.objects.filter(
        stok__gt=0,
        harga__lte=preferensi.budget_max,
    ).select_related("kategori")

    if preferensi.budget_min is not None:
        produk_list = produk_list.filter(
            harga__gte=preferensi.budget_min
        )

    hasil = hitung_rekomendasi(
        preferensi,
        produk_list,
    )

    rekomendasi_obj = Rekomendasi.objects.create(
        preferensi=preferensi,
        jumlah_hasil=len(hasil),
    )

    detail_list = []

    for peringkat, (produk, skor) in enumerate(
        hasil,
        start=1,
    ):
        detail_list.append(
            DetailRekomendasi(
                rekomendasi=rekomendasi_obj,
                produk=produk,
                skor_kecocokan=Decimal(
                    str(round(float(skor), 8))
                ),
                peringkat=peringkat,
                alasan_rekomendasi=buat_alasan_rekomendasi(
                    produk,
                    preferensi,
                ),
            )
        )

    if detail_list:
        DetailRekomendasi.objects.bulk_create(detail_list)

    hasil_rekomendasi = rekomendasi_obj.detail.select_related(
        "produk",
        "produk__kategori",
    ).all()

    return render(
        request,
        "smartbako/panel_pengguna/rekomendasi.html",
        {
            "preferensi": preferensi,
            "rekomendasi": rekomendasi_obj,
            "hasil_rekomendasi": hasil_rekomendasi,
        },
    )


# ==================================================
# RIWAYAT REKOMENDASI
# ==================================================

@login_required
def riwayat_rekomendasi(request):
    riwayat = Rekomendasi.objects.filter(
        preferensi__pengguna=request.user
    ).select_related(
        "preferensi"
    ).order_by(
        "-tanggal_rekomendasi"
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
    daftar_id = request.GET.getlist("produk")

    produk_dipilih = Produk.objects.filter(
        id__in=daftar_id
    ).select_related("kategori")

    return render(
        request,
        "smartbako/panel_pengguna/bandingkan.html",
        {
            "produk_dipilih": produk_dipilih,
        },
    )


# ==================================================
# PROFIL PENGGUNA
# ==================================================

@login_required
def profil_pengguna(request):
    if request.method == "POST":
        form = ProfilForm(
            request.POST,
            instance=request.user,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Profil berhasil diperbarui.",
            )
            return redirect("smartbako:profil")
    else:
        form = ProfilForm(instance=request.user)

    return render(
        request,
        "smartbako/panel_pengguna/profil/profil.html",
        {"form": form},
    )


# ==================================================
# UBAH KATA SANDI
# ==================================================

@login_required
def ubah_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(
            user=request.user,
            data=request.POST,
        )

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            messages.success(
                request,
                "Kata sandi berhasil diperbarui.",
            )

            return redirect("smartbako:ubah_password")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(
        request,
        "smartbako/panel_pengguna/profil/ubah_password.html",
        {"form": form},
    )
