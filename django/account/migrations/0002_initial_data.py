from django.db import migrations
from django.core.management.sql import emit_post_migrate_signal
from django.db import transaction
from account import models
import sys

# Import initial_users.py, throwing an error if not found
try:
    from account.migrations.initial_users import initial_users  # NOQA
except ImportError:
    sys.exit('Unable to import initial_users.py in account/migrations (refer to initial_users.example.py for help)')


def insert_user_roles(apps, schema_editor):
    """
    Inserts UserRole objects
    """

    roles = ['admin', 'participant']

    for role in roles:
        with transaction.atomic():
            models.UserRole(name=role).save()


def insert_users(apps, schema_editor):
    """
    Inserts default Users
    """

    for user in initial_users.INITIAL_USERS:
        with transaction.atomic():
            # Convert user role name into UserRole object
            user['role'] = models.UserRole.objects.get(name=user['role'])
            # Create user object
            models.User(**user).save()


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_user_roles),
        migrations.RunPython(insert_users)
    ]
