
"""
Pengaturan utama proyek SmartBako.
"""

from pathlib import Path
from decouple import Csv, config

# Menentukan lokasi folder utama proyek.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==================================================
# KEAMANAN
# ==================================================

# SECRET_KEY digunakan Django untuk kebutuhan keamanan.
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-smartbako-development-key-2026",
)

# DEBUG digunakan saat proses pengembangan.
DEBUG = config("DEBUG", default=True, cast=bool)

# Daftar alamat yang boleh mengakses aplikasi.
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)


# ==================================================
# APLIKASI
# ==================================================

# Daftar aplikasi yang digunakan dalam proyek.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "smartbako",
]

# Middleware digunakan untuk memproses setiap permintaan pengguna.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Menentukan file URL utama.
ROOT_URLCONF = "config.urls"

# Mengatur lokasi dan proses pemanggilan template HTML.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Pengaturan server WSGI dan ASGI.
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ==================================================
# DATABASE
# ==================================================

# SmartBako menggunakan SQLite sebagai database.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ==================================================
# VALIDASI KATA SANDI
# ==================================================

# Mengatur aturan kata sandi ketika pengguna membuat akun.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ==================================================
# BAHASA DAN WAKTU
# ==================================================

# Mengatur bahasa dan zona waktu aplikasi.
LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True


# ==================================================
# FILE STATIS DAN MEDIA
# ==================================================

# Lokasi file CSS, JavaScript, dan gambar tampilan.
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Lokasi penyimpanan gambar produk yang diunggah admin.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Membatasi ukuran file yang diunggah menjadi 2 MB.
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

# Mengatur tipe ID utama pada model database.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==================================================
# AUTENTIKASI SMARTBAKO
# ==================================================

# Mengatur halaman tujuan untuk proses login dan logout.
LOGIN_URL = "smartbako:login"
LOGIN_REDIRECT_URL = "smartbako:beranda"
LOGOUT_REDIRECT_URL = "smartbako:landing_page"

# Sesi pengguna berakhir setelah satu hari.
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_SAVE_EVERY_REQUEST = True


# ==================================================
# EMAIL
# ==================================================

# Email ditampilkan di terminal saat pengembangan.
# Pengaturan SMTP dapat digunakan melalui file .env.
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)


# ==================================================
# PENGATURAN PRODUKSI
# ==================================================

# Pengaturan keamanan tambahan ketika DEBUG dimatikan.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
