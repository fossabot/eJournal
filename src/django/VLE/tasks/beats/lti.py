from __future__ import absolute_import, unicode_literals

from celery import shared_task

from VLE.models import Journal
from VLE.utils import grading


@shared_task
def check_if_need_VLE_publish():
    for journal in Journal.objects.all():
        grading.send_journal_status_to_LMS(journal)
