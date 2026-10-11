
from django.shortcuts import render


def beranda(request):
    return render(request, 'smartbako/panel_pengguna/dashboard.html')
