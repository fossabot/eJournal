import datetime

import factory
from django.utils import timezone

import VLE.models
from VLE.utils import generic_utils as utils


class ProgressNodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.PresetNode'

    description = 'Progress node description'

    due_date = timezone.now() + datetime.timedelta(weeks=1)
    lock_date = timezone.now() + datetime.timedelta(weeks=2)

    type = VLE.models.Node.PROGRESS

    target = 5

    format = factory.SubFactory('test.factory.format.FormatFactory')

    @factory.post_generation
    def update_journals(self, create, extracted):
        if not create:
            return
        journals = VLE.models.Journal.all_objects.filter(assignment__format=self.format)
        utils.update_journals(journals, self)


class EntrydeadlineNodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.PresetNode'

    description = 'Entrydeadline node description'

    due_date = timezone.now() + datetime.timedelta(days=3)
    lock_date = timezone.now() + datetime.timedelta(days=5)

    type = VLE.models.Node.ENTRYDEADLINE

    forced_template = factory.SubFactory('test.factory.template.TemplateFactory',
                                         format=factory.SelfAttribute('..format'))

    format = factory.SubFactory('test.factory.format.FormatFactory')

    @factory.post_generation
    def update_journals(self, create, extracted):
        if not create:
            return
        journals = VLE.models.Journal.all_objects.filter(assignment__format=self.format)
        utils.update_journals(journals, self)
