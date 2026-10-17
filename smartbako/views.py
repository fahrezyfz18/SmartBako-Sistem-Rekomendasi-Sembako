
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models.deletion import ProtectedError
from .models import Kategori, Produk


def landing_page(request):
    return render(request, "smartbako/landing_page.html")


def beranda(request):
    produk_terbaru = Produk.objects.select_related(
        "kategori"
    ).all()[:8]

    return render(
        request,
        "smartbako/panel_pengguna/dashboard.html",
        {"produk_terbaru": produk_terbaru},
    )


def katalog(request):
    daftar_produk = Produk.objects.select_related("kategori").all()
    daftar_kategori = Kategori.objects.all()

    kata_kunci = request.GET.get("q", "").strip()
    kategori_id = request.GET.get("kategori", "")

    if kata_kunci:
        daftar_produk = daftar_produk.filter(
            nama__icontains=kata_kunci
        ) | daftar_produk.filter(
            merek__icontains=kata_kunci
        )

    if kategori_id.isdigit():
        daftar_produk = daftar_produk.filter(
            kategori_id=int(kategori_id)
        )

    return render(
        request,
        "smartbako/panel_pengguna/katalog.html",
        {
            "produk_list": daftar_produk.distinct(),
            "kategori_list": daftar_kategori,
            "kata_kunci": kata_kunci,
            "kategori_terpilih": kategori_id,
        },
    )


def detail_produk(request, produk_id):
    produk = get_object_or_404(Produk, pk=produk_id)

    return render(
        request,
        "smartbako/panel_pengguna/detail_produk.html",
        {"produk": produk},
    )


# ==============================
# KELOLA KATEGORI ADMIN
# ==============================

def daftar_kategori(request):
    kategori_list = Kategori.objects.all()

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/daftar.html",
        {
            "kategori_list": kategori_list,
        },
    )


def tambah_kategori(request):
    if request.method == "POST":
        nama = request.POST.get("nama", "").strip()
        deskripsi = request.POST.get("deskripsi", "").strip()

        if not nama:
            return render(
                request,
                "smartbako/panel_admin/kelola_kategori/tambah.html",
                {
                    "nama": nama,
                    "deskripsi": deskripsi,
                    "error": "Nama kategori wajib diisi.",
                },
            )

        if Kategori.objects.filter(nama__iexact=nama).exists():
            return render(
                request,
                "smartbako/panel_admin/kelola_kategori/tambah.html",
                {
                    "nama": nama,
                    "deskripsi": deskripsi,
                    "error": "Nama kategori sudah digunakan.",
                },
            )

        Kategori.objects.create(
            nama=nama,
            deskripsi=deskripsi,
        )

        return redirect("smartbako:daftar_kategori")

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/tambah.html",
    )


def edit_kategori(request, kategori_id):
    kategori = get_object_or_404(Kategori, pk=kategori_id)

    if request.method == "POST":
        nama = request.POST.get("nama", "").strip()
        deskripsi = request.POST.get("deskripsi", "").strip()

        duplikat = Kategori.objects.filter(
            nama__iexact=nama
        ).exclude(pk=kategori.pk).exists()

        if not nama:
            error = "Nama kategori wajib diisi."
        elif duplikat:
            error = "Nama kategori sudah digunakan."
        else:
            kategori.nama = nama
            kategori.deskripsi = deskripsi
            kategori.save()

            return redirect("smartbako:daftar_kategori")

        return render(
            request,
            "smartbako/panel_admin/kelola_kategori/edit.html",
            {
                "kategori": kategori,
                "error": error,
            },
        )

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/edit.html",
        {
            "kategori": kategori,
        },
    )


def hapus_kategori(request, kategori_id):
    if request.method == "POST":
        kategori = get_object_or_404(Kategori, pk=kategori_id)

        try:
            kategori.delete()
        except ProtectedError:
            return render(
                request,
                "smartbako/panel_admin/kelola_kategori/daftar.html",
                {
                    "kategori_list": Kategori.objects.all(),
                    "error": (
                        "Kategori tidak dapat dihapus karena "
                        "masih digunakan oleh produk."
                    ),
                },
            )

    return redirect("smartbako:daftar_kategori")
