# Generated by Django 2.2.13 on 2020-06-09 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ble', '0006_auto_20200609_1540'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='seen_within_geofence',
            field=models.BooleanField(default=False),
        ),
    ]