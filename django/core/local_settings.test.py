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

ADMIN_EMAIL = 'bear-rsg@contacts.bham.ac.uk'

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
