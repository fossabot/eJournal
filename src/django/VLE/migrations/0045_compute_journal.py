# Generated by Django 2.2.8 on 2020-04-19 12:38

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VLE', '0044_change_profile_picture'),
        ('computedfields', '0002_contributingmodelsmodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='full_names',
            field=models.TextField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='journal',
            name='grade',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='journal',
            name='needs_lti_link',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.TextField(), default=list, editable=False, size=None),
        ),
        migrations.AddField(
            model_name='journal',
            name='needs_marking',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='journal',
            name='stored_image',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='journal',
            name='stored_name',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='journal',
            name='unpublished',
            field=models.FloatField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='journal',
            name='usernames',
            field=models.TextField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='journal',
            name='image',
            field=models.TextField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='journal',
            name='name',
            field=models.TextField(editable=False, null=True),
        ),
    ]
