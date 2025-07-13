"""
Settings that are specific to this particular instance of the project.
This can contain sensitive information (such as keys) and should not be shared with others.

REMEMBER: If modfiying the content of this file, reflect the changes in local_settings.example.py
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Create a SECRET_KEY.
# Online tools can help generate this for you, e.g. https://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = ''

# Create Google RECAPTCHA public and private keys: https://www.google.com/recaptcha/
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

# Set to True if in development, or False is in production
DEBUG = True/False

# Set to ['*'] if in development, or specific IP addresses and domains if in production
ALLOWED_HOSTS = ['*']/['human-ai-interaction.bham.ac.uk']

# Used by Django Debug Toolbar (comment out to disable DDT)
INTERNAL_IPS = ["127.0.0.1"]

# Code used to create participant accounts, to restrict who can create an account
PARTICIPANT_ACCOUNT_CREATE_CODE = '123456'

# Set the database name below
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
# How many minutes since the first message should an experiment instance be made inactive
EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES_SINCE_FIRST_MESSAGE = 3
# How many minutes since the experiment instance was created (with no messages) should it be made inactive
EXPERIMENT_INSTANCE_INACTIVE_AFTER_MINUTES_SINCE_SINCE_CREATED = 30
# The maxmimum number of active experiment instances at any given time
EXPERIMENT_INSTANCES_ACTIVE_MAX = 1
# How many minutes to allow an admin to manually determine the responder of an experiment (admin or AI)
WAIT_FOR_RESPONDER_TO_BE_DETERMINED_MINUTES = 3
# The probability of an I becoming the Responder in an ExperimentInstance (instead of a user)
PROBABILITY_RESPONDER_IS_AI = 0.5

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
