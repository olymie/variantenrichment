# Generated by Django 3.0.13 on 2021-06-08 15:48

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('tool', '0010_auto_20210603_1754'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='mutation_taster_score',
        ),
        migrations.AddField(
            model_name='project',
            name='cadd_job',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AlterField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.UUID('ff752b6a-dcfe-41c2-a633-1088b97e6c1c'), editable=False, primary_key=True, serialize=False),
        ),
    ]
