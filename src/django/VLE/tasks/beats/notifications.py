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


def _generate_upcoming_deadline_notifications(deadline_query, preferences):
    """_generate_upcoming_deadline_notifications

    This sends mails to the users who are connected to the PresetNodes query that is send with.

    Arguments:
    deadline_query -- query of PresetNodes
    preferences -- one of these preference options needs to be set in the user preference
    """
    notifications = []
    # Remove all filled entrydeadline
    no_submissions = Q(type=VLE.models.Node.ENTRYDEADLINE, node__entry__isnull=True) | Q(type=VLE.models.Node.PROGRESS)
    deadlines = deadline_query.filter(no_submissions).distinct()
    for deadline in deadlines:
        # Only send to users who have a journal
        try:
            journal = VLE.models.Journal.objects.get(pk=deadline.node.journal)
        except VLE.models.Journal.DoesNotExist:
            continue

        # Dont send a mail when the target points is reached
        if deadline.type == VLE.models.Node.PROGRESS and journal.get_grade() > deadline.target:
            continue

        for author in journal.authors.filter(user__preferences__upcoming_deadline_reminder__in=preferences):
            if author.user.can_view(journal):
                VLE.models.Notification.objects.create(
                    type=Notification.UPCOMING_DEADLINE,
                    user=author.user,
                    node=deadline.node,
                )

    return notifications


@shared_task
def generate_upcoming_deadline_notifications():
    """generate_upcoming_deadline_notifications

    Sends reminder emails to users who have upcoming deadlines.
    Each user receives one a week before, and a day before a mail about the deadline.
    """
    return _generate_upcoming_deadline_notifications(
        VLE.models.PresetNode.objects.filter(
            due_date__range=(
                timezone.now().date() + datetime.timedelta(days=1),
                timezone.now().date() + datetime.timedelta(days=2))
        ),
        [VLE.models.Preferences.DAY, VLE.models.Preferences.DAY_AND_WEEK],
    ) + _generate_upcoming_deadline_notifications(
        VLE.models.PresetNode.objects.filter(
            due_date__range=(
                timezone.now().date() + datetime.timedelta(days=7),
                timezone.now().date() + datetime.timedelta(days=8))
        ),
        [VLE.models.Preferences.WEEK, VLE.models.Preferences.DAY_AND_WEEK],
    )


def add_notifications_to_content(content, notifications, period, name):
    """Add the notifications to the content supplied in a mail-template-friendly object.

    Skips over notifications that are sent or should be sent at another time.
    Will batch batchable notifications if there is more than one of them.

    params:
    content -- list of content to add the notifications in
    notifications -- list of notifications to loop over and add to the content list
    period -- period in which the notifications are send

    returns: list of id's that are added (even when batched)
    """
    if not notifications:
        return []

    sending = []
    user = notifications.first().user
    content.append({
        'name': name,
        'notifications': [],
    })

    for notification in notifications:
        notification.refresh_from_db()
        if not notification.sent and \
           getattr(user.preferences, VLE.models.Notification.TYPES[notification.type]['name'], Preferences.DAILY) in \
           period['pref']:
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

            content[-1]['notifications'].append({
                'title': notification.title,
                'content': notification_content,
                'url': notification.url,
            })

    # If nothing is sent, remove it from the list
    if not sending:
        content.pop()

    return sending


def gen_content_from_notifications(notifications, period):
    """Generate an object to be passed onto the digest template from a list of notifications

    Skips over notifications that are sent or should be sent at another time.
    Will batch batchable notifications if there is more than one of them.

    params:
    notifications -- list of notifications to loop over and add to the content list\
    period -- period in which the notifications are send

    returns: tuple of:
        - Object that can be passed to the digest template
        - list of id's that are added (even when batched)
    """
    sending = []
    content = []
    # Loop over notifications belonging to one course
    for course in notifications.filter(course__isnull=False).values_list('course', flat=True).distinct():
        course = VLE.models.Course.objects.get(pk=course)
        content.append({
            'name': course.name,
            'subcontent': [],
        })
        sending += add_notifications_to_content(
            content=content[-1]['subcontent'],
            notifications=notifications.filter(course=course, assignment__isnull=True),
            period=period,
            name='Course notifications'
        )

        # Loop over notifications belonging to one assignment
        for assignment in notifications.filter(
           course=course, assignment__isnull=False).values_list('assignment', flat=True).distinct():
            assignment = VLE.models.Assignment.objects.get(pk=assignment)
            sending += add_notifications_to_content(
                content=content[-1]['subcontent'],
                notifications=notifications.filter(course=course, assignment=assignment),
                period=period,
                name=assignment.name,
            )
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
    # TODO: test verified email

    # Loop over all users that potentially have a new notification
    for user in VLE.models.Notification.objects.filter(
       sent=False).order_by('user__pk').values_list('user', flat=True).distinct():

        user = VLE.models.User.objects.get(pk=user)
        content, user_sending = gen_content_from_notifications(
            VLE.models.Notification.objects.filter(user=user, sent=False),
            period
        )
        sending += user_sending

        # If there is nothing to be sent, dont send an email
        if not user_sending:
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
