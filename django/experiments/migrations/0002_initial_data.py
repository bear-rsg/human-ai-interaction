from django.db import migrations
from experiments import models


def insert_modalities(apps, schema_editor):
    """
    Inserts Modality objects
    """

    for obj in [
        {
            'name': 'Text',
            'icon': '<i class="fa-solid fa-comments"></i>'
        },
        {
            'name': 'Audio',
            'icon': '<i class="fa-solid fa-headphones"></i>'
        },
        {
            'name': 'Video',
            'icon': '<i class="fa-solid fa-video"></i>'
        },
    ]:
        models.Modality.objects.create(**obj)

class Migration(migrations.Migration):

    dependencies = [
        ('experiments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_modalities),
    ]
