# Generated by Django 2.1 on 2018-09-29 20:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VLE', '0002_remove_role_can_add_course'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participation',
            name='role',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='role', to='VLE.Role'),
            preserve_default=False,
        ),
    ]
