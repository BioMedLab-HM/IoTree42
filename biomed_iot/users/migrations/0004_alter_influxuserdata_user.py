# Generated by Django 5.0.4 on 2024-05-09 09:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_delete_grafanauserdata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='influxuserdata',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
