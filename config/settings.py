"""
Pengaturan Django untuk proyek SmartBako.

Nilai rahasia dan nilai yang berbeda antar lingkungan (SECRET_KEY, DEBUG,
ALLOWED_HOSTS) dibaca dari file .env melalui python-decouple.

Dokumentasi:
https://docs.djangoproject.com/en/5.2/topics/settings/
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

from decouple import Csv, config

# Folder utama proyek (folder yang berisi manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# KEAMANAN
# ==========================================================

# SECURITY WARNING: jangan gunakan key default ini di produksi.
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-smartbako-development-key-2026",
)

# SECURITY WARNING: matikan DEBUG di produksi (DEBUG=False di .env).
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=Csv(),
)


# ==========================================================
# APLIKASI
# ==========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "smartbako",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ==========================================================
# DATABASE
# ==========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ==========================================================
# VALIDASI KATA SANDI
# ==========================================================

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


# ==========================================================
# BAHASA DAN ZONA WAKTU
# ==========================================================

LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True


# ==========================================================
# FILE STATIS DAN MEDIA
# ==========================================================

STATIC_URL = "/static/"
# Tujuan perintah `collectstatic` saat deploy.
STATIC_ROOT = BASE_DIR / "staticfiles"

# Gambar produk yang diunggah admin disimpan di <BASE_DIR>/media/produk/.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Batas ukuran unggahan (2 MB) agar server tidak terbebani.
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================================
# AUTENTIKASI SMARTBAKO
# ==========================================================

# Memakai nama URL agar tidak perlu diubah bila path berubah.
LOGIN_URL = "smartbako:login"
LOGIN_REDIRECT_URL = "smartbako:beranda"
LOGOUT_REDIRECT_URL = "smartbako:landing_page"

# Sesi berakhir setelah 1 hari tanpa aktivitas.
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_SAVE_EVERY_REQUEST = True


# ==========================================================
# EMAIL
# ==========================================================

# Saat pengembangan, email (misalnya reset kata sandi) ditampilkan di
# terminal. Ganti ke SMTP lewat .env ketika sudah siap.
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)


# ==========================================================
# PENGATURAN PRODUKSI
# ==========================================================

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"