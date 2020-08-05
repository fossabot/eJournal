import test.factory as factory
from test.utils import api

from django.test import TestCase

from VLE.models import AssignmentParticipation, Field, JournalImportRequest


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

    def test_journal_import_request_factory(self):
        jir = factory.JournalImportRequest(author=factory.Student())

        assert JournalImportRequest.objects.count() == 1, 'A single journal import request is created'
        assert jir.target.pk != jir.source.pk, 'A unique journal is generated for both the source and target'

        # A jir generates only a single ap for both its source and target
        ap_source = AssignmentParticipation.objects.get(journal=jir.source)
        ap_target = AssignmentParticipation.objects.get(journal=jir.target)

        assert jir.author.pk is ap_source.user.pk and jir.author.pk is ap_target.user.pk, \
            'A generated journal import request shares its author among the source and target journals'

    def test_JIR_list(self):
        jir = factory.JournalImportRequest()
        supervisor = jir.target.assignment.author
        unrelated_teacher = factory.Teacher()
        data = {'journal_target_id': jir.target.pk}

        # Only relevant users can access JIRs
        api.get(self, 'journal_import_request', params=data, user=jir.author)
        api.get(self, 'journal_import_request', params=data, user=supervisor)
        api.get(self, 'journal_import_request', params=data, user=unrelated_teacher, status=403)

        jir2 = factory.JournalImportRequest(author=jir.author, target=jir.target)
        # Also generate an unrelated JIR
        factory.JournalImportRequest()

        resp = api.get(self, 'journal_import_request', params=data, user=jir.author)['journal_import_requests']

        assert len(resp) == 2, 'Both JIRs are serialized'
        assert resp[0]['id'] == jir.pk and resp[1]['id'] == jir2.pk, 'The correct JIRs are serialized'
        assert resp[0]['source']['id'] == jir.source.pk and resp[0]['target']['id'] == jir.target.pk, \
            'The correct source and target journal are serialized'

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
