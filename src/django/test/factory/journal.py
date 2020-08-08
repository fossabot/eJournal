import test.factory.participation

import factory

import VLE.factory
import VLE.models


class JournalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.Journal'

    assignment = factory.SubFactory('test.factory.assignment.AssignmentFactory')

    @factory.post_generation
    def add_user(self, create, extracted):
        if not create:
            return

        if not VLE.models.AssignmentParticipation.objects.filter(journal=self).exists():
            if extracted:
                ap = test.factory.participation.AssignmentParticipationFactory(
                    journal=self, assignment=self.assignment, user=extracted)
            else:
                ap = test.factory.participation.AssignmentParticipationFactory(
                    journal=self, assignment=self.assignment)
            self.add_author(ap)


class LtiJournalFactory(JournalFactory):
    assignment = factory.SubFactory('test.factory.assignment.LtiAssignmentFactory')

    @factory.post_generation
    def add_user(self, create, extracted):
        if not create:
            return

        if not VLE.models.AssignmentParticipation.objects.filter(journal=self).exists():
            if extracted:
                ap = test.factory.participation.LtiAssignmentParticipationFactory(
                    journal=self, assignment=self.assignment, user=extracted)
            else:
                ap = test.factory.participation.LtiAssignmentParticipationFactory(
                    journal=self, assignment=self.assignment)
            self.add_author(ap)


class GroupJournalFactory(JournalFactory):
    assignment = factory.SubFactory('test.factory.assignment.GroupAssignmentFactory')
    author_limit = 3


class PopulatedJournalFactory(JournalFactory):
    node = factory.RelatedFactory(
        'test.factory.node.NodeFactory',
        factory_related_name='journal',
    )


class JournalImportRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.JournalImportRequest'

    author = factory.SubFactory('test.factory.user.UserFactory')
    source = factory.LazyAttribute(lambda self: PopulatedJournalFactory(add_user=self.author))
    target = factory.LazyAttribute(lambda self: JournalFactory(add_user=self.author))
