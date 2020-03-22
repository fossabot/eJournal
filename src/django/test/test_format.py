import test.factory as factory
from test.utils import api

from django.test import TestCase

import VLE.serializers as serialize
from VLE.models import Entry, Journal


class FormatAPITest(TestCase):
    def setUp(self):
        self.teacher = factory.Teacher()
        self.admin = factory.Admin()
        self.course = factory.Course(author=self.teacher)
        self.assignment = factory.Assignment(courses=[self.course])
        self.format = factory.Format(assignment=self.assignment)
        self.template = factory.Template(format=self.format)
        self.update_dict = {
            'assignment_details': {
                'name': 'Colloq',
                'description': 'description1',
                'is_published': True
            },
            'templates': serialize.TemplateSerializer(self.format.template_set.filter(archived=False), many=True).data,
            'removed_presets': [],
            'removed_templates': [],
            'presets': []
        }

    def test_update_format(self):
        # TODO: Improve template testing
        api.update(
            self, 'formats', params={
                'pk': self.assignment.pk, 'assignment_details': None,
                'templates': [], 'presets': [], 'removed_presets': [],
                'removed_templates': []
            }, user=factory.Student(), status=403)
        api.update(
            self, 'formats', params={
                'pk': self.assignment.pk, 'assignment_details': None,
                'templates': [], 'presets': [], 'removed_presets': [],
                'removed_templates': []
            }, user=self.teacher)
        api.update(
            self, 'formats', params={
                'pk': self.assignment.pk, 'assignment_details': None,
                'templates': [], 'presets': [], 'removed_presets': [],
                'removed_templates': []
            }, user=factory.Admin())

        # Try to publish the assignment
        api.update(self, 'formats', params={'pk': self.assignment.pk, **self.update_dict},
                   user=factory.Student(), status=403)
        api.update(self, 'formats', params={'pk': self.assignment.pk, **self.update_dict},
                   user=self.teacher)
        api.update(self, 'formats', params={'pk': self.assignment.pk, **self.update_dict},
                   user=factory.Admin())

        # Check cannot unpublish/change assignment type if there are entries
        factory.Entry(node__journal__assignment=self.assignment)
        group_dict = self.update_dict.copy()
        group_dict['assignment_details']['is_group_assignment'] = True
        self.update_dict['assignment_details']['is_published'] = False
        api.update(self, 'formats', params={'pk': self.assignment.pk, **self.update_dict},
                   user=self.teacher, status=400)
        api.update(self, 'formats', params={'pk': self.assignment.pk, **group_dict},
                   user=self.teacher, status=400)
        Entry.objects.filter(node__journal__assignment=self.assignment).delete()
        api.update(self, 'formats', params={'pk': self.assignment.pk, **self.update_dict},
                   user=self.teacher, status=200)
        api.update(self, 'formats', params={'pk': self.assignment.pk, **group_dict},
                   user=self.teacher, status=200)
        assert not Journal.objects.filter(node__journal__assignment=self.assignment).exists(), \
            'All journals should be deleted after type change'
        self.update_dict['assignment_details']['is_published'] = True
        api.update(self, 'formats', params={'pk': self.assignment.pk, **self.update_dict},
                   user=self.teacher, status=200)

        # Test script sanitation
        self.update_dict['assignment_details']['description'] = '<script>alert("asdf")</script>Rest'
        resp = api.update(self, 'formats', params={'pk': self.assignment.pk, **self.update_dict},
                          user=self.teacher)
        assert resp['assignment_details']['description'] == 'Rest'
