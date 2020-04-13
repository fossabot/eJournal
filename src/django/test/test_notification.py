import test.factory as factory

from django.core import mail
from django.test import TestCase

import VLE.factory
from VLE.models import Notification, gen_url
from VLE.permissions import get_supervisors_of
from VLE.tasks.email import send_notification
from VLE.utils.error_handling import VLEParticipationError, VLEProgrammingError


class NotificationTest(TestCase):
    def check_send_notification(self, notification):
        outbox_len = len(mail.outbox)

        if notification.sent:
            send_notification(notification.pk)
            assert len(mail.outbox) == outbox_len, 'No actual mail should be sent'
            return

        send_notification(notification.pk)
        assert len(mail.outbox) == outbox_len + 1, 'An actual mail should be sent'
        print(mail.outbox[-1].body)
        for content in Notification.CONTENT[notification.type].values():
            if content is not None:
                assert content in mail.outbox[-1].body, 'all content should be in mail'
        # assert notification.url in mail.outbox[-1].body, 'url should be in mail'
        assert notification.user.full_name in mail.outbox[-1].body, 'full name should be in mail'

        send_notification(notification.pk)
        assert len(mail.outbox) == outbox_len + 1, 'Only 1 mail should be sent'

    def test_gen_url(self):
        node = factory.Entry().node
        user = node.journal.authors.first().user

        assert 'nID' in gen_url(node=node, user=user), 'gen_url should give node id when node is supplied'
        assert str(node.pk) in gen_url(node=node, user=user), 'gen_url should give node id when node is supplied'

        assert 'nID' not in gen_url(journal=node.journal, user=user), \
            'gen_url should not give node id when not supplied'
        assert 'Journal' in gen_url(journal=node.journal, user=user), \
            'gen_url should give journal id when not supplied'
        assert str(node.journal.pk) in gen_url(journal=node.journal, user=user), \
            'gen_url should give journal id when not supplied'

        assert 'Journal' not in gen_url(assignment=node.journal.assignment, user=user), \
            'gen_url should not give journal id when not supplied'
        assert 'Assignment' in gen_url(assignment=node.journal.assignment, user=user), \
            'gen_url should give assignment id when not supplied'
        assert str(node.journal.assignment.pk) in gen_url(assignment=node.journal.assignment, user=user), \
            'gen_url should give assignment id when not supplied'

        assert 'Assignment' not in gen_url(course=node.journal.assignment.courses.first(), user=user), \
            'gen_url should not give assignment id when not supplied'
        assert 'Course' in gen_url(course=node.journal.assignment.courses.first(), user=user), \
            'gen_url should give course id when not supplied'
        assert str(node.journal.assignment.courses.first().pk) in gen_url(
            course=node.journal.assignment.courses.first(), user=user), \
            'gen_url should give course id when not supplied'

        self.assertRaises(VLEProgrammingError, gen_url, node=node)
        self.assertRaises(VLEProgrammingError, gen_url, user=factory.Student())
        self.assertRaises(VLEParticipationError, gen_url, node=node, user=factory.Student())

    def test_get_supervisors_of(self):
        unconnected_course = factory.Course()
        connected_course1 = factory.Course()
        connected_course2 = factory.Course()

        assignment = factory.Assignment(courses=[connected_course1, connected_course2])
        journal = factory.Journal(assignment=assignment)
        other_journal = factory.Journal(assignment=assignment)

        supervisors = get_supervisors_of(journal)
        assert unconnected_course.author not in supervisors
        assert connected_course1.author in supervisors
        assert connected_course2.author in supervisors
        assert assignment.author in supervisors
        assert journal.authors.first().user not in supervisors
        assert other_journal.authors.first().user not in supervisors

    def test_comment_notification(self):
        comment = factory.TeacherComment(published=True)
        journal = comment.entry.node.journal

        assert Notification.objects.count() == 2, '1 comment notification is created (and 1 entry notification)'
        notification = Notification.objects.last()
        assert notification.user == comment.entry.author
        assert not notification.sent
        assert Notification.objects.last().type == Notification.NEW_COMMENT

        student_comment = factory.StudentComment(entry=comment.entry)
        assert Notification.objects.count() == 3, '1 new comment notification is created'
        notification = Notification.objects.last()
        assert notification.user == student_comment.entry.node.journal.assignment.courses.first().author
        assert not notification.sent, \
            'Student should not get comment notifications pushed by default'

        self.check_send_notification(notification)

        factory.TeacherComment(published=False, entry=comment.entry)
        assert Notification.objects.count() == 3, 'No new notifications should be added'

        journal.authors.add(factory.AssignmentParticipation(assignment=journal.assignment))
        factory.TeacherComment(entry=comment.entry, published=True)
        assert Notification.objects.count() == 5, '2 new notifications should be added for both students'

        factory.Participation(
            course=journal.assignment.courses.first(),
            role=journal.assignment.courses.first().role_set.filter(name='TA').first())
        # factory.AssignmentParticipation(assignment=journal.assignment, user=second_teacher)
        factory.StudentComment(entry=comment.entry)
        assert Notification.objects.count() == 7, '2 new notifications should be added for both teachers'

        # TODO: work out how to test with delay

    def test_grade_notification(self):
        entry = factory.Entry()
        notifications_before = Notification.objects.count()
        VLE.factory.make_grade(entry, entry.node.journal.assignment.author.pk, 10, published=True)
        VLE.factory.make_grade(entry, entry.node.journal.assignment.author.pk, 10, published=False)
        assert Notification.objects.count() == notifications_before + 1, '1 grade notification are created'
        assert Notification.objects.last().user == entry.node.journal.authors.first().user
        assert Notification.objects.last().type == Notification.NEW_GRADE

        self.check_send_notification(Notification.objects.last())

    def test_entry_notification(self):
        notifications_before = Notification.objects.count()
        factory.Entry()
        assert Notification.objects.count() == notifications_before + 1, '1 new notification is created'
        assert Notification.objects.last().type == Notification.NEW_ENTRY

        self.check_send_notification(Notification.objects.last())

    def test_assignment_notification(self):
        assignment = factory.Assignment(is_published=False)
        course = assignment.courses.first()
        participation = factory.Participation(course=course, role=course.role_set.get(name='Student'))
        notifications_before = Notification.objects.count()
        assignment.is_published = True
        assignment.save()
        assert Notification.objects.count() == notifications_before + 1, '1 only for student notification is created'
        assert Notification.objects.last().user == participation.user
        assert Notification.objects.last().type == Notification.NEW_ASSIGNMENT
