import test.factory as factory
from datetime import date, timedelta
from test.utils import api

from django.test import TestCase

from VLE.models import Entry, Field


class EntryAPITest(TestCase):
    def setUp(self):
        self.student = factory.Student()
        self.admin = factory.Admin()
        self.journal = factory.Journal(user=self.student)
        self.teacher = self.journal.assignment.courses.first().author
        self.journal_teacher = factory.Journal(user=self.teacher, assignment=self.journal.assignment)
        self.format = self.journal.assignment.format
        factory.Template(format=self.format)
        factory.Template(format=self.format)
        factory.Template(format=self.format)

        self.valid_create_params = {
            'journal_id': self.journal.pk,
            'template_id': self.format.template_set.first().pk,
            'content': []
        }
        fields = Field.objects.filter(template=self.format.template_set.first())
        self.valid_create_params['content'] = [{'data': 'test data', 'id': field.id} for field in fields]

    def test_create(self):
        # Check valid entry creation
        resp = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        resp2 = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        assert resp['id'] != resp2['id'], 'Multiple creations should lead to different ids'

        # Check if students cannot update journals without required parts filled in
        create_params = self.valid_create_params.copy()
        create_params['content'] = [{
            'data': 'test title',
            'id': self.valid_create_params['content'][0]['id']
        }]
        api.create(self, 'entries', params=create_params, user=self.student, status=400)

        # Check for assignment locked
        self.journal.assignment.lock_date = date.today() - timedelta(1)
        self.journal.assignment.save()
        api.create(self, 'entries', params=create_params, user=self.student, status=403)
        self.journal.assignment.lock_date = date.today() + timedelta(1)
        self.journal.assignment.save()

        # Check if template for other assignment wont work
        create_params = self.valid_create_params.copy()
        alt_journal = factory.Journal(user=self.student)
        template = factory.Template(format=alt_journal.assignment.format)
        create_params['template_id'] = template.pk
        api.create(self, 'entries', params=create_params, user=self.student, status=403)

        # Teachers shouldn't be able to make entries on their own journal
        teacher_params = self.valid_create_params.copy()
        teacher_params['journal_id'] = self.journal_teacher.pk
        api.create(self, 'entries', params=teacher_params, user=self.teacher, status=403)

        # Entries can no longer be created if the LTI link is outdated (new active uplink)
        assignment_old_lti_id = self.journal.assignment.active_lti_id
        self.journal.assignment.active_lti_id = 'new_lti_id_1'
        self.journal.assignment.save()
        resp = api.create(self, 'entries', params=self.valid_create_params, user=self.student, status=403)
        assert resp['description'] == self.journal.outdated_link_warning_msg, 'When the active LTI uplink is outdated' \
            ' no more entries can be created.'
        self.journal.assignment.active_lti_id = assignment_old_lti_id
        self.journal.assignment.save()

        # TODO: Test for entry bound to entrydeadline
        # TODO: Test with file upload
        # TODO: Test added index

    def test_valid_entry(self):
        template = factory.TemplateAllTypes(format=self.format)
        fields = Field.objects.filter(template=template)
        entries = {
            Field.TEXT: ['text', 'VALID'],
            Field.RICH_TEXT: ['<p> RICH </p>', 'VALID'],
            Field.VIDEO: ['https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'INVALID'],
            Field.URL: ['https://ejournal.app', 'INVALID'],
            Field.DATE: ['2019-10-10', 'INVALID'],
            Field.DATETIME: ['2019-10-10T12:12:00', 'INVALID'],
            Field.SELECTION: ['a', 'INVALID'],
        }
        create_params = {
            'journal_id': self.journal.pk,
            'template_id': template.pk,
            'content': [{
                'id': f.pk,
                'data': entries[f.type][0]
            } for f in fields if f.type in entries]
        }

        api.create(self, 'entries', params=create_params, user=self.student)['entry']
        # Test is all
        for i, field in enumerate(create_params['content']):
            field['data'] = list(entries.values())[i][1]
            if field['data'] != 'VALID':
                api.create(self, 'entries', params=create_params, user=self.student, status=400)
            field['data'] = list(entries.values())[i][0]

    def test_required_and_optional(self):
        # Creation with only required params should work
        required_only_creation = {
            'journal_id': self.journal.pk,
            'template_id': self.format.template_set.first().pk,
            'content': []
        }
        fields = Field.objects.filter(template=self.format.template_set.first())
        required_only_creation['content'] = [{'data': 'test data', 'id': field.id}
                                             for field in fields if field.required]
        api.create(self, 'entries', params=required_only_creation, user=self.student)

        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        params = {
            'pk': entry['id'],
            'content': [{
                'id': field['field'],
                'data': ''
            } for field in entry['content']]
        }
        # Student should always provide required parameters
        api.update(self, 'entries', params=params.copy(), user=self.student, status=400)

        # Student should be able to update only the required fields, leaving the optinal fields empty
        fields = Field.objects.filter(template=self.format.template_set.first())
        params = {
            'pk': entry['id'],
            'content': [{
                'id': field.pk,
                'data': 'filled' if field.required else ''
            } for field in fields]
        }
        resp = api.update(self, 'entries', params=params.copy(), user=self.student)['entry']
        assert len(resp['content']) == 2, 'Response should have emptied the optional fields'
        # Student should be able to edit an optinal field
        params = {
            'pk': entry['id'],
            'content': [{
                'id': field.pk,
                'data': 'filled'
            } for field in fields]
        }
        resp = api.update(self, 'entries', params=params.copy(), user=self.student)['entry']
        assert len(resp['content']) == 3 and resp['content'][2]['data'] == 'filled', \
            'Response should have filled the optional fields'

    def test_update(self):
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']

        params = {
            'pk': entry['id'],
            'content': [{
                'id': field['field'],
                'data': field['data']
            } for field in entry['content']]
        }

        api.update(self, 'entries', params=params.copy(), user=self.student)
        # Other users shouldn't be able to update an entry
        api.update(self, 'entries', params=params.copy(), user=self.teacher, status=403)

        # Check for assignment locked
        self.journal.assignment.lock_date = date.today() - timedelta(1)
        self.journal.assignment.save()
        api.update(self, 'entries', params=params.copy(), user=self.student, status=403)
        self.journal.assignment.lock_date = date.today() + timedelta(1)
        self.journal.assignment.save()

        # Entries can no longer be edited if the LTI link is outdated (new active uplink)
        assignment_old_lti_id = self.journal.assignment.active_lti_id
        self.journal.assignment.active_lti_id = 'new_lti_id_2'
        self.journal.assignment.save()
        resp = api.update(self, 'entries', params=params.copy(), user=self.student, status=403)
        assert resp['description'] == self.journal.outdated_link_warning_msg, 'When the active LTI uplink is outdated' \
            ' no more entries can be created.'
        self.journal.assignment.active_lti_id = assignment_old_lti_id
        self.journal.assignment.save()

        # Grade and publish an entry
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 5, 'published': True}, user=self.student,
                   status=403)
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 5, 'published': True}, user=self.teacher)

        # Shouldn't be able to edit entries after grade
        api.update(self, 'entries', params=params.copy(), user=self.student, status=400)

        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 5, 'published': False}, user=self.teacher)
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 5, 'published': True}, user=self.teacher)
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 5, 'published': True},
                   user=factory.Teacher(), status=403)

        # Check if a published entry cannot be unpublished
        api.create(self, 'grades', params={'entry_id': entry['id'], 'published': False}, user=self.teacher, status=400)

    def test_destroy(self):
        # Only a student can delete their own entry
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        api.delete(self, 'entries', params={'pk': entry['id']}, user=factory.Student(), status=403)
        api.delete(self, 'entries', params={'pk': entry['id']}, user=self.teacher, status=403)
        api.delete(self, 'entries', params={'pk': entry['id']}, user=self.student)

        # Superusers can delete all entries
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        api.delete(self, 'entries', params={'pk': entry['id']}, user=factory.Admin())

        # Only superusers should be allowed to delete graded entries
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 5, 'published': True}, user=self.teacher)
        api.delete(self, 'entries', params={'pk': entry['id']}, user=self.student, status=403)
        api.delete(self, 'entries', params={'pk': entry['id']}, user=factory.Admin())

        # Entries can no longer be deleted if the LTI link is outdated (new active uplink)
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        entry = Entry.objects.get(pk=entry['id'])
        journal = entry.node.journal
        assignment_old_lti_id = journal.assignment.active_lti_id
        journal.assignment.active_lti_id = 'new_lti_id_3'
        journal.assignment.save()

        resp = api.delete(self, 'entries', params={'pk': entry.pk}, user=self.student, status=403)
        assert resp['description'] == journal.outdated_link_warning_msg, 'When the active LTI uplink is outdated' \
            ' no more entries can be created.'
        journal.assignment.active_lti_id = assignment_old_lti_id
        journal.assignment.save()

        # Only superusers should be allowed to delete locked entries
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        self.journal.assignment.lock_date = date.today() - timedelta(1)
        self.journal.assignment.save()
        api.delete(self, 'entries', params={'pk': entry['id']}, user=self.student, status=403)
        api.delete(self, 'entries', params={'pk': entry['id']}, user=factory.Admin())

    def test_grade(self):
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        entry = api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 1, 'published': True},
                           user=self.teacher)['entry']
        assert entry['grade']['grade'] == 1
        entry = api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 0, 'published': True},
                           user=self.teacher)['entry']
        assert entry['grade']['grade'] == 0

    def test_grade_history(self):
        entry = api.create(self, 'entries', params=self.valid_create_params, user=self.student)['entry']
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 1, 'published': True},
                   user=self.teacher)
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 1, 'published': False},
                   user=self.teacher)
        api.create(self, 'grades', params={'entry_id': entry['id'], 'grade': 10, 'published': True},
                   user=self.teacher)
        grade_history = api.get_list(self, 'grades', params={'entry_id': entry['id']},
                                     user=self.teacher)['grade_history']
        assert len(grade_history) == 3, 'Grade history is incomplete.'
        assert grade_history[0]['author'] == grade_history[1]['author'] == grade_history[2]['author'] == \
            self.teacher.full_name, 'Teacher should be author of all grades.'
        assert grade_history[0]['grade'] == grade_history[1]['grade'] == 1
        assert grade_history[2]['grade'] == 10
        assert grade_history[0]['published'] == grade_history[2]['published'] and grade_history[0]['published'], \
            'First and last grade should be published.'
        assert not grade_history[1]['published'], 'Second grade should be unpublished.'
