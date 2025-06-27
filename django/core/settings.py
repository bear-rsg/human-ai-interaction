import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'core/templates')


# Application definition

INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # 3rd Party
    # captchanotimeout is a custom app to override "captcha" to prevent 2 minute timeouts
    # See: https://github.com/praekelt/django-recaptcha/issues/183
    'captchanotimeout',
    'django_recaptcha',
    'ckeditor',
    'debug_toolbar',
    # Custom apps
    'account',
    'general',
    'experiments',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'settings_value': 'core.templatetags.settings_value',
            }
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Custom user model for authentication

AUTH_USER_MODEL = 'account.User'


# Redirects for login and logout

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/account/'
LOGOUT_REDIRECT_URL = '/account/login/'


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

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = False  # Set to True if using internationalisation (translations) in your project

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATICFILES_DIRS = [os.path.join(BASE_DIR, "core/static")]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")


# Media files (user uploaded content)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/latest/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CKEditor
# Image File uploads via CKEditor
CKEDITOR_UPLOAD_PATH = 'cke_uploads/'  # will be based within MEDIA dir
CKEDITOR_ALLOW_NONIMAGE_FILES = False  # only allow images to be uploaded
CKEDITOR_IMAGE_BACKEND = 'ckeditor_uploader.backends.PillowBackend'
CKEDITOR_THUMBNAIL_SIZE = (100, 100)
CKEDITOR_FORCE_JPEG_COMPRESSION = True
CKEDITOR_IMAGE_QUALITY = 90
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]
# Configuration
# For full list of configurations, see: https://ckeditor.com/docs/ckeditor4/latest/api/CKEDITOR_config.html
# For full list of toolbar buttons, see: https://ckeditor.com/latest/samples/toolbarconfigurator/index.html#advanced
SILENCED_SYSTEM_CHECKS = ["ckeditor.W001"]
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            {
                'name': 'styles',
                'items': [
                    'TextColor', 'BGColor', 'Bold', 'Italic', 'Underline', 'Strike',
                    '-',
                    'Subscript', 'Superscript'
                ]
            },
            {
                'name': 'clipboard',
                'items': ['Undo', 'Redo']
            },
            {
                'name': 'paragraph',
                'items': [
                    'NumberedList', 'BulletedList',
                    '-',
                    'Outdent', 'Indent',
                    '-',
                    'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'
                ]
            },
            {
                'name': 'links',
                'items': ['Link', 'Unlink', 'Anchor']
            },
            {
                'name': 'editing',
                'items': ['Find', '-', 'Scayt']
            },
            {
                'name': 'insert',
                'items': ['Image', 'Table', 'HorizontalRule', 'SpecialChar']
            },
            {
                'name': 'views',
                'items': ['Source', 'Maximize']
            }
        ],
        'format_tags': 'h2;h3;h4;h5;p',
        'tabSpaces': 4,
        'height': '30vh',
        'width': '100%',
        'allowedContent': True,
        'entities_greek': False,
        'entities_latin': False,
        'scayt_autoStartup': True,
        'scayt_sLang': 'en_GB',
        'uiColor': '#FFFFFF',
        'language': 'en',
        'defaultLanguage': 'en',
        'removePlugins': ','.join([
            'elementspath',
        ]),
        'versionCheck': False,
    }
}


# Import local_settings.py
SECRET_KEY = None
try:
    from .local_settings import *  # NOQA
except ImportError:
    sys.exit('Unable to import local_settings.py (refer to local_settings.example.py for help)')

# Ensure the SECRET_KEY is supplied in local_settings.py - and trust that the other settings are there too.
if not SECRET_KEY:  # NOQA
    sys.exit('Missing SECRET_KEY in local_settings.py')


# Storages

# Default STORAGES from Django documentation
# See: https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-STORAGES
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Use ManifestStaticFilesStorage when not in debug mode
if not DEBUG:  # NOQA
    STORAGES['staticfiles'] = {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"}


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'stream': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
            'maxBytes': 104857600,  # 100*1024*1024 bytes (100MB)
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['stream', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': 'True',
        },
    },
}
