# Migrasi awal SmartBako: membuat seluruh tabel sesuai smartbako/models.py.
# (Menggantikan 0001 lama yang hanya berisi Kategori dan Produk, serta 0002
# yang mengubah tabel yang belum pernah dibuat.)

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Kategori',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=100, unique=True, verbose_name='nama kategori')),
                ('deskripsi', models.TextField(blank=True, verbose_name='deskripsi')),
            ],
            options={
                'verbose_name': 'Kategori',
                'verbose_name_plural': 'Kategori',
                'ordering': ['nama'],
            },
        ),
        migrations.CreateModel(
            name='Produk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=200, verbose_name='nama produk')),
                ('merek', models.CharField(blank=True, default='', max_length=100, verbose_name='merek')),
                ('harga', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='harga')),
                ('ukuran', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='ukuran')),
                ('satuan', models.CharField(blank=True, default='', max_length=30, verbose_name='satuan')),
                ('stok', models.PositiveIntegerField(default=0, verbose_name='stok')),
                ('deskripsi', models.TextField(blank=True, verbose_name='deskripsi')),
                ('gambar', models.ImageField(blank=True, null=True, upload_to='produk/', verbose_name='gambar')),
                ('tanggal_dibuat', models.DateTimeField(auto_now_add=True)),
                ('tanggal_diperbarui', models.DateTimeField(auto_now=True)),
                ('kategori', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='produk', to='smartbako.kategori', verbose_name='kategori')),
            ],
            options={
                'verbose_name': 'Produk',
                'verbose_name_plural': 'Produk',
                'ordering': ['nama'],
            },
        ),
        migrations.CreateModel(
            name='Preferensi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('budget_min', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='anggaran minimum')),
                ('budget_max', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='anggaran maksimum')),
                ('ukuran', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='ukuran')),
                ('satuan', models.CharField(blank=True, max_length=30, verbose_name='satuan')),
                ('merek', models.CharField(blank=True, max_length=100, verbose_name='merek')),
                ('kebutuhan_tambahan', models.TextField(blank=True, verbose_name='kebutuhan tambahan')),
                ('tanggal_input', models.DateTimeField(auto_now_add=True)),
                ('kategori', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='preferensi', to='smartbako.kategori', verbose_name='kategori')),
                ('pengguna', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferensi', to=settings.AUTH_USER_MODEL, verbose_name='pengguna')),
            ],
            options={
                'verbose_name': 'Preferensi',
                'verbose_name_plural': 'Preferensi',
                'ordering': ['-tanggal_input'],
            },
        ),
        migrations.CreateModel(
            name='Rekomendasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tanggal_rekomendasi', models.DateTimeField(auto_now_add=True)),
                ('jumlah_hasil', models.PositiveIntegerField(default=0)),
                ('preferensi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rekomendasi', to='smartbako.preferensi', verbose_name='preferensi')),
            ],
            options={
                'verbose_name': 'Rekomendasi',
                'verbose_name_plural': 'Rekomendasi',
                'ordering': ['-tanggal_rekomendasi'],
            },
        ),
        migrations.CreateModel(
            name='DetailRekomendasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skor_kecocokan', models.DecimalField(decimal_places=8, default=0, max_digits=10)),
                ('peringkat', models.PositiveIntegerField()),
                ('alasan_rekomendasi', models.TextField(blank=True)),
                ('produk', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='detail_rekomendasi', to='smartbako.produk', verbose_name='produk')),
                ('rekomendasi', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detail', to='smartbako.rekomendasi', verbose_name='rekomendasi')),
            ],
            options={
                'verbose_name': 'Detail Rekomendasi',
                'verbose_name_plural': 'Detail Rekomendasi',
                'ordering': ['peringkat'],
                'constraints': [models.UniqueConstraint(fields=('rekomendasi', 'produk'), name='unik_produk_dalam_rekomendasi')],
            },
        ),
    ]