# Generated by Django 3.0.13 on 2021-03-05 20:44

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tool', '0002_auto_20210305_1226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('0ef36012-b668-4003-b6c9-8c4a7d4561dc'), editable=False, primary_key=True, serialize=False),
        ),
    ]
