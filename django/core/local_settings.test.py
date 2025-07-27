"""
Settings that are specific to this particular instance of the project.
This can contain sensitive information (such as keys) and should not be shared with others.

REMEMBER: If modfiying the content of this file, reflect the changes in local_settings.example.py
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'u6n(9&8g-3=6d1#jyp^#))you-h&y^-5y7*&hu)cpxzeu_7#j+'

RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

DEBUG = True

ALLOWED_HOSTS = ['*']

# Used by Django Debug Toolbar (comment out to disable DDT)
INTERNAL_IPS = ["127.0.0.1"]

# Code used to create participant accounts, to restrict who can create an account
PARTICIPANT_ACCOUNT_CREATE_CODE = '123456'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'human-ai-interaction.sqlite3'),
        'TEST': {
            'NAME': os.path.join(BASE_DIR, 'human-ai-interaction_TEST.sqlite3'),
        },
    }
}

# Experiment related settings
EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES_SINCE_FIRST_MESSAGE = 5
EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES_SINCE_SINCE_CREATED = 30
EXPERIMENT_INSTANCES_ACTIVE_MAX = 1
WAIT_FOR_RESPONDER_TO_BE_DETERMINED_MINUTES = 1
PROBABILITY_RESPONDER_IS_AI = 0.5
WAIT_TO_REQUEST_RESPONSE_SECONDS = 5

# Email
# Provide the email address for the site admin (e.g. the researcher/research team)
ADMIN_EMAIL = 'example@bham.ac.uk'
# Email configuration (different options for dev vs live environments)
if DEBUG is True:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'sent_emails')
    DEFAULT_FROM_EMAIL = 'example@bham.ac.uk'
    NOTIFICATION_EMAIL = ('example@bham.ac.uk',)
else:
    EMAIL_USE_TLS = False
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'bear-mn01.bham.ac.uk'
    EMAIL_PORT = 25
    EMAIL_HOST_USER = 'example@bham.ac.uk'
    DEFAULT_FROM_EMAIL = 'example@bham.ac.uk'
    NOTIFICATION_EMAIL = ('example@bham.ac.uk',)
