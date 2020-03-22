import test.factory as factory
from test.utils import api

from django.test import TestCase


class NodeTest(TestCase):
    def setUp(self):
        self.journal = factory.Journal()
        self.student = self.journal.authors.first().user
        self.teacher = self.journal.assignment.courses.first().author

    def test_get(self):
        api.get(self, 'nodes', params={'journal_id': self.journal.pk}, user=self.student)
        api.get(self, 'nodes', params={'journal_id': self.journal.pk}, user=factory.Admin())
        api.get(self, 'nodes', params={'journal_id': self.journal.pk}, user=factory.Teacher(), status=403)
        api.get(self, 'nodes', params={'journal_id': self.journal.pk}, user=self.teacher)
