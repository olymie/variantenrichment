# Generated by Django 3.0.13 on 2021-07-16 09:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tool', '0025_auto_20210715_1729'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='backgroundset',
            name='population',
        ),
    ]
