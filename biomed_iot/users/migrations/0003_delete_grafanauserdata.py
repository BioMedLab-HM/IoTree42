# Generated by Django 5.0.4 on 2024-05-09 08:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_nodereduserdata_access_token_grafanauserdata_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='GrafanaUserData',
        ),
    ]
