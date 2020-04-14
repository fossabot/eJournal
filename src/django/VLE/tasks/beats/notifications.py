from __future__ import absolute_import, unicode_literals

import datetime

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

import VLE.models


def _send_deadline_mail(deadline, journal):
    assignment = journal.assignment
    emails_sent_to = []
    # remove where the user does not want to recieve an email.
    for author in journal.authors.filter(
       user__verified_email=True, user__preferences__upcoming_deadline_notifications=True):
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
        emails_sent_to.append(author.user.email)
    return emails_sent_to


def _send_deadline_mails(deadline_query):
    """_send_deadline_mails

    This sends mails to the users who are connected to the PresetNodes query that is send with.

    Arguments:
    deadline_query -- query of PresetNodes
    """
    emails_sent_to = []
    # Remove all filled entrydeadline
    no_submissions = Q(type=VLE.models.Node.ENTRYDEADLINE, node__entry__isnull=True) | Q(type=VLE.models.Node.PROGRESS)
    deadlines = deadline_query.filter(no_submissions).distinct()\
                              .values('node', 'node__journal', 'due_date', 'type', 'target')
    for deadline in deadlines:
        # Only send to users who have a journal
        try:
            journal = VLE.models.Journal.objects.get(pk=deadline['node__journal'])
        except VLE.models.Journal.DoesNotExist:
            continue

        # Dont send a mail when the target points is reached
        if deadline['type'] == VLE.models.Node.PROGRESS and journal.get_grade() > deadline['target']:
            continue

        emails_sent_to += _send_deadline_mail(deadline, journal)

    return emails_sent_to


@shared_task
def send_upcoming_deadlines():
    """send_upcoming_deadlines

    Sends reminder emails to users who have upcoming deadlines.
    Each user receives one a week before, and a day before a mail about the deadline.
    """
    upcoming_day_deadlines = VLE.models.PresetNode.objects.filter(
        due_date__range=(
            timezone.now().date() + datetime.timedelta(days=1),
            timezone.now().date() + datetime.timedelta(days=2)))
    emails_sent_to = _send_deadline_mails(upcoming_day_deadlines)
    upcoming_week_deadlines = VLE.models.PresetNode.objects.filter(
        due_date__range=(
            timezone.now().date() + datetime.timedelta(days=7),
            timezone.now().date() + datetime.timedelta(days=8)))
    emails_sent_to += _send_deadline_mails(upcoming_week_deadlines)
    return emails_sent_to


@shared_task
def send_digest_notiications():
    period = {
        'name': 'weekly',
        'pref': [VLE.models.Preferences.DAILY, VLE.models.Preferences.WEEKLY],
        'past': 'In the past week',
    } if datetime.datetime.today().weekday() == 0 else {
        'name': 'daily',
        'pref': [VLE.models.Preferences.DAILY],
        'past': 'In the past 24 hours',
    }
    types = VLE.models.Notification.TYPES

    for user in VLE.models.Notification.objects.filter(
       sent=False).order_by('user__pk').values_list('user', flat=True).distinct():
        user = VLE.models.User.objects.get(pk=user)
        notifications = VLE.models.Notification.objects.filter(user=user)
        content = ['{}, you received the following notifications:'.format(period['past'])]
        # For each type, check if user has that preference as this digest type, if so, count them per type
        # And add a proper message together with the count to the content list
        for type in types.keys():
            filtered = notifications.filter(type=type)
            if getattr(user.preferences, types[type]['name']) in period['pref'] and filtered.exists():
                filtered.update(sent=True)
                if filtered.count() == 1:
                    content.append(types[type]['singular'])
                else:
                    content.append(types[type]['plural'].format(filtered.count()))

        if len(content) == 1:
            continue

        email_data = {
            'heading': 'Your {} digest'.format(period),
            'main_content': content,
            'full_name': user.full_name,
            'button_url': '{}/Home/'.format(settings.BASELINK),
            'button_text': 'Go to eJournal',
            'profile_url': '{}/Profile'.format(settings.BASELINK)
        }

        html_content = render_to_string('digest.html', {'email_data': email_data})
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject='{} digest - eJournal'.format(period['name'].title()),
            body=text_content,
            from_email='eJournal | Noreply<noreply@{}>'.format(settings.EMAIL_SENDER_DOMAIN),
            headers={'Content-Type': 'text/plain'},
            to=[user.email]
        )

        email.attach_alternative(html_content, 'text/html')
        email.send()

    VLE.models.Notification.objects.filter(creation_date__lt=timezone.now() - datetime.timedelta(days=30)).delete()
