import test.factory as factory
from test.utils import api

from django.test import TestCase

from VLE.models import Field


class JournalImportRequestTest(TestCase):
    def setUp(self):
        self.journal1_student1 = factory.Journal()
        self.student1 = self.journal1_student1.authors.first().user
        self.assignment = self.journal1_student1.assignment

        self.assignment2 = factory.Assignment()
        self.journal1_student2 = factory.Journal(assignment=self.assignment2)
        self.student2 = self.journal1_student2.authors.first().user

        ap = factory.AssignmentParticipation(assignment=self.assignment2, user=self.student1)
        self.journal2_student1 = ap.journal

    def test_create(self):
        # You cannot import a journal into itself
        data = {'journal_source_id': self.journal1_student1.pk, 'journal_target_id': self.journal1_student1.pk}
        api.create(self, 'journal_import_request', params=data, user=self.student1, status=400)

        # You can only import from and to ones own journal
        data = {'journal_source_id': self.journal1_student1.pk, 'journal_target_id': self.journal1_student2.pk}
        api.create(self, 'journal_import_request', params=data, user=self.student1, status=403)

        # You cannot request to import an empty journal
        data = {'journal_source_id': self.journal1_student1.pk, 'journal_target_id': self.journal2_student1.pk}
        api.create(self, 'journal_import_request', params=data, user=self.student1, status=400)

        # So we create an entry in journal1_student1
        format = self.assignment.format
        template = factory.Template(format=format)
        valid_create_params = {
            'journal_id': self.journal1_student1.pk,
            'template_id': template.pk,
            'content': []
        }
        fields = Field.objects.filter(template=template)
        valid_create_params['content'] = [{'data': 'test data', 'id': field.id} for field in fields]
        api.create(self, 'entries', params=valid_create_params, user=self.student1)

        # Succesfully create a JournalImportRequest
        data = {'journal_source_id': self.journal1_student1.pk, 'journal_target_id': self.journal2_student1.pk}
        api.create(self, 'journal_import_request', params=data, user=self.student1, status=201)
