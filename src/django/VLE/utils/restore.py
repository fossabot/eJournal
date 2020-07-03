# Assume we work in the backup environment migrated upto atleast 0038 (with the faulty migration 0038)
from VLE.models import *
import os
from django.conf import settings
import subprocess
from rest_framework import serializers
import json
import datetime
from mimetypes import guess_extension

local_file_info_dump_path = '/home/maarten/eJournal_file_restore_info.json'
production_file_info_path = '/home/mel/file_restoration/eJournal_file_restore_info.json'
production_file_temp_dir = '/home/mel/file_restoration'
missing_fc_ids_backup_24_03_2020 = [2254, 2261, 2284]
missing_fc_ids_live = [2254, 2255, 2257, 2258, 2261, 2262, 2263, 2264, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2279, 2280, 2281, 2282, 2283, 2284, 2287, 2288, 2289, 2293, 2294, 2642]
fc_ids_to_restore = [id for id in missing_fc_ids_live if id not in missing_fc_ids_backup_24_03_2020 and id < FileContext.objects.last().pk]
fc_ids_to_restore = [2255, 2257, 2258, 2262, 2263, 2264, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2279, 2280, 2281, 2282, 2283, 2287, 2288, 2289, 2293, 2294]


class FileContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileContext
        fields = "__all__"


def content_to_url(content, BASELINK=None):
    return "{}/Home/Course/{}/Assignment/{}/Journal/{}".format(
        BASELINK if BASELINK else settings.BASELINK,
        content.entry.node.journal.assignment.courses.first().pk,
        content.entry.node.journal.assignment.pk,
        content.entry.node.journal.pk
    )

def copy_file_to_production(fc):
    '''
    Copies files to temporary production directory (mel does not have permissions to SCP directly)
    '''
    p = subprocess.Popen(["scp", fc.file.path, "mel@ejournal:{}/{}.{}".format(
        production_file_temp_dir, fc.file_name, fc.file.name.split('.')[-1])])
    sts = os.waitpid(p.pid, 0)

def date_time_str_to_date_time_obj(date_time_str):
    return datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S.%f')

def retrieve_and_copy_files():
    file_info_dict = dict()

    for fc_pk in fc_ids_to_restore[1:]:
        fc = FileContext.objects.get(pk=fc_pk)

        # We are dealing with FC within RT of a journal whose file exists on disk
        assert fc.journal
        assert 'content-' in fc.file_name
        assert os.path.exists(fc.file.path)

        # The FileContext is referenced once in a content model instance
        content = Content.objects.get(data__icontains='files/{}?access'.format(fc_pk))

        serialized_fc = FileContextSerializer(fc).data
        # Add missing fields due to faulty migration
        serialized_fc['content'] = content.pk
        serialized_fc['in_rich_text'] = True

        file_info_dict[fc.pk] = {
            'fc_data': serialized_fc,
            'content_url': content_to_url(content, BASELINK='https://uva.ejournal.app'),
            'fc.file.name': fc.file.name,
            'temp_location': '{}/{}.{}'.format(production_file_temp_dir, fc.file_name, fc.file.name.split('.')[-1]),
            'destination_path': '/webapps/ejournal/media/{}'.format(fc.file.name)
        }

        copy_file_to_production(fc)

    # Dump to info file to local machine
    with open(local_file_info_dump_path, 'w') as outfile:
        json.dump(file_info_dict, outfile, indent=4)

    # Copy info file to production
    p = subprocess.Popen(["scp", local_file_info_dump_path, "mel@ejournal:{}".format(production_file_info_path)])
    sts = os.waitpid(p.pid, 0)

def move_temp_file_to_production_location():
    '''
    Move the files from the production temp directory to the final location creating missing dirs
    '''
    pass
    # Prob best to use the 'name' trick, requires permission
    # 'ejournal webapps 644'

# From Production shell
def restore_file_context_instances():
    '''
    Assumes the temp location is accessible by django
    '''
    file_info_dict = json.load(open(production_file_info_path, "r"))

    for fc_pk in fc_ids_to_restore[1:]:
        content = Content.objects.get(data__icontains='files/{}?access'.format(fc_pk))
        # restoration and production db instances are assumed to be synced
        assert content.pk == file_info_dict[str(fc_pk)]['fc_data']['content']

        p = subprocess.Popen([
            "install",
            "-C",
            "-m", "644",
            "-o", "ejournal",
            "-g", "webapps",
            file_info_dict[str(fc_pk)]['temp_location'],
            file_info_dict[str(fc_pk)]['destination_path']
        ])
        sts = os.waitpid(p.pid, 0)

        new_fc = FileContext.objects.create(
            # https://stackoverflow.com/questions/8332443/set-djangos-filefield-to-an-existing-file
            # TODO Check if the file link works like this (fc.file.name and fc.file.path etc)
            file=file_info_dict[str(fc_pk)]['fc.file.name'],
            in_rich_text=file_info_dict[str(fc_pk)]['fc_data']['in_rich_text'],
            access_id=file_info_dict[str(fc_pk)]['fc_data']['access_id'],
            file_name=file_info_dict[str(fc_pk)]['fc_data']['file_name'],
            author=User.objects.get(pk=file_info_dict[str(fc_pk)]['fc_data']['author']),
            # TODO get relevant model instances!!
            content=content,
            journal=Journal.objects.get(pk=file_info_dict[str(fc_pk)]['fc_data']['journal']),
            is_temp=False,
            # QUESTION: Deze dates niet overnemen?
            creation_date=date_time_str_to_date_time_obj(file_info_dict[str(fc_pk)]['fc_data']['creation_date']),
            last_edited=date_time_str_to_date_time_obj(file_info_dict[str(fc_pk)]['fc_data']['last_edited'])
        )

        content.data = content.data.replace('files/{}?access'.format(fc_pk), 'files/{}?access'.format(new_fc.pk))
        content.save()

file_names = ['content-21748.jpeg', 'content-1870.png', 'content-23449.png']
content_ids = [21748, 1870, 23449]
fc_ids = [2261, 2254, 2284]
access_ids = [
    '4EhQYLbdS2e3vDt06IQAX1QwJfZ742BCpgoHaQosBrFycnXD22OFhe5oVhDnhjLUpQP5KvmvhV2pQ93WUcpSLmGTLpQ9NDlDnCUb3BG6XkXrskOdesqs8S3NNbVPuWqn',
    'A1IGtMg91HjOsiJ9w7KEiTg9ogSCPNtfh0kU0OH3B0ER2O3biIbVjCjYCpnQyBNf8uIQtoZJsevSTwWo20yDf7JvLHLNKsdSbYcQRkktMvcTJ9pVYRReJr7gA5Lhu2bt',
    'aMhClS1TXijNiOPYfATnZRJWyGHPlMN5k6oHdw8j2N1Pc5lJ5IOMc2OVuMBKm5PXOAgXZVYq4KZvxdX4cBdDzbtR7qs66YMMqRx3GM0TNF71nVjPDxt0FckIRZC3xE7o'
]
temp_dir = '/home/mel/file_restoration/last-3-from-older-lars-backup'

def last_3():
    for i in range(3):
        content = Content.objects.get(pk=content_ids[i])

        # Relative path from the media root
        fc_file_name = "{}/journalfiles/{}/{}".format(
            content.entry.node.journal.authors.first().user.pk,
            content.entry.node.journal.pk,
            file_names[i]
        )
        file_destination = "{}/{}".format('/webapps/ejournal/media', fc_file_name)

        p = subprocess.Popen([
            "install",
            "-C",
            "-m", "644",
            "-o", "ejournal",
            "-g", "webapps",
            "{}/{}".format(temp_dir, file_names[i]),
            file_destination
        ])
        sts = os.waitpid(p.pid, 0)

        new_fc = FileContext.objects.create(
            file=fc_file_name,
            in_rich_text=True,
            file_name=file_names[i],
            author=content.entry.node.journal.authors.first().user,
            content=content,
            journal=content.entry.node.journal,
            is_temp=False,
        )

        content.data = content.data.replace('files/{}?access'.format(fc_ids[i]), 'files/{}?access'.format(new_fc.pk))
        content.data = content.data.replace('?access_id={}'.format(access_ids[i]), '?access_id={}'.format(new_fc.access_id))
        content.save()

        print(content_to_url(content))
