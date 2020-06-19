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


def get_content_from_notifications(notifications, user, period):
    """Loop over all notifications, and put the content of the notification in a mail-friendly object.
    NOTE: skips over notifications that are not included in the prefered period of the user

    returns: (content list, included notification ids)
    """
    content = []
    sending = []
    for notification in notifications:
        notification.refresh_from_db()
        if not notification.sent and \
           getattr(user.preferences, VLE.models.Notification.TYPES[notification.type]['name']) in period['pref']:
            notification.sent = True
            notification.save()

            sending.append(notification.pk)
            notification_content = notification.content

            # Potentially batch notifications
            if notification.type in VLE.models.Notification.BATCHED_TYPES:
                filter = {
                    'type': notification.type,
                    VLE.models.Notification.BATCHED_TYPES[notification.type]: getattr(
                        notification, VLE.models.Notification.BATCHED_TYPES[notification.type]).pk
                }
                # See if there are also other notifications
                count = 1 + notifications.filter(**filter).count()
                # Include them in the send as a batched notification
                notifications.filter(**filter).update(sent=True)
                if count > 1:
                    notification_content = notification.batch_content(n=count)

            content.append({
                'title': notification.title,
                'content': notification_content,
                'url': notification.url,
            })

    return content, sending


@shared_task
def send_digest_notifications():
    """Send a digest email to all users with notifications turned on.

    For users with daily notifications, it will send all non send notifications that the user would like to receive
    For users with weekly notifications, it will only send all notifications on mondays
    """
    period = {
        'name': 'weekly',
        'pref': [VLE.models.Preferences.DAILY, VLE.models.Preferences.WEEKLY],
        'past': 'In the past week',
    } if datetime.datetime.today().weekday() == 0 else {
        'name': 'daily',
        'pref': [VLE.models.Preferences.DAILY],
        'past': 'In the past 24 hours',
    }
    sending = []

    # Loop over all users that potentially have a new notification
    for user in VLE.models.Notification.objects.filter(
       sent=False).order_by('user__pk').values_list('user', flat=True).distinct():

        old_sending_len = len(sending)
        user = VLE.models.User.objects.get(pk=user)
        notifications = VLE.models.Notification.objects.filter(
            user=user, sent=False)
        content = []

        # Loop over notifications belonging to one course
        for course in notifications.filter(course__isnull=False).values_list('course', flat=True).distinct():
            course = VLE.models.Course.objects.get(pk=course)
            course_notis = notifications.filter(course=course, assignment__isnull=True)
            general_notis, course_sending = get_content_from_notifications(course_notis, user, period)
            sending += course_sending
            content.append({
                'name': course.name,
                'subcontent': [],
            })
            if general_notis:
                content[-1]['subcontent'].append({
                    'name': 'Course notifications',
                    'notifications': general_notis,
                })

            # Loop over notifications belonging to one assignment
            for assignment in notifications.filter(
               course=course, assignment__isnull=False).values_list('assignment', flat=True).distinct():
                assignment = VLE.models.Assignment.objects.get(pk=assignment)
                assignment_notis = notifications.filter(assignment=assignment, node__isnull=True)
                other_assignment_notis = notifications.filter(assignment=assignment, node__isnull=False)
                general_notis, assignment_sending = get_content_from_notifications(assignment_notis, user, period)
                other_notis, other_sending = get_content_from_notifications(other_assignment_notis, user, period)
                sending += assignment_sending + other_sending
                if general_notis or other_notis:
                    content[-1]['subcontent'].append({
                        'name': assignment.name,
                        'notifications': general_notis + other_notis,
                    })

            # If no notifications are found for the set preference, remove the course from the content
            if not content[-1]['subcontent']:
                content.pop()

        # If there is nothing to be sent, dont send an email
        if old_sending_len == len(sending):
            continue

        email_data = {
            'heading': 'Your {} digest'.format(period['name']),
            'main_content': ['{}, you received the following notifications:'.format(period['past'])],
            'notifications': content,
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

    return {
        'description': 'Sent notification nrs {}'.format(sending),
        'successful': True,
    }
