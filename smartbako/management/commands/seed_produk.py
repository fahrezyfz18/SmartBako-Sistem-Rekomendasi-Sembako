"""
Mengisi database dengan data dummy kategori dan produk sembako.

Pemakaian:
    python manage.py seed_produk           # tambah data dummy
    python manage.py seed_produk --reset   # hapus produk dulu, lalu isi ulang
    python manage.py seed_produk --tanpa-gambar   # tanpa membuat gambar dummy

Catatan:
- Data bersifat dummy untuk pengembangan dan pengujian rekomendasi.
  Harga hanya perkiraan dan tidak mencerminkan harga pasar sebenarnya.
- Perintah aman dijalankan berulang kali: produk dengan nama, merek,
  ukuran, dan satuan yang sama tidak akan dibuat dua kali.
- Produk yang belum punya gambar akan dibuatkan gambar ilustrasi
  sederhana (bukan foto asli) dan disimpan di media/produk/.
  Gambar asli dapat diganti kapan saja lewat panel admin.
"""

import io
import random
import textwrap
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import ProtectedError
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from smartbako.models import Kategori, Produk

# Seed tetap agar stok yang dihasilkan selalu sama setiap dijalankan.
SEED_ACAK = 2026

KATEGORI = {
    "Beras": "Beras putih, pulen, dan medium untuk kebutuhan makan sehari-hari.",
    "Minyak Goreng": "Minyak goreng sawit kemasan pouch dan botol.",
    "Gula": "Gula pasir putih dan gula merah untuk masak dan minuman.",
    "Telur": "Telur ayam ras dan telur bebek segar.",
    "Tepung": "Tepung terigu, tepung beras, dan tepung tapioka.",
    "Mi Instan": "Mi instan goreng dan berkuah berbagai rasa.",
    "Garam": "Garam dapur beryodium untuk memasak.",
    "Kecap dan Bumbu": "Kecap, saus, dan bumbu dapur siap pakai.",
    "Susu": "Susu kental manis, susu bubuk, dan susu UHT.",
    "Kopi dan Teh": "Kopi bubuk, kopi sachet, dan teh celup.",
}

# Format: (kategori, nama, merek, deskripsi, [(ukuran, satuan, harga), ...])
# Setiap varian ukuran menjadi satu produk tersendiri.
DATA_PRODUK = [
    # ---------------- BERAS ----------------
    ("Beras", "Beras Pandan Wangi", "Topi Koki",
     "Beras pulen dengan aroma pandan alami, cocok untuk nasi sehari-hari.",
     [(5, "kg", 82000), (10, "kg", 160000), (25, "kg", 395000)]),
    ("Beras", "Beras Premium Setra Ramos", "Sania",
     "Beras premium bulir panjang, pulen, dan bersih dari kotoran.",
     [(5, "kg", 76000), (10, "kg", 149000)]),
    ("Beras", "Beras Medium", "Bulog",
     "Beras medium harga terjangkau untuk kebutuhan keluarga.",
     [(5, "kg", 62000), (10, "kg", 122000)]),
    ("Beras", "Beras Rojolele", "Raja",
     "Beras rojolele asli, pulen dan wangi, khas Delanggu.",
     [(5, "kg", 85000), (10, "kg", 168000)]),
    ("Beras", "Beras Merah Organik", "Lingkar Organik",
     "Beras merah organik tinggi serat, cocok untuk menu diet sehat.",
     [(1, "kg", 32000), (2, "kg", 62000)]),
    ("Beras", "Beras Ketan Putih", "Rose Brand",
     "Beras ketan putih untuk membuat lemper, tape, dan kue tradisional.",
     [(1, "kg", 24000)]),
    ("Beras", "Beras Pulen Wangi", "Ayam Jago",
     "Beras pulen dengan butiran utuh, cocok untuk nasi uduk dan nasi goreng.",
     [(5, "kg", 74000), (10, "kg", 145000)]),
    ("Beras", "Beras Cianjur", "Fortune",
     "Beras cianjur pulen, lembut, dan tidak cepat basi.",
     [(5, "kg", 79000)]),

    # ------------- MINYAK GORENG -------------
    ("Minyak Goreng", "Minyak Goreng Sawit", "Bimoli",
     "Minyak goreng sawit jernih, dua kali penyaringan, tidak mudah berbusa.",
     [(1, "liter", 21000), (2, "liter", 41000), (5, "liter", 99000)]),
    ("Minyak Goreng", "Minyak Goreng Sawit", "Sania",
     "Minyak goreng sawit kaya vitamin A dan E untuk menggoreng sehari-hari.",
     [(1, "liter", 19500), (2, "liter", 38000)]),
    ("Minyak Goreng", "Minyak Goreng Sawit", "Filma",
     "Minyak goreng sawit premium, hasil gorengan renyah dan tidak berminyak.",
     [(1, "liter", 20500), (2, "liter", 40000)]),
    ("Minyak Goreng", "Minyak Goreng Sawit", "Tropical",
     "Minyak goreng dengan teknologi penyaringan ganda, bening dan sehat.",
     [(1, "liter", 20000), (2, "liter", 39000)]),
    ("Minyak Goreng", "Minyak Goreng Sawit", "Fortune",
     "Minyak goreng sawit ekonomis untuk kebutuhan rumah tangga dan usaha.",
     [(1, "liter", 18500), (2, "liter", 36000), (5, "liter", 88000)]),
    ("Minyak Goreng", "Minyak Goreng Rakyat", "Minyakita",
     "Minyak goreng kemasan sederhana dengan harga terjangkau.",
     [(1, "liter", 15700)]),
    ("Minyak Goreng", "Minyak Kelapa Murni", "Barco",
     "Minyak kelapa untuk menumis dan menggoreng dengan aroma khas kelapa.",
     [(0.5, "liter", 17000), (1, "liter", 32000)]),

    # ----------------- GULA -----------------
    ("Gula", "Gula Pasir Putih", "Gulaku",
     "Gula pasir putih kristal, bersih dan cepat larut.",
     [(0.5, "kg", 9500), (1, "kg", 18000), (2, "kg", 35000)]),
    ("Gula", "Gula Pasir", "Rose Brand",
     "Gula pasir kemasan praktis untuk minuman dan kue.",
     [(1, "kg", 17500)]),
    ("Gula", "Gula Pasir Premium", "Gula Pasir Rajawali",
     "Gula pasir premium dari tebu pilihan.",
     [(1, "kg", 17000)]),
    ("Gula", "Gula Merah Aren", "Javara",
     "Gula aren asli, cocok untuk kolak, cendol, dan sambal.",
     [(0.5, "kg", 22000), (1, "kg", 42000)]),
    ("Gula", "Gula Batu", "Rose Brand",
     "Gula batu kristal untuk teh dan minuman tradisional.",
     [(0.5, "kg", 15000)]),
    ("Gula", "Gula Halus", "Claris",
     "Gula halus untuk taburan kue dan adonan.",
     [(0.25, "kg", 9000), (0.5, "kg", 16500)]),

    # ----------------- TELUR -----------------
    ("Telur", "Telur Ayam Negeri", "Peternak Lokal",
     "Telur ayam ras segar, cangkang bersih, ukuran sedang.",
     [(10, "butir", 25000), (30, "butir", 72000)]),
    ("Telur", "Telur Ayam Negeri", "Japfa",
     "Telur ayam ras pilihan dengan kualitas terjaga.",
     [(10, "butir", 27000)]),
    ("Telur", "Telur Ayam Omega-3", "Super Egg",
     "Telur ayam dengan kandungan omega-3 lebih tinggi.",
     [(10, "butir", 36000)]),
    ("Telur", "Telur Ayam Kampung", "Peternak Lokal",
     "Telur ayam kampung segar, kuning telur lebih pekat.",
     [(10, "butir", 30000)]),
    ("Telur", "Telur Bebek", "Peternak Lokal",
     "Telur bebek segar untuk martabak dan telur asin.",
     [(10, "butir", 32000)]),
    ("Telur", "Telur Puyuh", "Peternak Lokal",
     "Telur puyuh segar untuk sayur dan sate.",
     [(25, "butir", 15000)]),

    # ----------------- TEPUNG -----------------
    ("Tepung", "Tepung Terigu Protein Sedang", "Segitiga Biru",
     "Tepung terigu serbaguna untuk gorengan, kue, dan mi.",
     [(0.5, "kg", 7000), (1, "kg", 13500)]),
    ("Tepung", "Tepung Terigu Protein Tinggi", "Cakra Kembar",
     "Tepung terigu protein tinggi untuk roti dan mi.",
     [(1, "kg", 14500)]),
    ("Tepung", "Tepung Terigu Protein Rendah", "Kunci Biru",
     "Tepung terigu protein rendah untuk kue kering dan bolu.",
     [(1, "kg", 14000)]),
    ("Tepung", "Tepung Beras", "Rose Brand",
     "Tepung beras putih untuk kue tradisional dan adonan gorengan.",
     [(0.5, "kg", 8500)]),
    ("Tepung", "Tepung Tapioka", "Rose Brand",
     "Tepung tapioka untuk cireng, pempek, dan pengental masakan.",
     [(0.5, "kg", 8000)]),
    ("Tepung", "Tepung Maizena", "Maizenaku",
     "Tepung jagung untuk pengental sup dan bahan kue.",
     [(0.1, "kg", 4500), (0.3, "kg", 11000)]),
    ("Tepung", "Tepung Bumbu Serbaguna", "Sasa",
     "Tepung bumbu siap pakai untuk ayam goreng renyah.",
     [(0.075, "kg", 3000), (0.21, "kg", 8000)]),
    ("Tepung", "Tepung Ketan Putih", "Rose Brand",
     "Tepung ketan untuk klepon, onde-onde, dan mochi.",
     [(0.5, "kg", 11000)]),

    # ---------------- MI INSTAN ----------------
    ("Mi Instan", "Mi Goreng Original", "Indomie",
     "Mi instan goreng rasa original dengan bumbu kecap dan bawang goreng.",
     [(1, "pcs", 3500), (5, "pcs", 16500), (40, "pcs", 125000)]),
    ("Mi Instan", "Mi Kuah Rasa Ayam Bawang", "Indomie",
     "Mi instan berkuah rasa ayam bawang yang gurih.",
     [(1, "pcs", 3200), (5, "pcs", 15500)]),
    ("Mi Instan", "Mi Kuah Rasa Soto", "Indomie",
     "Mi instan berkuah rasa soto dengan koya gurih.",
     [(1, "pcs", 3200), (5, "pcs", 15500)]),
    ("Mi Instan", "Mi Goreng", "Mie Sedaap",
     "Mi instan goreng dengan kriuk renyah.",
     [(1, "pcs", 3400), (5, "pcs", 16000)]),
    ("Mi Instan", "Mi Kuah Rasa Kari Ayam", "Mie Sedaap",
     "Mi instan berkuah kari ayam dengan aroma rempah.",
     [(1, "pcs", 3200)]),
    ("Mi Instan", "Mi Goreng Rasa Ayam Pedas", "Supermi",
     "Mi instan goreng rasa ayam pedas.",
     [(1, "pcs", 3100)]),
    ("Mi Instan", "Mi Kuah Rasa Baso Sapi", "Sarimi",
     "Mi instan berkuah rasa baso sapi, porsi isi dua.",
     [(1, "pcs", 3300)]),
    ("Mi Instan", "Mi Telur Kering", "Burung Dara",
     "Mi telur kering untuk mi goreng dan mi rebus rumahan.",
     [(0.2, "kg", 7500)]),
    ("Mi Instan", "Bihun Jagung", "Padamu",
     "Bihun jagung untuk bihun goreng dan isian sup.",
     [(0.175, "kg", 6000)]),

    # ----------------- GARAM -----------------
    ("Garam", "Garam Dapur Beryodium", "Refina",
     "Garam halus beryodium untuk memasak sehari-hari.",
     [(0.25, "kg", 4000), (0.5, "kg", 7000)]),
    ("Garam", "Garam Meja Halus", "Cap Kapal",
     "Garam meja halus beryodium dalam kemasan praktis.",
     [(0.25, "kg", 3000), (0.5, "kg", 5500)]),
    ("Garam", "Garam Kasar", "Cap Kapal",
     "Garam kasar untuk mengasinkan ikan dan telur.",
     [(1, "kg", 6000)]),
    ("Garam", "Garam Himalaya", "Lingkar Organik",
     "Garam batu himalaya merah muda dengan mineral alami.",
     [(0.25, "kg", 25000)]),

    # ------------- KECAP DAN BUMBU -------------
    ("Kecap dan Bumbu", "Kecap Manis", "Bango",
     "Kecap manis dari kedelai hitam pilihan, kental dan legit.",
     [(0.22, "liter", 11000), (0.55, "liter", 25000)]),
    ("Kecap dan Bumbu", "Kecap Manis", "ABC",
     "Kecap manis kental untuk semur dan nasi goreng.",
     [(0.135, "liter", 6000), (0.52, "liter", 21000)]),
    ("Kecap dan Bumbu", "Kecap Asin", "ABC",
     "Kecap asin untuk tumisan dan masakan oriental.",
     [(0.133, "liter", 7000)]),
    ("Kecap dan Bumbu", "Saus Sambal", "ABC",
     "Saus sambal pedas untuk pendamping gorengan dan bakso.",
     [(0.335, "kg", 12000)]),
    ("Kecap dan Bumbu", "Saus Tomat", "Del Monte",
     "Saus tomat kental untuk spageti dan nasi goreng.",
     [(0.34, "kg", 13000)]),
    ("Kecap dan Bumbu", "Penyedap Rasa Sapi", "Royco",
     "Bumbu penyedap rasa sapi untuk sup dan tumisan.",
     [(0.1, "kg", 6000), (0.23, "kg", 12500)]),
    ("Kecap dan Bumbu", "Kaldu Ayam Bubuk", "Masako",
     "Kaldu ayam bubuk untuk menambah rasa gurih masakan.",
     [(0.1, "kg", 5500), (0.25, "kg", 12000)]),
    ("Kecap dan Bumbu", "Bumbu Nasi Goreng", "Bamboe",
     "Bumbu nasi goreng instan siap tumis.",
     [(0.025, "kg", 4500)]),
    ("Kecap dan Bumbu", "Bumbu Rendang", "Bamboe",
     "Bumbu rendang instan dengan rempah lengkap.",
     [(0.036, "kg", 6000)]),
    ("Kecap dan Bumbu", "Santan Kelapa Cair", "Kara",
     "Santan kelapa cair siap pakai untuk gulai dan kolak.",
     [(0.065, "liter", 3500), (0.2, "liter", 9000)]),
    ("Kecap dan Bumbu", "Terasi Udang", "ABC",
     "Terasi udang untuk sambal terasi dan tumisan.",
     [(0.004, "kg", 1000)]),
    ("Kecap dan Bumbu", "Merica Bubuk", "Ladaku",
     "Lada putih bubuk dengan aroma pedas hangat.",
     [(0.015, "kg", 3000)]),

    # ----------------- SUSU -----------------
    ("Susu", "Susu Kental Manis", "Frisian Flag",
     "Susu kental manis untuk minuman, roti, dan kue.",
     [(0.37, "kg", 13500)]),
    ("Susu", "Susu Kental Manis Cokelat", "Indomilk",
     "Susu kental manis rasa cokelat.",
     [(0.37, "kg", 12500)]),
    ("Susu", "Susu Kental Manis Sachet", "Carnation",
     "Susu kental manis sachet praktis sekali pakai.",
     [(0.04, "kg", 2000)]),
    ("Susu", "Susu UHT Full Cream", "Ultra Milk",
     "Susu cair UHT full cream siap minum.",
     [(0.25, "liter", 6500), (1, "liter", 19500)]),
    ("Susu", "Susu UHT Cokelat", "Indomilk",
     "Susu cair UHT rasa cokelat.",
     [(0.19, "liter", 4500)]),
    ("Susu", "Susu Bubuk Full Cream", "Dancow",
     "Susu bubuk full cream untuk keluarga.",
     [(0.4, "kg", 58000), (0.8, "kg", 112000)]),

    # -------------- KOPI DAN TEH --------------
    ("Kopi dan Teh", "Kopi Bubuk Robusta", "Kapal Api",
     "Kopi bubuk robusta dengan aroma kuat.",
     [(0.065, "kg", 7500), (0.165, "kg", 17000)]),
    ("Kopi dan Teh", "Kopi Bubuk Tubruk", "ABC",
     "Kopi bubuk tubruk tradisional.",
     [(0.065, "kg", 6500)]),
    ("Kopi dan Teh", "Kopi Susu Sachet", "Good Day",
     "Kopi instan tiga-dalam-satu rasa mocacinno.",
     [(10, "sachet", 15000)]),
    ("Kopi dan Teh", "Kopi Hitam Sachet", "Torabika",
     "Kopi hitam instan dengan gula.",
     [(10, "sachet", 13000)]),
    ("Kopi dan Teh", "Teh Celup Melati", "Sariwangi",
     "Teh celup aroma melati, praktis diseduh.",
     [(25, "pcs", 7500)]),
    ("Kopi dan Teh", "Teh Tubruk Melati", "Teh Gopek",
     "Teh tubruk wangi melati khas Jawa.",
     [(0.04, "kg", 3500)]),
    ("Kopi dan Teh", "Teh Celup Hijau", "Sosro",
     "Teh hijau celup tanpa gula.",
     [(25, "pcs", 11000)]),

    # ---------- TAMBAHAN AGAR DATASET >= 200 PRODUK ----------
    ("Beras", "Beras Super Slyp", "Cap Bunga",
     "Beras super slyp putih bersih, nasi pulen dan tidak lembek.",
     [(5, "kg", 72000), (10, "kg", 141000), (20, "kg", 278000)]),
    ("Beras", "Beras Pera", "Cap Jempol",
     "Beras pera dengan tekstur nasi tidak lengket, cocok untuk nasi goreng.",
     [(5, "kg", 68000), (10, "kg", 133000)]),
    ("Beras", "Beras Hitam Organik", "Lingkar Organik",
     "Beras hitam organik kaya antioksidan untuk menu sehat.",
     [(1, "kg", 38000)]),
    ("Beras", "Beras Basmati", "Sania",
     "Beras basmati bulir panjang untuk nasi kebuli dan biryani.",
     [(1, "kg", 45000), (5, "kg", 215000)]),
    ("Beras", "Beras Shirataki", "Konjac Nusantara",
     "Beras shirataki rendah kalori dari umbi porang.",
     [(0.5, "kg", 39000)]),
    ("Minyak Goreng", "Minyak Goreng Sawit", "Sunco",
     "Minyak goreng sawit jernih dan tidak mudah keruh.",
     [(1, "liter", 20500), (2, "liter", 40000)]),
    ("Minyak Goreng", "Minyak Goreng Sawit", "Kunci Mas",
     "Minyak goreng sawit ekonomis untuk menggoreng dan menumis.",
     [(1, "liter", 18000), (2, "liter", 35000)]),
    ("Minyak Goreng", "Minyak Goreng Sawit", "Hemart",
     "Minyak goreng sawit kemasan pouch hemat.",
     [(1, "liter", 17500), (2, "liter", 34000)]),
    ("Minyak Goreng", "Minyak Jagung", "Mazola",
     "Minyak jagung rendah lemak jenuh untuk masakan sehat.",
     [(0.45, "liter", 32000), (1, "liter", 65000)]),
    ("Minyak Goreng", "Minyak Zaitun Extra Virgin", "Borges",
     "Minyak zaitun extra virgin untuk salad dan tumisan ringan.",
     [(0.25, "liter", 55000)]),
    ("Minyak Goreng", "Margarin Serbaguna", "Blue Band",
     "Margarin serbaguna untuk menumis, kue, dan olesan roti.",
     [(0.2, "kg", 9500), (1, "kg", 42000)]),
    ("Gula", "Gula Pasir Kuning", "Gulaku",
     "Gula pasir kuning dengan rasa manis khas tebu.",
     [(1, "kg", 17500)]),
    ("Gula", "Gula Kelapa Cetak", "Javara",
     "Gula kelapa cetak untuk masakan Jawa dan minuman.",
     [(0.5, "kg", 18000)]),
    ("Gula", "Gula Rendah Kalori", "Tropicana Slim",
     "Pemanis rendah kalori untuk minuman, praktis dalam sachet.",
     [(50, "sachet", 32000)]),
    ("Gula", "Gula Pasir Kemasan Ekonomis", "Gula Pasir Lokal",
     "Gula pasir curah kemasan plastik dengan harga ekonomis.",
     [(1, "kg", 16000), (5, "kg", 78000)]),
    ("Telur", "Telur Ayam Negeri", "Telur Sehat",
     "Telur ayam ras ukuran besar, cocok untuk kebutuhan dapur.",
     [(15, "butir", 37000), (30, "butir", 71000)]),
    ("Telur", "Telur Asin Brebes", "Peternak Lokal",
     "Telur bebek asin khas Brebes, siap santap.",
     [(5, "butir", 22000)]),
    ("Telur", "Telur Ayam Organik", "Telur Sehat",
     "Telur ayam dari peternakan organik tanpa antibiotik.",
     [(10, "butir", 42000)]),
    ("Telur", "Telur Ayam Arab", "Peternak Lokal",
     "Telur ayam arab berukuran kecil dengan kuning telur besar.",
     [(10, "butir", 28000)]),
    ("Tepung", "Tepung Terigu Serbaguna", "Lencana Merah",
     "Tepung terigu serbaguna harga terjangkau.",
     [(1, "kg", 12000)]),
    ("Tepung", "Tepung Roti", "Kobe",
     "Tepung roti panir untuk lapisan nugget dan udang goreng.",
     [(0.1, "kg", 5000), (0.2, "kg", 9000)]),
    ("Tepung", "Tepung Pisang Goreng", "Sasa",
     "Tepung bumbu khusus pisang goreng renyah.",
     [(0.21, "kg", 8500)]),
    ("Tepung", "Tepung Sagu", "Rose Brand",
     "Tepung sagu untuk kue sagu dan bakso.",
     [(0.5, "kg", 9500)]),
    ("Tepung", "Tepung Hunkwe", "Cap Bola",
     "Tepung kacang hijau untuk kue cantik manis.",
     [(0.15, "kg", 7000)]),
    ("Mi Instan", "Mi Goreng Rendang", "Indomie",
     "Mi instan goreng rasa rendang dengan bumbu rempah.",
     [(1, "pcs", 3500), (5, "pcs", 16500)]),
    ("Mi Instan", "Mi Goreng Aceh", "Indomie",
     "Mi instan goreng rasa mi aceh pedas.",
     [(1, "pcs", 3500)]),
    ("Mi Instan", "Mi Kuah Rasa Kaldu Ayam", "Indomie",
     "Mi instan berkuah rasa kaldu ayam ringan.",
     [(1, "pcs", 3200), (5, "pcs", 15500)]),
    ("Mi Instan", "Mi Goreng Korean Spicy", "Mie Sedaap",
     "Mi instan goreng rasa pedas ala Korea.",
     [(1, "pcs", 4000), (5, "pcs", 19000)]),
    ("Mi Instan", "Mi Kuah Rasa Soto", "Mie Sedaap",
     "Mi instan berkuah rasa soto dengan jeruk nipis.",
     [(1, "pcs", 3200)]),
    ("Mi Instan", "Mi Goreng Rasa Ayam Bawang", "Sarimi",
     "Mi instan goreng rasa ayam bawang isi dua.",
     [(1, "pcs", 3400)]),
    ("Mi Instan", "Mi Kuah Rasa Ayam Spesial", "Supermi",
     "Mi instan berkuah rasa ayam spesial.",
     [(1, "pcs", 3000), (5, "pcs", 14500)]),
    ("Mi Instan", "Mi Gelas Rasa Ayam Bawang", "Mie Gelas",
     "Mi instan porsi kecil dalam kemasan gelas.",
     [(1, "pcs", 1500), (10, "pcs", 14000)]),
    ("Mi Instan", "Bihun Beras", "Cap Tiga Ayam",
     "Bihun beras halus untuk bihun goreng dan soto.",
     [(0.25, "kg", 8500)]),
    ("Mi Instan", "Soun Kacang Hijau", "Cap Tiga Ayam",
     "Soun kacang hijau kenyal untuk sup dan martabak.",
     [(0.1, "kg", 6000)]),
    ("Garam", "Garam Dapur", "Segitiga G",
     "Garam dapur halus beryodium kemasan ekonomis.",
     [(0.25, "kg", 2500), (0.5, "kg", 4500)]),
    ("Garam", "Garam Krosok Bali", "Amed Salt",
     "Garam krosok tradisional dari pesisir Bali.",
     [(0.25, "kg", 18000)]),
    ("Garam", "Garam Diet Rendah Natrium", "Lososa",
     "Garam rendah natrium untuk diet sehat.",
     [(0.2, "kg", 22000)]),
    ("Kecap dan Bumbu", "Kecap Manis", "Sedaap",
     "Kecap manis kental dengan gula kelapa asli.",
     [(0.2, "liter", 8500), (0.52, "liter", 20000)]),
    ("Kecap dan Bumbu", "Kecap Manis Cap Bango Refill", "Bango",
     "Kecap manis kemasan isi ulang yang lebih hemat.",
     [(0.725, "liter", 30000)]),
    ("Kecap dan Bumbu", "Saus Tiram", "Saori",
     "Saus tiram untuk tumisan sayur dan seafood.",
     [(0.133, "liter", 9000)]),
    ("Kecap dan Bumbu", "Saus Sambal Extra Pedas", "Indofood",
     "Saus sambal dengan tingkat kepedasan ekstra.",
     [(0.275, "kg", 11000)]),
    ("Kecap dan Bumbu", "Bumbu Opor Ayam", "Bamboe",
     "Bumbu opor instan dengan santan dan rempah.",
     [(0.036, "kg", 6000)]),
    ("Kecap dan Bumbu", "Bumbu Soto Ayam", "Indofood",
     "Bumbu soto ayam instan untuk soto kuning.",
     [(0.045, "kg", 5000)]),
    ("Kecap dan Bumbu", "Bumbu Rawon", "Bamboe",
     "Bumbu rawon instan dengan kluwek asli.",
     [(0.036, "kg", 6000)]),
    ("Kecap dan Bumbu", "Penyedap Rasa Ayam", "Royco",
     "Bumbu penyedap rasa ayam untuk masakan sehari-hari.",
     [(0.1, "kg", 6000), (0.23, "kg", 12500)]),
    ("Kecap dan Bumbu", "Micin", "Ajinomoto",
     "Penyedap monosodium glutamat untuk menambah rasa gurih.",
     [(0.1, "kg", 7000), (0.25, "kg", 16000)]),
    ("Kecap dan Bumbu", "Santan Kelapa Bubuk", "Sasa",
     "Santan bubuk instan, tinggal larutkan dengan air.",
     [(0.02, "kg", 2500)]),
    ("Kecap dan Bumbu", "Ketumbar Bubuk", "Desaku",
     "Ketumbar bubuk untuk bumbu ungkep dan gulai.",
     [(0.016, "kg", 2500)]),
    ("Kecap dan Bumbu", "Kunyit Bubuk", "Desaku",
     "Kunyit bubuk untuk nasi kuning dan kari.",
     [(0.02, "kg", 2500)]),
    ("Susu", "Susu Kental Manis Putih", "Indomilk",
     "Susu kental manis putih kemasan kaleng.",
     [(0.37, "kg", 12500)]),
    ("Susu", "Susu Kental Manis Pouch", "Frisian Flag",
     "Susu kental manis kemasan pouch, mudah dituang.",
     [(0.28, "kg", 10500), (0.545, "kg", 19500)]),
    ("Susu", "Susu UHT Stroberi", "Ultra Milk",
     "Susu cair UHT rasa stroberi.",
     [(0.2, "liter", 5500)]),
    ("Susu", "Susu UHT Low Fat", "Greenfields",
     "Susu cair UHT rendah lemak.",
     [(1, "liter", 23000)]),
    ("Susu", "Susu Bubuk Instan", "Bendera",
     "Susu bubuk instan untuk anak dan keluarga.",
     [(0.4, "kg", 48000), (0.8, "kg", 92000)]),
    ("Susu", "Susu Kedelai", "Vitasoy",
     "Susu kedelai siap minum tanpa laktosa.",
     [(0.25, "liter", 7000)]),
    ("Susu", "Krimer Kental Manis", "Enaak",
     "Krimer kental manis untuk minuman dan topping.",
     [(0.37, "kg", 10000)]),
    ("Kopi dan Teh", "Kopi Bubuk Arabika Gayo", "Kopi Gayo",
     "Kopi arabika gayo dengan cita rasa asam seimbang.",
     [(0.2, "kg", 45000)]),
    ("Kopi dan Teh", "Kopi Bubuk Special Mix", "Kapal Api",
     "Kopi bubuk dengan gula dalam sachet.",
     [(10, "sachet", 14500)]),
    ("Kopi dan Teh", "Kopi Instan Murni", "Nescafe",
     "Kopi instan murni tanpa gula.",
     [(0.05, "kg", 18000), (0.1, "kg", 34000)]),
    ("Kopi dan Teh", "Kopi Susu Gula Aren Sachet", "Luwak White Koffie",
     "Kopi susu instan dengan gula aren.",
     [(10, "sachet", 16000)]),
    ("Kopi dan Teh", "Teh Celup Original", "Sariwangi",
     "Teh celup hitam rasa original.",
     [(25, "pcs", 7000), (50, "pcs", 13000)]),
    ("Kopi dan Teh", "Teh Celup Melati", "Teh Tong Tji",
     "Teh celup melati dengan aroma harum.",
     [(25, "pcs", 9000)]),
    ("Kopi dan Teh", "Teh Tubruk", "Teh Poci",
     "Teh tubruk wangi untuk diseduh di poci tanah liat.",
     [(0.05, "kg", 5000)]),
    ("Kopi dan Teh", "Teh Hijau Bubuk Matcha", "Hario Tea",
     "Bubuk matcha untuk minuman dan kue.",
     [(0.05, "kg", 35000)]),
]


def normalisasi_ukuran(ukuran, satuan):
    """
    Ukuran di bawah 1 kg/liter diubah ke gram/ml agar mudah dibaca dan
    muat di kolom ukuran (2 angka desimal). Contoh: 0.075 kg -> 75 gram.
    """
    ukuran = Decimal(str(ukuran))

    if satuan == "kg" and ukuran < 1:
        ukuran, satuan = ukuran * 1000, "gram"
    elif satuan == "liter" and ukuran < 1:
        ukuran, satuan = ukuran * 1000, "ml"

    # Disamakan dengan format kolom (2 desimal) agar pencarian data lama cocok.
    return ukuran.quantize(Decimal("0.01")), satuan


def format_ukuran(nilai):
    """Decimal('2.50') -> '2,5' dan Decimal('500.000') -> '500' (untuk nama produk)."""
    teks = f"{Decimal(nilai).normalize():f}"
    return teks.replace(".", ",")


# ==========================================================
# GAMBAR ILUSTRASI DUMMY
# ==========================================================

UKURAN_GAMBAR = 600

# (warna latar, warna aksen) per kategori.
WARNA_KATEGORI = {
    "Beras": ("#F3EBDD", "#8A6A3B"),
    "Minyak Goreng": ("#FBF1C9", "#9A7A12"),
    "Gula": ("#F6F1F1", "#8C5A5A"),
    "Telur": ("#FBE9D7", "#A4602A"),
    "Tepung": ("#EFEDE8", "#6F6658"),
    "Mi Instan": ("#FCE3D6", "#B3471D"),
    "Garam": ("#E5EEF5", "#3F6684"),
    "Kecap dan Bumbu": ("#EBDFD8", "#6B3A2A"),
    "Susu": ("#E8F1FB", "#2F5E91"),
    "Kopi dan Teh": ("#E6EDE2", "#4A6B3A"),
}
WARNA_DEFAULT = ("#F1EFEA", "#5E1C23")
WARNA_TEKS = "#2E2A27"


def muat_font(ukuran, tebal=False):
    """Font Arial (Windows) atau DejaVu (Linux); cadangan: font bawaan Pillow."""
    kandidat = (
        ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if tebal
        else ["arial.ttf", "DejaVuSans.ttf"]
    )
    for nama_font in kandidat:
        try:
            return ImageFont.truetype(nama_font, ukuran)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=ukuran)
    except TypeError:
        # Pillow versi lama belum mendukung parameter size.
        return ImageFont.load_default()


def font_muat(draw, teks, lebar_maks, ukuran_awal, tebal=True, ukuran_min=14):
    """Mengecilkan font sampai teks muat dalam lebar_maks piksel."""
    ukuran = ukuran_awal
    font = muat_font(ukuran, tebal)
    while ukuran > ukuran_min and draw.textlength(teks, font=font) > lebar_maks:
        ukuran -= 2
        font = muat_font(ukuran, tebal)
    return font


def tulis_tengah(draw, y, teks, font, warna):
    """Menulis teks rata tengah secara horizontal."""
    lebar = draw.textlength(teks, font=font)
    draw.text(((UKURAN_GAMBAR - lebar) / 2, y), teks, font=font, fill=warna)


def buat_gambar_dummy(nama, merek, kategori, keterangan_ukuran):
    """Membuat gambar PNG ilustrasi kemasan produk, mengembalikan bytes."""
    latar, aksen = WARNA_KATEGORI.get(kategori, WARNA_DEFAULT)
    gambar = Image.new("RGB", (UKURAN_GAMBAR, UKURAN_GAMBAR), latar)
    draw = ImageDraw.Draw(gambar)

    # Bentuk kemasan dengan label kategori di bagian atas.
    kiri, atas, kanan, bawah = 110, 80, 490, 400
    lebar_isi = kanan - kiri - 40
    draw.rounded_rectangle((kiri, atas, kanan, bawah), radius=36,
                           fill="white", outline=aksen, width=6)
    draw.rounded_rectangle((kiri, atas, kanan, atas + 64), radius=36, fill=aksen)
    draw.rectangle((kiri, atas + 32, kanan, atas + 64), fill=aksen)

    label = kategori.upper()
    tulis_tengah(draw, atas + 16, label,
                 font_muat(draw, label, lebar_isi, 28), "white")

    # Merek (maksimal 2 baris).
    y = atas + 110
    for baris in textwrap.wrap(merek, 16)[:2]:
        font = font_muat(draw, baris, lebar_isi, 44)
        tulis_tengah(draw, y, baris, font, aksen)
        y += 52

    # Ukuran kemasan.
    tulis_tengah(draw, bawah - 72, keterangan_ukuran,
                 font_muat(draw, keterangan_ukuran, lebar_isi, 36), WARNA_TEKS)

    # Nama produk di bawah kemasan (maksimal 2 baris).
    y = bawah + 36
    for baris in textwrap.wrap(nama, 28)[:2]:
        font = font_muat(draw, baris, UKURAN_GAMBAR - 60, 30)
        tulis_tengah(draw, y, baris, font, WARNA_TEKS)
        y += 40

    tulis_tengah(draw, UKURAN_GAMBAR - 48, "Gambar ilustrasi",
                 muat_font(20), "#8A8178")

    buffer = io.BytesIO()
    gambar.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def pasang_gambar_dummy(produk):
    """Membuat dan menyimpan gambar dummy untuk produk yang belum bergambar."""
    keterangan = f"{format_ukuran(produk.ukuran)} {produk.satuan}".strip()
    isi = buat_gambar_dummy(
        produk.nama,
        produk.merek or "Tanpa Merek",
        produk.kategori.nama,
        keterangan,
    )
    nama_file = f"dummy-{slugify(produk.merek)}-{slugify(produk.nama)}.png"
    produk.gambar.save(nama_file, ContentFile(isi), save=True)


class Command(BaseCommand):
    help = "Mengisi database dengan data dummy kategori dan produk sembako."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Hapus semua produk terlebih dahulu sebelum mengisi ulang.",
        )
        parser.add_argument(
            "--tanpa-gambar",
            action="store_true",
            help="Jangan membuat gambar ilustrasi dummy.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        acak = random.Random(SEED_ACAK)

        if options["reset"]:
            self.hapus_produk()

        kategori_map = {}
        for nama, deskripsi in KATEGORI.items():
            kategori, _ = Kategori.objects.get_or_create(
                nama=nama,
                defaults={"deskripsi": deskripsi},
            )
            kategori_map[nama] = kategori

        jumlah_baru = 0
        jumlah_ada = 0
        jumlah_gambar = 0
        buat_gambar = not options["tanpa_gambar"]

        for nama_kategori, nama, merek, deskripsi, varian in DATA_PRODUK:
            for ukuran, satuan, harga in varian:
                ukuran, satuan = normalisasi_ukuran(ukuran, satuan)

                # Sekitar 1 dari 15 produk dibuat stok habis untuk menguji
                # bahwa produk tanpa stok tidak ikut direkomendasikan.
                stok = 0 if acak.random() < 0.07 else acak.randint(5, 120)

                produk, dibuat = Produk.objects.get_or_create(
                    nama=f"{nama} {format_ukuran(ukuran)} {satuan}",
                    merek=merek,
                    ukuran=ukuran,
                    satuan=satuan,
                    defaults={
                        "kategori": kategori_map[nama_kategori],
                        "harga": Decimal(harga),
                        "stok": stok,
                        "deskripsi": deskripsi,
                    },
                )

                if dibuat:
                    jumlah_baru += 1
                else:
                    jumlah_ada += 1

                # Produk lama yang belum bergambar juga ikut dibuatkan.
                if buat_gambar and not produk.gambar:
                    pasang_gambar_dummy(produk)
                    jumlah_gambar += 1

        self.stdout.write(self.style.SUCCESS(
            f"Selesai. Kategori: {len(kategori_map)}, "
            f"produk baru: {jumlah_baru}, sudah ada sebelumnya: {jumlah_ada}, "
            f"gambar dibuat: {jumlah_gambar}."
        ))

    def hapus_produk(self):
        """Menghapus produk yang belum pernah masuk riwayat rekomendasi."""
        jumlah_dihapus = 0
        for produk in Produk.objects.all():
            nama_gambar = produk.gambar.name if produk.gambar else ""
            try:
                produk.delete()
                jumlah_dihapus += 1
                if nama_gambar.startswith("produk/dummy-"):
                    produk.gambar.storage.delete(nama_gambar)
            except ProtectedError:
                # Produk yang sudah tercatat di riwayat rekomendasi dibiarkan.
                pass

        self.stdout.write(f"{jumlah_dihapus} produk lama dihapus.")