
from decimal import Decimal, InvalidOperation
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test

from .models import Kategori, Produk


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
    return render(request, 'smartbako/panel_pengguna/dashboard.html')


# ==========================================
# DASHBOARD ADMIN
# ==========================================

@admin_required
def dashboard_admin(request):
    context = {
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

@admin_required
def daftar_kategori(request):
    kategori = Kategori.objects.all()

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

        if not nama:
            messages.error(request, 'Nama kategori wajib diisi.')

        elif Kategori.objects.filter(nama__iexact=nama).exists():
            messages.error(request, 'Nama kategori sudah tersedia.')

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
        'kategori': kategori
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

    return redirect('daftar_kategori')


# ==========================================
# KELOLA PRODUK
# ==========================================

@admin_required
def daftar_produk(request):
    produk = Produk.objects.select_related('kategori').all()

    context = {
        'produk': produk,
        'total_produk': produk.count(),
    }

    return render(
        request,
        'smartbako/panel_admin/kelola_produk/daftar.html',
        context
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
            messages.success(
                request,
                'Akun pengguna berhasil dihapus.'
            )

    return redirect('daftar_pengguna')


@admin_required
def logout_admin(request):
    if request.method == 'POST':
        logout(request)
        return redirect('/admin/login/')

    return redirect('dashboard_admin')
