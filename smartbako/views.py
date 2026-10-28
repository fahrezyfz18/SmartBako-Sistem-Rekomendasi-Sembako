from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Kategori, Produk
from .forms import CustomUserCreationForm

# --- HALAMAN PUBLIK ---
def landing_page(request):
    return render(request, "smartbako/landing_page/beranda.html")

def fitur_view(request):
    return render(request, "smartbako/landing_page/fitur.html")

def produk_publik_view(request):
    produk_list = Produk.objects.all()
    return render(request, "smartbako/landing_page/produk.html", {"produk_list": produk_list})

def tentang_kami_view(request):
    return render(request, "smartbako/landing_page/tentang_kami.html")

def login_view(request):
    """Menangani proses otentikasi / masuk pengguna (Hanya via Email)"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('smartbako:admin_dashboard')
        return redirect('smartbako:beranda')

    if request.method == 'POST':
        email_input = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        
        user = None
        if email_input:
            try:
                from django.contrib.auth.models import User
                matched_user = User.objects.get(email=email_input)
                user = authenticate(request, username=matched_user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, "Berhasil masuk ke akun Anda.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('smartbako:beranda')
        else:
            messages.error(request, "Email atau password salah.")

    return render(request, "smartbako/auth/login.html")

def registrasi_view(request):
    """Menangani pendaftaran akun baru menggunakan CustomUserCreationForm"""
    if request.user.is_authenticated:
        return redirect('smartbako:beranda')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Akun berhasil dibuat! Silakan masuk.")
            return redirect('smartbako:login')
        else:
            messages.error(request, "Terjadi kesalahan pada data registrasi Anda. Silakan periksa kembali.")
    else:
        form = CustomUserCreationForm()

    return render(request, "smartbako/auth/register.html", {"form": form})

def logout_view(request):
    """Menangani proses keluar akun"""
    logout(request)
    messages.info(request, "Anda telah keluar dari sistem.")
    return redirect('smartbako:landing_page')

def lupa_password_view(request):
    """Menangani halaman pemulihan password"""
    return render(request, "smartbako/auth/lupa_password.html")


# --- HALAMAN PENGGUNA ---
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
    return render(request, "smartbako/panel_pengguna/detail_produk.html", {"produk": produk})

def rekomendasi(request):
    return render(request, "smartbako/panel_pengguna/rekomendasi.html")


# --- HALAMAN ADMIN KUSTOM ---
def admin_dashboard(request):
    return render(request, "smartbako/panel_admin/dashboard.html")

def admin_kelola_produk(request):
    produk_list = Produk.objects.all()
    return render(request, "smartbako/panel_admin/kelola_produk/daftar.html", {"produk_list": produk_list})