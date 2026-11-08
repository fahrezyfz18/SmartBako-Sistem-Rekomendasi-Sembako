"""
View panel admin SmartBako (hanya untuk akun staff).

Mencakup use case admin: Login, Kelola Data Produk, Kelola Data Kategori,
Kelola Data Pengguna, Melihat Statistik Hasil Rekomendasi (dashboard), dan
Melihat Riwayat Preferensi Pengguna.
"""

from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Count, Max, ProtectedError, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import FilterPreferensiForm, KategoriForm, ProdukForm
from .models import Kategori, Preferensi, Produk, Rekomendasi

User = get_user_model()

JUMLAH_PER_HALAMAN = 10
NAMA_HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
BATAS_STOK_MENIPIS = 10


# ==================================================
# FUNGSI PENDUKUNG
# ==================================================

def admin_required(view_func):
    """
    Membatasi view hanya untuk akun staff yang aktif.
    - Belum login -> diarahkan ke halaman login (dengan ?next=).
    - Bukan staff -> diarahkan ke dashboard pengguna.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), "smartbako:login")

        if not (user.is_active and user.is_staff):
            messages.error(request, "Halaman tersebut khusus admin.")
            return redirect("smartbako:beranda")

        return view_func(request, *args, **kwargs)

    return wrapper


def paginasi(request, queryset, jumlah=JUMLAH_PER_HALAMAN):
    """Mengembalikan objek halaman sesuai parameter ?page=."""
    return Paginator(queryset, jumlah).get_page(request.GET.get("page"))


def ambil_id_angka(request, nama_parameter):
    """Nilai ?parameter= berupa angka; selain itu dianggap kosong."""
    nilai = request.GET.get(nama_parameter, "").strip()
    return nilai if nilai.isdigit() else ""


def alamat_kembali(request, cadangan):
    """URL ?kembali= dari form, hanya jika mengarah ke situs ini sendiri."""
    tujuan = request.POST.get("kembali", "")
    if tujuan and url_has_allowed_host_and_scheme(
        tujuan,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return tujuan
    return cadangan


def hapus_file_gambar(nama_file, storage):
    """Menghapus file gambar lama dari storage bila ada."""
    if nama_file and storage.exists(nama_file):
        storage.delete(nama_file)


def data_grafik_rekomendasi(jumlah_hari=7):
    """Jumlah rekomendasi per hari selama `jumlah_hari` terakhir."""
    hari_ini = timezone.localdate()
    tanggal_awal = hari_ini - timedelta(days=jumlah_hari - 1)

    jumlah_per_tanggal = {
        baris["tanggal"]: baris["jumlah"]
        for baris in (
            Rekomendasi.objects
            .filter(tanggal_rekomendasi__date__gte=tanggal_awal)
            .annotate(tanggal=TruncDate("tanggal_rekomendasi"))
            .values("tanggal")
            .annotate(jumlah=Count("id"))
        )
    }

    nilai_tertinggi = max(jumlah_per_tanggal.values(), default=0)
    grafik = []

    for selisih in range(jumlah_hari):
        tanggal = tanggal_awal + timedelta(days=selisih)
        jumlah = jumlah_per_tanggal.get(tanggal, 0)
        grafik.append({
            "hari": NAMA_HARI[tanggal.weekday()],
            "tanggal": tanggal.strftime("%d/%m"),
            "jumlah": jumlah,
            "persentase": round(jumlah / nilai_tertinggi * 100) if nilai_tertinggi else 0,
        })

    return grafik


def data_kategori_populer(batas=3):
    """
    Kategori yang paling sering dipilih dalam preferensi pengguna,
    ditambah baris "Lainnya" sesuai wireframe dashboard.
    """
    preferensi_berkategori = Preferensi.objects.filter(kategori__isnull=False)
    total = preferensi_berkategori.count()

    if not total:
        return []

    baris_list = list(
        preferensi_berkategori
        .values("kategori__nama")
        .annotate(jumlah=Count("id"))
        .order_by("-jumlah", "kategori__nama")
    )

    hasil = [
        {
            "nama": baris["kategori__nama"],
            "jumlah": baris["jumlah"],
            "persentase": round(baris["jumlah"] / total * 100),
        }
        for baris in baris_list[:batas]
    ]

    sisa = sum(baris["jumlah"] for baris in baris_list[batas:])
    if sisa:
        hasil.append({
            "nama": "Lainnya",
            "jumlah": sisa,
            "persentase": round(sisa / total * 100),
        })

    return hasil


# ==================================================
# DASHBOARD (US-14 / FR-05)
# ==================================================

@admin_required
def dashboard_admin(request):
    context = {
        "total_produk": Produk.objects.count(),
        "total_kategori": Kategori.objects.count(),
        "total_pengguna": User.objects.filter(is_staff=False).count(),
        "total_rekomendasi": Rekomendasi.objects.count(),
        "total_stok_habis": Produk.objects.filter(stok=0).count(),
        "grafik_rekomendasi": data_grafik_rekomendasi(),
        "kategori_populer": data_kategori_populer(),
        "produk_populer": (
            Produk.objects
            .select_related("kategori")
            .annotate(jumlah_rekomendasi=Count("detail_rekomendasi"))
            .filter(jumlah_rekomendasi__gt=0)
            .order_by("-jumlah_rekomendasi", "nama")[:5]
        ),
        "preferensi_terbaru": (
            Preferensi.objects
            .select_related("pengguna", "kategori")
            .order_by("-tanggal_input")[:5]
        ),
    }
    return render(request, "smartbako/panel_admin/dashboard.html", context)


# ==================================================
# KELOLA KATEGORI (US-09 / FR-03)
# ==================================================

@admin_required
def daftar_kategori(request):
    kategori_list = Kategori.objects.annotate(jumlah_produk=Count("produk"))

    kata_kunci = request.GET.get("q", "").strip()
    if kata_kunci:
        kategori_list = kategori_list.filter(nama__icontains=kata_kunci)

    context = {
        "page_obj": paginasi(request, kategori_list),
        "total_kategori": Kategori.objects.count(),
        "kata_kunci": kata_kunci,
        # Form tambah cepat di samping tabel (sesuai wireframe).
        "form": KategoriForm(),
    }
    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/daftar.html",
        context,
    )


@admin_required
def tambah_kategori(request):
    if request.method == "POST":
        form = KategoriForm(request.POST)
        if form.is_valid():
            kategori = form.save()
            messages.success(
                request,
                f'Kategori "{kategori.nama}" berhasil ditambahkan.',
            )
            return redirect("smartbako:daftar_kategori")
    else:
        form = KategoriForm()

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/tambah.html",
        {"form": form},
    )


@admin_required
def edit_kategori(request, id):
    kategori = get_object_or_404(Kategori, pk=id)

    if request.method == "POST":
        form = KategoriForm(request.POST, instance=kategori)
        if form.is_valid():
            form.save()
            messages.success(request, "Kategori berhasil diperbarui.")
            return redirect("smartbako:daftar_kategori")
        # Judul halaman tetap memakai nama yang tersimpan di database.
        kategori.refresh_from_db()
    else:
        form = KategoriForm(instance=kategori)

    return render(
        request,
        "smartbako/panel_admin/kelola_kategori/edit.html",
        {"form": form, "kategori": kategori},
    )


@admin_required
@require_POST
def hapus_kategori(request, id):
    kategori = get_object_or_404(Kategori, pk=id)

    try:
        kategori.delete()
    except ProtectedError:
        messages.error(
            request,
            f'Kategori "{kategori.nama}" masih memiliki produk, sehingga tidak '
            "dapat dihapus. Pindahkan atau hapus produknya terlebih dahulu.",
        )
    else:
        messages.success(request, "Kategori berhasil dihapus.")

    return redirect("smartbako:daftar_kategori")


# ==================================================
# KELOLA PRODUK (US-03 / FR-02)
# ==================================================

@admin_required
def daftar_produk(request):
    produk_list = Produk.objects.select_related("kategori").order_by("nama")

    kata_kunci = request.GET.get("q", "").strip()
    kategori_id = ambil_id_angka(request, "kategori")
    status_stok = request.GET.get("stok", "")

    if kata_kunci:
        produk_list = produk_list.filter(
            Q(nama__icontains=kata_kunci) | Q(merek__icontains=kata_kunci)
        )
    if kategori_id:
        produk_list = produk_list.filter(kategori_id=int(kategori_id))
    if status_stok == "habis":
        produk_list = produk_list.filter(stok=0)
    elif status_stok == "menipis":
        produk_list = produk_list.filter(stok__gt=0, stok__lte=BATAS_STOK_MENIPIS)
    else:
        status_stok = ""

    context = {
        "page_obj": paginasi(request, produk_list),
        "total_produk": Produk.objects.count(),
        "total_stok_habis": Produk.objects.filter(stok=0).count(),
        "kategori_list": Kategori.objects.all(),
        "kata_kunci": kata_kunci,
        "kategori_terpilih": kategori_id,
        "status_stok": status_stok,
        "batas_stok_menipis": BATAS_STOK_MENIPIS,
    }
    return render(
        request,
        "smartbako/panel_admin/kelola_produk/daftar.html",
        context,
    )


@admin_required
def tambah_produk(request):
    if request.method == "POST":
        form = ProdukForm(request.POST, request.FILES)
        if form.is_valid():
            produk = form.save()
            messages.success(
                request,
                f'Produk "{produk.nama}" berhasil ditambahkan.',
            )
            return redirect("smartbako:daftar_produk")
    else:
        form = ProdukForm()

    return render(
        request,
        "smartbako/panel_admin/kelola_produk/tambah.html",
        {"form": form},
    )


@admin_required
def detail_produk_admin(request, id):
    produk = get_object_or_404(
        Produk.objects
        .select_related("kategori")
        .annotate(jumlah_rekomendasi=Count("detail_rekomendasi")),
        pk=id,
    )
    return render(
        request,
        "smartbako/panel_admin/kelola_produk/detail.html",
        {"produk": produk, "batas_stok_menipis": BATAS_STOK_MENIPIS},
    )


@admin_required
def edit_produk(request, id):
    produk = get_object_or_404(Produk.objects.select_related("kategori"), pk=id)
    # Dicatat sebelum form dibuat, karena form mengubah instance saat validasi.
    gambar_lama = produk.gambar.name if produk.gambar else ""

    if request.method == "POST":
        form = ProdukForm(request.POST, request.FILES, instance=produk)
        if form.is_valid():
            produk = form.save()

            gambar_baru = produk.gambar.name if produk.gambar else ""
            if gambar_lama and gambar_lama != gambar_baru:
                hapus_file_gambar(gambar_lama, produk.gambar.storage)

            messages.success(request, "Data produk berhasil diperbarui.")
            return redirect("smartbako:daftar_produk")
        # Kembalikan data asli agar gambar & judul halaman tetap benar.
        produk.refresh_from_db()
    else:
        form = ProdukForm(instance=produk)

    return render(
        request,
        "smartbako/panel_admin/kelola_produk/edit.html",
        {"form": form, "produk": produk},
    )


@admin_required
@require_POST
def hapus_produk(request, id):
    produk = get_object_or_404(Produk, pk=id)
    gambar = produk.gambar.name if produk.gambar else ""
    storage = produk.gambar.storage

    try:
        produk.delete()
    except ProtectedError:
        messages.error(
            request,
            f'Produk "{produk.nama}" sudah tercatat di riwayat rekomendasi '
            "dan tidak dapat dihapus. Ubah stoknya menjadi 0 agar tidak "
            "ditampilkan lagi.",
        )
    else:
        hapus_file_gambar(gambar, storage)
        messages.success(request, "Produk berhasil dihapus.")

    return redirect("smartbako:daftar_produk")


# ==================================================
# KELOLA PENGGUNA (US-11 / FR-04)
# ==================================================

@admin_required
def daftar_pengguna(request):
    pengguna_list = User.objects.order_by("-date_joined")

    kata_kunci = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    peran = request.GET.get("peran", "")

    if kata_kunci:
        pengguna_list = pengguna_list.filter(
            Q(first_name__icontains=kata_kunci)
            | Q(email__icontains=kata_kunci)
            | Q(username__icontains=kata_kunci)
        )
    if status in ("aktif", "nonaktif"):
        pengguna_list = pengguna_list.filter(is_active=(status == "aktif"))
    else:
        status = ""
    if peran in ("admin", "pengguna"):
        pengguna_list = pengguna_list.filter(is_staff=(peran == "admin"))
    else:
        peran = ""

    context = {
        "page_obj": paginasi(request, pengguna_list),
        "total_pengguna": User.objects.filter(is_staff=False).count(),
        "total_nonaktif": User.objects.filter(is_active=False).count(),
        "kata_kunci": kata_kunci,
        "status_terpilih": status,
        "peran_terpilih": peran,
    }
    return render(
        request,
        "smartbako/panel_admin/kelola_pengguna/daftar.html",
        context,
    )


@admin_required
def detail_pengguna(request, id):
    pengguna = get_object_or_404(User, pk=id)
    preferensi_pengguna = Preferensi.objects.filter(pengguna=pengguna)

    context = {
        "pengguna": pengguna,
        "total_preferensi": preferensi_pengguna.count(),
        "total_rekomendasi": Rekomendasi.objects.filter(
            preferensi__pengguna=pengguna
        ).count(),
        "preferensi_list": (
            preferensi_pengguna
            .select_related("kategori")
            .annotate(jumlah_hasil=Max("rekomendasi__jumlah_hasil"))
            .order_by("-tanggal_input")[:10]
        ),
    }
    return render(
        request,
        "smartbako/panel_admin/kelola_pengguna/detail.html",
        context,
    )


def boleh_dikelola(request, pengguna):
    """Admin tidak boleh mengubah akunnya sendiri atau akun superuser."""
    if pengguna.pk == request.user.pk:
        messages.error(request, "Kamu tidak dapat mengubah akunmu sendiri.")
        return False

    if pengguna.is_superuser:
        messages.error(request, "Akun admin utama tidak dapat diubah.")
        return False

    return True


@admin_required
@require_POST
def ubah_status_pengguna(request, id):
    pengguna = get_object_or_404(User, pk=id)

    if boleh_dikelola(request, pengguna):
        pengguna.is_active = not pengguna.is_active
        pengguna.save(update_fields=["is_active"])

        status = "diaktifkan" if pengguna.is_active else "dinonaktifkan"
        messages.success(request, f'Akun "{pengguna.email}" berhasil {status}.')

    return redirect(alamat_kembali(request, "smartbako:daftar_pengguna"))


@admin_required
@require_POST
def hapus_pengguna(request, id):
    pengguna = get_object_or_404(User, pk=id)

    if boleh_dikelola(request, pengguna):
        email = pengguna.email
        pengguna.delete()
        messages.success(request, f'Akun "{email}" berhasil dihapus.')

    return redirect("smartbako:daftar_pengguna")


# ==================================================
# RIWAYAT PREFERENSI (US-13 / FR-06)
# ==================================================

@admin_required
def riwayat_preferensi(request):
    preferensi_list = (
        Preferensi.objects
        .select_related("pengguna", "kategori")
        .annotate(jumlah_hasil=Max("rekomendasi__jumlah_hasil"))
        .order_by("-tanggal_input")
    )

    form_filter = FilterPreferensiForm(request.GET or None)
    if form_filter.is_valid():
        data = form_filter.cleaned_data
        if data["q"]:
            preferensi_list = preferensi_list.filter(
                Q(pengguna__first_name__icontains=data["q"])
                | Q(pengguna__email__icontains=data["q"])
            )
        if data["kategori"]:
            preferensi_list = preferensi_list.filter(kategori=data["kategori"])
        if data["tanggal_awal"]:
            preferensi_list = preferensi_list.filter(
                tanggal_input__date__gte=data["tanggal_awal"]
            )
        if data["tanggal_akhir"]:
            preferensi_list = preferensi_list.filter(
                tanggal_input__date__lte=data["tanggal_akhir"]
            )

    # "Paling sering dicari": kombinasi kategori + ukuran + satuan terbanyak.
    paling_dicari = (
        Preferensi.objects
        .filter(kategori__isnull=False)
        .values("kategori__nama", "ukuran", "satuan")
        .annotate(jumlah=Count("id"))
        .order_by("-jumlah")[:3]
    )

    context = {
        "page_obj": paginasi(request, preferensi_list),
        "total_preferensi": Preferensi.objects.count(),
        "form_filter": form_filter,
        "ada_filter": bool(request.GET.dict().keys() - {"page"}),
        "paling_dicari": paling_dicari,
    }
    return render(
        request,
        "smartbako/panel_admin/riwayat_preferensi/daftar.html",
        context,
    )


@admin_required
def detail_preferensi(request, id):
    preferensi = get_object_or_404(
        Preferensi.objects.select_related("pengguna", "kategori"),
        pk=id,
    )
    rekomendasi = preferensi.rekomendasi.first()
    hasil = (
        rekomendasi.detail.select_related("produk", "produk__kategori")
        if rekomendasi
        else []
    )

    context = {
        "preferensi": preferensi,
        "rekomendasi": rekomendasi,
        "hasil": hasil,
    }
    return render(
        request,
        "smartbako/panel_admin/riwayat_preferensi/detail.html",
        context,
    )


# ==================================================
# LOGOUT ADMIN
# ==================================================

@require_POST
def logout_admin(request):
    logout(request)
    messages.success(request, "Kamu berhasil keluar dari panel admin.")
    return redirect("smartbako:login")