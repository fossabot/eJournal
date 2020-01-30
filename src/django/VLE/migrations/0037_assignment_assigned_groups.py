# Generated by Django 2.2.8 on 2020-01-17 14:40

import django.db.models.manager
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VLE', '0036_mail_username_to_lower_case'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='assigned_groups',
            field=models.ManyToManyField(to='VLE.Group'),
        ),
        migrations.AlterModelManagers(
            name='journal',
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
