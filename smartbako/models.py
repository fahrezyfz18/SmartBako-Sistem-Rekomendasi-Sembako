from django.db import models

class Kategori(models.Model):
    # Field (Kolom) untuk tabel Kategori
    nama = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nama

class Produk(models.Model):
    # Kolom untuk tabel Produk
    nama = models.CharField(max_length=200)
    merek = models.CharField(max_length=100, blank=True, null=True)
    harga = models.IntegerField()
    kemasan = models.CharField(max_length=50, blank=True, null=True) 
    gambar = models.ImageField(upload_to='produk_images/', blank=True, null=True)
    
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE, related_name='produk')

    def __str__(self):
        return f"{self.nama} ({self.merek})"