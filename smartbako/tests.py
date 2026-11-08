"""
Pengujian dasar SmartBako.

Jalankan dengan:  python manage.py test smartbako
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Kategori, Preferensi, Produk, Rekomendasi
from .services.preprocessing import preprocessing_teks
from .services.recommendation import hitung_rekomendasi, simpan_rekomendasi

User = get_user_model()
PASSWORD = "SandiAman#2026"


class DataUjiMixin:
    """Membuat data kategori, produk, pengguna, dan admin untuk pengujian."""

    @classmethod
    def setUpTestData(cls):
        cls.kategori_beras = Kategori.objects.create(nama="Beras")
        cls.kategori_minyak = Kategori.objects.create(nama="Minyak")

        cls.beras = Produk.objects.create(
            nama="Beras Pandan Wangi",
            kategori=cls.kategori_beras,
            merek="Topi Koki",
            harga=Decimal("75000"),
            ukuran=Decimal("5"),
            satuan="kg",
            stok=10,
        )
        cls.minyak = Produk.objects.create(
            nama="Minyak Goreng",
            kategori=cls.kategori_minyak,
            merek="Sania",
            harga=Decimal("38000"),
            ukuran=Decimal("2"),
            satuan="liter",
            stok=5,
        )
        cls.stok_habis = Produk.objects.create(
            nama="Beras Murah",
            kategori=cls.kategori_beras,
            harga=Decimal("50000"),
            stok=0,
        )

        cls.pengguna = User.objects.create_user(
            username="budi",
            email="budi@contoh.com",
            password=PASSWORD,
        )
        cls.admin = User.objects.create_user(
            username="admin",
            email="admin@contoh.com",
            password=PASSWORD,
            is_staff=True,
        )


class PreprocessingTests(TestCase):

    def test_teks_dibersihkan_dan_stopword_dihapus(self):
        hasil = preprocessing_teks("Saya ingin Beras 2,5 kg yang PULEN!")
        self.assertEqual(hasil, "beras 2.5 kg pulen")

    def test_teks_kosong(self):
        self.assertEqual(preprocessing_teks(None), "")


class RekomendasiTests(DataUjiMixin, TestCase):

    def test_produk_paling_mirip_menjadi_peringkat_pertama(self):
        preferensi = Preferensi(
            pengguna=self.pengguna,
            kategori=self.kategori_beras,
            budget_max=Decimal("100000"),
            ukuran=Decimal("5"),
            satuan="kg",
        )
        hasil = hitung_rekomendasi(preferensi, Produk.objects.all())

        self.assertEqual(hasil[0][0], self.beras)
        self.assertNotIn(self.stok_habis, [produk for produk, _ in hasil])

    def test_hanya_anggaran_tetap_menghasilkan_rekomendasi(self):
        preferensi = Preferensi(
            pengguna=self.pengguna,
            budget_max=Decimal("40000"),
        )
        hasil = hitung_rekomendasi(preferensi, Produk.objects.all())

        self.assertEqual([produk for produk, _ in hasil], [self.minyak])

    def test_simpan_rekomendasi_membuat_detail(self):
        preferensi = Preferensi.objects.create(
            pengguna=self.pengguna,
            budget_max=Decimal("100000"),
        )
        rekomendasi = simpan_rekomendasi(preferensi)

        self.assertEqual(rekomendasi.jumlah_hasil, 2)
        self.assertEqual(rekomendasi.detail.count(), 2)


class AutentikasiTests(DataUjiMixin, TestCase):

    def login(self, email, password=PASSWORD):
        return self.client.post(
            reverse("smartbako:login"),
            {"email": email, "password": password},
        )

    def test_login_dengan_email(self):
        respons = self.login("BUDI@contoh.com")
        self.assertRedirects(respons, reverse("smartbako:beranda"))

    def test_login_dengan_username_ditolak(self):
        respons = self.login("budi")
        self.assertEqual(respons.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_kata_sandi_salah_ditolak(self):
        respons = self.login("budi@contoh.com", "salah")
        self.assertEqual(respons.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_diarahkan_ke_dashboard_admin(self):
        respons = self.login("admin@contoh.com")
        self.assertRedirects(respons, reverse("smartbako:dashboard_admin"))

    def test_registrasi_tanpa_username(self):
        data = {
            "first_name": "Budi Lain",
            "email": "budi@gmail.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        respons = self.client.post(reverse("smartbako:registrasi"), data)
        self.assertRedirects(respons, reverse("smartbako:login"))

        akun = User.objects.get(email="budi@gmail.com")
        # Username "budi" sudah dipakai, jadi dibuat "budi1" otomatis.
        self.assertEqual(akun.username, "budi1")
        self.assertFalse(akun.is_staff)

        # Akun baru langsung bisa login dengan email.
        respons = self.login("budi@gmail.com")
        self.assertRedirects(respons, reverse("smartbako:beranda"))

    def test_registrasi_email_ganda_ditolak(self):
        self.client.post(reverse("smartbako:registrasi"), {
            "first_name": "Palsu",
            "email": "Budi@Contoh.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        })
        self.assertEqual(User.objects.filter(email__iexact="budi@contoh.com").count(), 1)


class HakAksesTests(DataUjiMixin, TestCase):

    def test_tamu_tidak_bisa_membuka_dashboard_admin(self):
        respons = self.client.get(reverse("smartbako:dashboard_admin"))
        self.assertEqual(respons.status_code, 302)
        self.assertIn(reverse("smartbako:login"), respons.url)

    def test_pengguna_biasa_tidak_bisa_membuka_panel_admin(self):
        self.client.force_login(self.pengguna)
        respons = self.client.get(reverse("smartbako:daftar_produk"))
        self.assertRedirects(respons, reverse("smartbako:beranda"))

    def test_halaman_admin_dapat_dibuka_admin(self):
        preferensi = Preferensi.objects.create(
            pengguna=self.pengguna,
            kategori=self.kategori_beras,
            budget_max=Decimal("100000"),
        )
        simpan_rekomendasi(preferensi)

        self.client.force_login(self.admin)
        halaman = [
            ("dashboard_admin", []),
            ("daftar_kategori", []),
            ("tambah_kategori", []),
            ("edit_kategori", [self.kategori_beras.pk]),
            ("daftar_produk", []),
            ("tambah_produk", []),
            ("detail_produk_admin", [self.beras.pk]),
            ("edit_produk", [self.beras.pk]),
            ("daftar_pengguna", []),
            ("detail_pengguna", [self.pengguna.pk]),
            ("riwayat_preferensi", []),
            ("detail_preferensi", [preferensi.pk]),
        ]
        for nama, args in halaman:
            with self.subTest(nama=nama):
                respons = self.client.get(reverse(f"smartbako:{nama}", args=args))
                self.assertEqual(respons.status_code, 200)

    def test_filter_admin_dengan_nilai_aneh_tidak_error(self):
        self.client.force_login(self.admin)
        cek = [
            ("daftar_produk", {"kategori": "abc", "stok": "x", "page": "999"}),
            ("daftar_pengguna", {"status": "x", "peran": "x"}),
            ("riwayat_preferensi", {"tanggal_awal": "bukan-tanggal", "kategori": "abc"}),
        ]
        for nama, parameter in cek:
            with self.subTest(nama=nama):
                respons = self.client.get(reverse(f"smartbako:{nama}"), parameter)
                self.assertEqual(respons.status_code, 200)

    def test_tambah_produk_lengkap(self):
        self.client.force_login(self.admin)
        respons = self.client.post(reverse("smartbako:tambah_produk"), {
            "nama": "Gula Pasir 1 kg",
            "kategori": self.kategori_beras.pk,
            "merek": "Gulaku",
            "harga": "17000",
            "ukuran": "1",
            "satuan": "KG",
            "stok": "8",
            "deskripsi": "",
        })
        self.assertRedirects(respons, reverse("smartbako:daftar_produk"))
        produk = Produk.objects.get(nama="Gula Pasir 1 kg")
        self.assertEqual(produk.satuan, "kg")

    def test_tambah_produk_tanpa_merek_ditolak(self):
        self.client.force_login(self.admin)
        respons = self.client.post(reverse("smartbako:tambah_produk"), {
            "nama": "Produk Tanpa Merek",
            "kategori": self.kategori_beras.pk,
            "harga": "-5",
            "stok": "1",
        })
        self.assertEqual(respons.status_code, 200)
        form = respons.context["form"]
        self.assertIn("merek", form.errors)
        self.assertIn("harga", form.errors)
        self.assertFalse(Produk.objects.filter(nama="Produk Tanpa Merek").exists())

    def test_admin_tidak_bisa_menonaktifkan_diri_sendiri(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("smartbako:ubah_status_pengguna", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_akun_nonaktif_tidak_bisa_login(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("smartbako:ubah_status_pengguna", args=[self.pengguna.pk]))
        self.client.logout()

        respons = self.client.post(
            reverse("smartbako:login"),
            {"email": "budi@contoh.com", "password": PASSWORD},
        )
        self.assertEqual(respons.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_ubah_status_menolak_alamat_kembali_luar(self):
        self.client.force_login(self.admin)
        respons = self.client.post(
            reverse("smartbako:ubah_status_pengguna", args=[self.pengguna.pk]),
            {"kembali": "https://situs-jahat.com/"},
        )
        self.assertRedirects(respons, reverse("smartbako:daftar_pengguna"))

    def test_kategori_yang_dipakai_produk_tidak_terhapus(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("smartbako:hapus_kategori", args=[self.kategori_beras.pk])
        )
        self.assertTrue(Kategori.objects.filter(pk=self.kategori_beras.pk).exists())


class HalamanPenggunaTests(DataUjiMixin, TestCase):

    def setUp(self):
        self.client.force_login(self.pengguna)

    def test_membuka_hasil_rekomendasi_tidak_menambah_riwayat(self):
        respons = self.client.post(reverse("smartbako:atur_preferensi"), {
            "budget_max": "100000",
        })
        preferensi = Preferensi.objects.get(pengguna=self.pengguna)
        self.assertRedirects(
            respons,
            reverse("smartbako:rekomendasi", args=[preferensi.pk]),
        )

        self.client.get(reverse("smartbako:rekomendasi", args=[preferensi.pk]))
        self.client.get(reverse("smartbako:rekomendasi", args=[preferensi.pk]))
        self.assertEqual(Rekomendasi.objects.count(), 1)

    def test_bandingkan_mengabaikan_id_tidak_valid(self):
        respons = self.client.get(
            reverse("smartbako:bandingkan_produk"),
            {"produk": [self.beras.pk, "abc", self.minyak.pk]},
        )
        self.assertEqual(respons.status_code, 200)
        self.assertEqual(len(respons.context["produk_dipilih"]), 2)

    def test_halaman_pengguna_dapat_dibuka(self):
        for nama in ["beranda", "katalog", "riwayat", "profil", "ubah_password"]:
            with self.subTest(nama=nama):
                respons = self.client.get(reverse(f"smartbako:{nama}"))
                self.assertEqual(respons.status_code, 200)