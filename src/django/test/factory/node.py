import factory


class NodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.Node'

    journal = factory.SubFactory('test.factory.journal.JournalFactory')
    entry = factory.RelatedFactory(
        'test.factory.entry.EntryFactory',
        factory_related_name='node',
    )
