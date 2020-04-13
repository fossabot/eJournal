import test.factory as factory

from django.test import TestCase

from VLE.models import Notification
from VLE.tasks.email import send_notification


class NotificationTest(TestCase):
    def test_comment(self):
        comment = factory.TeacherComment(published=True)
        journal = comment.entry.node.journal

        assert Notification.objects.count() == 1, '1 comment notification is created'
        notification = Notification.objects.first()
        assert notification.user == comment.entry.author
        assert not notification.sent

        student_comment = factory.StudentComment()
        assert Notification.objects.count() == 2, '1 new comment notification is created'
        notification = Notification.objects.last()
        assert notification.user == student_comment.entry.node.journal.assignment.courses.first().author
        assert not notification.sent, \
            'Student should not get comment notifications pushed by default'

        send_notification(notification.pk)
        assert Notification.objects.get(pk=notification.pk).sent, 'Notification should be sent after sending'

        factory.TeacherComment(published=False)
        assert Notification.objects.count() == 2, 'No new notifications should be added'

        journal.authors.add(factory.AssignmentParticipation(assignment=journal.assignment))
        factory.TeacherComment(entry=comment.entry, published=True)
        assert Notification.objects.count() == 4, '2 new notifications should be added for both students'

        factory.Participation(
            course=journal.assignment.courses.first(),
            role=journal.assignment.courses.first().role_set.filter(name='TA').first())
        # factory.AssignmentParticipation(assignment=journal.assignment, user=second_teacher)
        factory.StudentComment(entry__node__journal=journal)
        assert Notification.objects.count() == 6, '2 new notifications should be added for both teachers'

        # TODO: work out how to test with delay

    def test_grade(self):
        entry = factory.Entry()
        notifications_before = Notification.objects.count()
        factory.Grade(entry=entry)
        # TODO: fix factory boy so that it doesnt create two grades for some reason (other then it, it is working)
        assert Notification.objects.count() == notifications_before + 2, '2 grade notification are created'
        assert Notification.objects.last().user == entry.node.journal.authors.first().user

    # def test_entry(self):
    #     notifications_before = Notification.objects.count()
    #     factory.Entry()
    #     assert Notification.objects.count() == notifications_before + 1, '1 new notification is created'
