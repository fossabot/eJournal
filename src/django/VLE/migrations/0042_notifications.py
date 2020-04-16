# Generated by Django 2.2.8 on 2020-04-14 12:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('VLE', '0041_increase_filename_length'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='preferences',
            name='comment_notifications',
        ),
        migrations.RemoveField(
            model_name='preferences',
            name='grade_notifications',
        ),
        migrations.AddField(
            model_name='preferences',
            name='new_assignment_notifications',
            field=models.TextField(choices=[('d', 'd'), ('w', 'w'), ('p', 'p'), ('o', 'o')], default='w', max_length=1),
        ),
        migrations.AddField(
            model_name='preferences',
            name='new_comment_notifications',
            field=models.TextField(choices=[('d', 'd'), ('w', 'w'), ('p', 'p'), ('o', 'o')], default='d', max_length=1),
        ),
        migrations.AddField(
            model_name='preferences',
            name='new_course_notifications',
            field=models.TextField(choices=[('d', 'd'), ('w', 'w'), ('p', 'p'), ('o', 'o')], default='w', max_length=1),
        ),
        migrations.AddField(
            model_name='preferences',
            name='new_entry_notifications',
            field=models.TextField(choices=[('d', 'd'), ('w', 'w'), ('p', 'p'), ('o', 'o')], default='w', max_length=1),
        ),
        migrations.AddField(
            model_name='preferences',
            name='new_grade_notifications',
            field=models.TextField(choices=[('d', 'd'), ('w', 'w'), ('p', 'p'), ('o', 'o')], default='p', max_length=1),
        ),
        migrations.AddField(
            model_name='preferences',
            name='new_preset_node_notifications',
            field=models.TextField(choices=[('d', 'd'), ('w', 'w'), ('p', 'p'), ('o', 'o')], default='w', max_length=1),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.TextField(choices=[('cour', 'new_course_notifications'), ('assi', 'new_assignment_notifications'), ('prst', 'new_preset_node_notifications'), ('entr', 'new_entry_notifications'), ('grad', 'new_grade_notifications'), ('comm', 'new_comment_notifications')], max_length=4)),
                ('url', models.TextField()),
                ('message', models.TextField()),
                ('sent', models.BooleanField(default=False)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
