import factory


class StudentCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.Comment'

    entry = factory.SubFactory('test.factory.entry.EntryFactory')
    text = 'test-comment'
    published = True

    @factory.post_generation
    def add_author(self, create, extracted):
        if not create:
            return

        self.author = self.entry.node.journal.authors.first().user
        self.save()


class TeacherCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.Comment'

    entry = factory.SubFactory('test.factory.entry.EntryFactory')
    text = 'test-comment'
    published = False

    @factory.post_generation
    def add_author(self, create, extracted):
        if not create:
            return

        self.author = self.entry.node.journal.assignment.courses.first().author
        self.save()
