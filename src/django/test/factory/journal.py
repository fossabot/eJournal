import test.factory.participation

import factory

import VLE.factory
import VLE.models


class JournalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.Journal'

    assignment = factory.SubFactory('test.factory.assignment.AssignmentFactory')

    @factory.post_generation
    def add_user_to_assignment(self, create, extracted):
        if not create:
            return

        if not VLE.models.AssignmentParticipation.objects.filter(journal=self).exists():
            author = test.factory.participation.AssignmentParticipationFactory(
                journal=self, assignment=self.assignment)
            self.add_author(author)


class LtiJournalFactory(JournalFactory):
    assignment = factory.SubFactory('test.factory.assignment.LtiAssignmentFactory')

    @factory.post_generation
    def add_user_to_assignment(self, create, extracted):
        if not create:
            return

        if not VLE.models.AssignmentParticipation.objects.filter(journal=self).exists():
            ap = test.factory.participation.AssignmentParticipationFactory(
                journal=self, assignment=self.assignment)
            # TODO configure working env as test LMS
            ap.grade_url = 'https://www.ejournal.app/'
            ap.sourcedid = 'Not None'
            ap.save()
            self.authors.add(ap)


class GroupJournalFactory(JournalFactory):
    assignment = factory.SubFactory('test.factory.assignment.GroupAssignmentFactory')
    author_limit = 3
