# Generated by Django 3.0.13 on 2021-06-24 07:59

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tool', '0011_auto_20210608_1748'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='cadd_job',
            new_name='cadd_file',
        ),
        migrations.AlterField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('c171e0d8-d2fe-4611-9959-94011cff713a'), editable=False, primary_key=True, serialize=False),
        ),
    ]
