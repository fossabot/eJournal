from __future__ import absolute_import, unicode_literals

import datetime

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, Sum
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from VLE.models import Entry, Journal, Node, PresetNode


def _send_deadline_mail(deadline, journal):
    assignment = journal.assignment
    for author in journal.authors.all():
        course = assignment.get_active_course(author.user)
        email_data = {}
        email_data['heading'] = 'Upcoming deadline'
        email_data['full_name'] = author.user.full_name
        email_data['main_content'] = '''\
        You have an unfinished deadline coming up for {} in {}.'''.format(course.name, assignment.name)
        email_data['extra_content'] = 'Date: {}'.format(deadline['due_date'])
        email_data['button_url'] = '{}/Home/Course/{}/Assignment/{}/Journal/{}?nID={}'\
                                   .format(settings.BASELINK, course.id, assignment.id, journal.id, deadline['node'])
        email_data['button_text'] = 'View Deadline'
        email_data['profile_url'] = '{}/Profile'.format(settings.BASELINK)

        html_content = render_to_string('call_to_action.html', {'email_data': email_data})
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject='Upcoming deadline in {}'.format(assignment.name),
            body=text_content,
            from_email='eJournal | Noreply<noreply@{}>'.format(settings.EMAIL_SENDER_DOMAIN),
            headers={'Content-Type': 'text/plain'},
            to=[author.user.email]
        )

        email.attach_alternative(html_content, 'text/html')
        email.send()


def _send_deadline_mails(deadline_query):
    """_send_deadline_mails

    This sends mails to the users who are connected to the PresetNodes query that is send with.

    Arguments:
    deadline_query -- query of PresetNodes
    """
    emails_sent_to = []
    # Remove all filled entrydeadline, and remove where the user does not want to recieve an email.
    no_submissions = Q(type=Node.ENTRYDEADLINE, node__entry__isnull=True) | Q(type=Node.PROGRESS)
    notifications_enabled = Q(node__journal__authors__user__preferences__upcoming_deadline_notifications=True)
    verified_email = Q(node__journal__authors__user__verified_email=True)
    deadlines = deadline_query.filter(notifications_enabled & verified_email & no_submissions)\
                              .values('node', 'node__journal', 'due_date', 'type', 'target')
    for deadline in deadlines:
        # Only send to users who have a journal
        try:
            journal = Journal.objects.get(pk=deadline['node__journal'])
        except Journal.DoesNotExist:
            continue

        # Dont send a mail when the target points is reached
        if deadline['type'] == Node.PROGRESS and \
           (Entry.objects.filter(node__journal=journal, creation_date__lt=deadline['due_date'],
                                 grade__published=True)
                         .aggregate(Sum('grade__grade'))['grade__grade__sum'] or 0) > deadline['target']:
            continue

        _send_deadline_mail(deadline, journal)
        for author in journal.authors.all():
            emails_sent_to.append(author.user.email)

    return emails_sent_to


@shared_task
def send_upcoming_deadlines():
    """send_upcoming_deadlines

    Sends reminder emails to users who have upcoming deadlines.
    Each user receives one a week before, and a day before a mail about the deadline.
    """
    upcoming_day_deadlines = PresetNode.objects.filter(
        due_date__range=(
            datetime.datetime.utcnow().date() + datetime.timedelta(days=1),
            datetime.datetime.utcnow().date() + datetime.timedelta(days=2)))
    _send_deadline_mails(upcoming_day_deadlines)
    upcoming_week_deadlines = PresetNode.objects.filter(
        due_date__range=(
            datetime.datetime.utcnow().date() + datetime.timedelta(days=7),
            datetime.datetime.utcnow().date() + datetime.timedelta(days=8)))
    emails_sent_to = _send_deadline_mails(upcoming_week_deadlines)
    return emails_sent_to
