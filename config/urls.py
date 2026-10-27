from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rute untuk panel admin
    path('admin/', admin.site.urls),

    # Rute untuk aplikasi smaetbako
    path('', include('smartbako.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)