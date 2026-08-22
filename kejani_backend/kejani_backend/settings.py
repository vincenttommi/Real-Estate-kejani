import environ
import os
from logging import config
from pathlib import Path
from decouple import config
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
from datetime import timedelta


#Initialize enviroment
#env = environ.Env()
# environ.Env.read_env(os.path.join(BASE_DIR, '.env'))



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config(
    "SECRET_KEY",default='django-insecure-sqre(rt!cagi(7k2i9b9o1q57fns9zl$9tzm32x#q6rt#^ej9w'
)
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "178.18.243.142",
    "0.0.0.0"
]


DEBUG = config("DEBUG",default=False,cast=bool)


ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '178.18.243.142',
    '0.0.0.0'
]


#EMAIL configuration
EMAIL_BACKEND = config('EMAIL_BACKEND',default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST',default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT',cast=int, default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS',cast='bool', default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER',default='vincenttommikorir@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD',default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL',default=EMAIL_HOST_USER)




LOGGING ={
    "version":1,
    "disable_existing_loggers":False,

    "handlers":{
        "file":{
            "level":"DEBUG",
            "class":"logging.FileHandler",
            "filename":"debug.log",
        },
    },
    "loggers":{
        "django":{
            "handlers":["file"],
            "level":"DEBUG",
            "propagate":True,
        }
    }
}


#Application definition

INSTALLED_APPS =[
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_extensions',
]

CORS_ALLOW_CREDENTIALS = True


CORS_ALLOWED_ORIGINS  = [
    "https://localhost.5173",
    "http://127.0.0.1:8000"

]


CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = ['set-cookie']

if DEBUG:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_DOMAIN = None    

CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = None

ROOT_URLCONF = "kejani_backend.urls"



REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS":"drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES":[
        # "rest_framework.permissions.IsAuthenticated"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES":[
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}


AUTH_USER_MODEL = 'user.User'


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    'user.middleware.CleanXForwardedForMiddleware',
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = 'kejani_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "dashboard/templates"],
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

WSGI_APPLICATION = 'kejani_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    "default":{
        "ENGINE":"django.db.backends.postgresql_psycopg2",
        "NAME":config("DB_NAME", default="kejani_db"),
        "USER":config("DB_USER", default="kejani_user"),
        "PASSWORD":config("DB_PASSWORD", default="tommi087"),
        "HOST":config("DB_HOST",default="localhost"),
        "PORT":config("DB_PORT", default="5432"),
}
}




SPECTACULAR_SETTINGS = {
    'TITLE': 'Kejani_backed API',
    'DESCRIPTION': '''
    *Kejani Backend API Documentation*

    Welcome to the Kejani_backend API - a platform that connects generosity with need.
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    'CONTACT': {
        'name': 'Kejani Support',
        'email': 'vincenttommikorir@gmail.com',
        'url': '',
    },

    'LICENSE': {
        'name': 'Proprietary',
        'url': 'https://kejani.co.ke/terms',
    },

    'EXTERNAL_DOCS': {
        'description': 'Kejani_Backend Documentation',
        'url': '',
    },

    # JWT Bearer Authentication
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Enter your JWT access token.',
            },
        },
    },

    'SECURITY': [
        {
            'BearerAuth': []
        }
    ],

    # Swagger UI settings
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': False,
        'defaultModelsExpandDepth': 1,
        'defaultModelExpandDepth': 1,
        'defaultModelRendering': 'example',
    },
}



# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


AUTHENTICATION_BACKENDS =[

    #Needed to login by username  in Django admin,regardless of alluath
    'django.contrib.auth.backends.ModelBackend',

    #alluath specific authentication methods, such as login by email

    'allauth.account.auth_backends.AuthenticationBackend',

]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'


#where collectstatic will put  files (for production)
STATIC_ROOT = os.path.join(BASE_DIR, "staticfile")


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, static)
]


#Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")




DEFAULT_AUTO_FIELS = "django.db.models.BigAutoField"


#APPEND_SLASH = False
scope = 'user'



SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":timedelta(minute=30),
    "REFRESH_TOKEN_LIFETIME":timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":False,
    "BLACKLIST_AFTER_ROTATION":True,
    "AUTH_HEADER_TYPE":("Bearer",),
}


CORS_ALLOW_CREDENTIALS = True
"""
instructs  the browser to allow cookies,authentication tokens and other credentials to be included  in cross-origin requests to django API
"""
