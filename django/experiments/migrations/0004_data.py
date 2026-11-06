from django.db import migrations
from experiments import models


def insert_custom_setting(apps, schema_editor):
    """
    Inserts CustomSetting objects
    """

    models.CustomSetting.objects.create(
        name='experiment_instances_active_max',
        value='10',
        description="The maximum amount of experiment instances that can occur at the same time. Increasing this past 10 may encounter issues."
    )


class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0003_customsetting_and_more'),
    ]

    operations = [
        migrations.RunPython(insert_custom_setting),
    ]
