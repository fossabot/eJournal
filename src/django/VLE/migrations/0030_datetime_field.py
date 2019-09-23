# Generated by Django 2.1.7 on 2019-09-19 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VLE', '0029_delete_lti_ids_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='field',
            name='type',
            field=models.TextField(choices=[('t', 'text'), ('rt', 'rich text'), ('i', 'img'), ('p', 'pdf'), ('f', 'file'), ('v', 'vid'), ('u', 'url'), ('d', 'date'), ('dt', 'datetime'), ('s', 'selection')], default='t', max_length=4),
        ),
    ]
