# Generated by Django 2.1.2 on 2018-10-19 11:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('VLE', '0005_presetnode_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='role',
            old_name='can_view_assignment_journals',
            new_name='can_all_view_journals',
        ),
    ]
