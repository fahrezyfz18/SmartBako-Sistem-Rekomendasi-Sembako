
from django.shortcuts import render, get_object_or_404
from .models import Kategori, Produk



def landing_page(request):
    return render(request, "smartbako/landing_page.html")
def beranda(request):
    produk_terbaru = Produk.objects.select_related("kategori").all()[:8]
    return render(request, "smartbako/panel_pengguna/dashboard.html", {"produk_terbaru": produk_terbaru})

def katalog(request):
    daftar_produk = Produk.objects.select_related("kategori").all()
    daftar_kategori = Kategori.objects.all()

    kata_kunci = request.GET.get("q", "").strip()
    kategori_id = request.GET.get("kategori", "")

    if kata_kunci:
        daftar_produk = daftar_produk.filter(nama__icontains=kata_kunci) | daftar_produk.filter(merek__icontains=kata_kunci)

    if kategori_id.isdigit():
        daftar_produk = daftar_produk.filter(kategori_id=int(kategori_id))

    context = {
        "produk_list": daftar_produk.distinct(),
        "kategori_list": daftar_kategori,
        "kata_kunci": kata_kunci,
        "kategori_terpilih": kategori_id,
    }
    return render(request, "smartbako/panel_pengguna/katalog.html", context)

def detail_produk(request, produk_id):
    produk = get_object_or_404(Produk, pk=produk_id)

    return render(
        request,
        "smartbako/panel_pengguna/detail_produk.html",
        {"produk": produk},
    )
