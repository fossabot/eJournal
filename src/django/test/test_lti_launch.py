"""
test_lti_launch.py.

Test lti launch.
"""
import VLE.lti_launch as lti
from django.test import TestCase
import VLE.factory as factory
import json
from VLE.models import Participation, User, Course, Assignment, Journal, Role


class lti_launch_test(TestCase):
    """Lti lanch test.

    Test if the gradepassback XML can be created.
    """

    def setUp(self):
        """Setup."""
        self.roles = json.load(open('../../config.json'))

        self.created_user = factory.make_user('TestUser', 'Pass')
        self.created_user.lti_id = 'awefd'
        self.created_user.save()

        self.created_course = factory.make_course('TestCourse', 'aaaa')
        self.created_course.lti_id = 'asdf'
        self.created_course.save()

        role = Role.objects.create(name='role')
        Participation.objects.create(
            user=self.created_user,
            course=self.created_course,
            role=role
        )

        self.created_assignment = factory.make_assignment("TestAss", "TestDescr")
        self.created_assignment.lti_id = 'bughh'
        self.created_assignment.user = self.created_user
        self.created_assignment.save()

        self.created_journal = factory.make_journal(self.created_assignment, self.created_user)

    def test_select_user(self):
        """Hopefully select a user."""
        selected_user = lti.select_create_user({
            'user_id': self.created_user.lti_id,
            'lis_person_contact_email_primary': 'test@mail.com',
            'lis_person_sourcedid': 'TestUsername'
        })
        self.assertEquals(selected_user, self.created_user)

    def test_create_user(self):
        """Hopefully create a user."""
        selected_user = lti.select_create_user({
            'user_id': 99999,
            'lis_person_contact_email_primary': 'test@mail.com',
            'lis_person_sourcedid': 'TestUsername'
        })
        self.assertIsInstance(selected_user, User)

    def test_select_course(self):
        """Hopefully select a course."""
        selected_course = lti.select_create_course({
            'context_id': self.created_course.lti_id,
            'roles': self.roles['teacher'],
        },
            user=self.created_user,
            roles=self.roles
        )
        self.assertEquals(selected_course, self.created_course)

    def test_create_course(self):
        """Hopefully create a course."""
        selected_course = lti.select_create_course({
            'context_id': self.created_course.pk + 1,
            'roles': self.roles['teacher'],
            'context_title': 'TestName',
            'context_label': 'bbbb'
        },
            user=self.created_user,
            roles=self.roles
        )
        self.assertIsInstance(selected_course, Course)

    def test_create_course_unauthorized(self):
        """Only a teacher should be able to create course if non can be selected."""
        selected_course = lti.select_create_course({
            'context_id': self.created_course.pk + 1,
            'roles': self.roles['ta'],
        },
            user=self.created_user,
            roles=self.roles
        )
        self.assertEquals(None, selected_course)

    def test_select_assignment(self):
        """Hopefully select a assignment."""
        selected_assignment = lti.select_create_assignment({
            'resource_link_id': self.created_assignment.lti_id,
            'roles': self.roles['teacher'],
        },
            user=self.created_user,
            course=self.created_course,
            roles=self.roles
        )
        self.assertEquals(selected_assignment, self.created_assignment)

    def test_create_assignment(self):
        """Hopefully create a assignment."""
        selected_assignment = lti.select_create_assignment({
            'resource_link_id': self.created_course.pk + 1,
            'roles': self.roles['teacher'],
            'resource_link_title': 'TestName',
            'custom_canvas_assignment_points_possible': 7
        },
            user=self.created_user,
            course=self.created_course,
            roles=self.roles
        )
        self.assertIsInstance(selected_assignment, Assignment)

    def test_create_assignment_unauthorized(self):
        """Only a teacher should be able to create assignment if non can be selected."""
        selected_assignment = lti.select_create_assignment({
            'resource_link_id': self.created_course.pk + 1,
            'roles': self.roles['ta'],
        },
            user=self.created_user,
            course=self.created_course,
            roles=self.roles
        )
        self.assertEquals(None, selected_assignment)

    def test_select_journal(self):
        """Hopefully select a journal."""
        selected_journal = lti.select_create_journal({
            'roles': self.roles['student'],
        },
            user=self.created_user,
            assignment=self.created_assignment,
            roles=self.roles
        )
        self.assertEquals(selected_journal, self.created_journal)

    def test_create_journal(self):
        """Hopefully create a journal."""
        self.created_journal.delete()
        selected_journal = lti.select_create_journal({
            'roles': self.roles['student'],
        },
            user=self.created_user,
            assignment=self.created_assignment,
            roles=self.roles
        )
        self.assertIsInstance(selected_journal, Journal)

    def test_create_journal_unauthorized(self):
        """Only a teacher should be able to create journal if non can be selected."""
        selected_journal = lti.select_create_journal({
            'roles': self.roles['ta'],
        },
            user=self.created_user,
            assignment=self.created_assignment,
            roles=self.roles
        )
        self.assertEquals(None, selected_journal)