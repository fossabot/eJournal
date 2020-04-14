import factory

import VLE.models


class TemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'VLE.Template'

    name = 'default text'

    @factory.post_generation
    def add_template(self, create, extracted):
        if not create:
            return

        self.format.template_set.add(self)

    @factory.post_generation
    def add_fields(self, create, extracted):
        if not create:
            return

        VLE.models.Field.objects.create(
            type=VLE.models.Field.TEXT, title='title', template=self, location=1, required=True)
        VLE.models.Field.objects.create(
            type=VLE.models.Field.TEXT, title='summary', template=self, location=2, required=True)
        VLE.models.Field.objects.create(
            type=VLE.models.Field.TEXT, title='optional', template=self, location=3, required=False)


class TemplateAllTypesFactory(TemplateFactory):
    name = 'all types'

    @factory.post_generation
    def add_fields(self, create, extracted):
        if not create:
            return
        fields = [
            ('TEXT', VLE.models.Field.TEXT),
            ('RICH_TEXT', VLE.models.Field.RICH_TEXT),
            ('IMG', VLE.models.Field.IMG),
            ('FILE', VLE.models.Field.FILE),
            ('VIDEO', VLE.models.Field.VIDEO),
            ('PDF', VLE.models.Field.PDF),
            ('URL', VLE.models.Field.URL),
            ('DATE', VLE.models.Field.DATE),
            ('DATETIME', VLE.models.Field.DATETIME),
            ('SELECTION', VLE.models.Field.SELECTION),
        ]
        for i, field in enumerate(fields):
            new_field = VLE.models.Field.objects.create(
                type=field[1], title=field[0], template=self, location=i, required=False)
            if field[0] == 'SELECTION':
                new_field.options = '["a","b","c","d"]'
                new_field.save()
