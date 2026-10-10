from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(BASE_DIR, 'myproject', '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'qw5WBM5N4JDMazu823RrIbcK3bJwA9ZQHLek4orDtfI')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1')

ALLOWED_HOSTS = [
    'backend-ak.vercel.app',
    'server-3-0.vercel.app',
    'cadverse.vercel.app',
    'backend-is8n.onrender.com',
    'main-frontend-3-0.vercel.app',
    '.vercel.app',
    '.onrender.com',
    'localhost',
    '127.0.0.1',
    '*'
]

# Application definition
INSTALLED_APPS = [
    'api.admin_config.MyAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'api',
    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
CORS_ALLOW_ALL_ORIGINS = True

# Allow specific origins for frontend
CORS_ALLOWED_ORIGINS = [
    "https://cadverse.vercel.app",
    "https://backend-is8n.onrender.com",
    "https://main-frontend-3-0.vercel.app",
    "https://server-3-0.vercel.app",
    "https://backend-ak.vercel.app",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True

# Set custom user model
AUTH_USER_MODEL = 'api.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# Supabase Cloud Storage & API Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'cadverse-files')
SUPABASE_BUCKET_BEFORE = os.getenv('SUPABASE_BUCKET_BEFORE', 'showcase-before')
SUPABASE_BUCKET_AFTER = os.getenv('SUPABASE_BUCKET_AFTER', 'showcase-after')

# Cache settings for OTP storage
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'otp-cache',
    }
}

# Additional SMTP settings for signal-based emails
SIGNAL_EMAIL_HOST = os.getenv('SIGNAL_EMAIL_HOST', 'smtp.gmail.com')
SIGNAL_EMAIL_PORT = int(os.getenv('SIGNAL_EMAIL_PORT', 587))
SIGNAL_EMAIL_USE_TLS = os.getenv('SIGNAL_EMAIL_USE_TLS', 'True').lower() in ('true', '1')
SIGNAL_EMAIL_HOST_USER = os.getenv('SIGNAL_EMAIL_HOST_USER', 'cadverse.a@gmail.com')
SIGNAL_EMAIL_HOST_PASSWORD = os.getenv('SIGNAL_EMAIL_HOST_PASSWORD', 'vpwcyhkivenwabzg')
SIGNAL_DEFAULT_FROM_EMAIL = os.getenv('SIGNAL_DEFAULT_FROM_EMAIL', 'CADverse Notifications <cadverse.a@gmail.com>')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', os.getenv('GMAIL_USER', 'verify.otp.cadverse@gmail.com'))
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', os.getenv('GMAIL_PASS', 'iqwkzskfkpjlmfoq'))
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

HOMEPAGE_URL = 'https://cadverse.vercel.app'

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
    DATABASES['default']['OPTIONS'] = {
        'sslmode': 'require',
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTHENTICATION_BACKENDS = [
    'api.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
