import factory

import VLE.models


class EntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.Entry'

    node = factory.SubFactory('test.factory.node.NodeFactory')
    template = None
    grade = None

    @factory.post_generation
    def add_node(self, create, extracted):
        if not create:
            return

        self.node.entry = self
        self.node.type = VLE.models.Node.ENTRY
        self.node.save()
        self.node.journal.node_set.add(self.node)
        self.template = self.node.journal.assignment.format.template_set.filter(preset_only=False).first()
        self.author = self.node.journal.authors.first().user
        self.save()

        if self.template:
            for field in self.template.field_set.all():
                VLE.models.Content.objects.create(
                    entry=self, field=field, data="filling data field {}".format(field.title))
