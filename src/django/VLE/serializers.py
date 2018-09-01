"""
Serializers.

Functions to convert certain data to other formats.
"""
from rest_framework import serializers
# import VLE.utils.generic_utils as utils
# import VLE.permissions as permissions
from VLE.models import User, Course, Node, Comment, Assignment, Role, Journal, Entry, Template, Field, Content, \
    JournalFormat, PresetNode
import VLE.utils.generic_utils as utils
import VLE.permissions as permissions
import statistics as st


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('last_login', 'username', 'first_name', 'last_name', 'is_active', 'email', 'name',
                  'profile_picture', 'is_teacher', 'lti_id', 'id', 'role', 'verified_email')
        read_only_fields = ('id', )

    def get_name(self, user):
        return user.first_name + ' ' + user.last_name

    def get_role(self, user):
        if 'course' not in self.context:
            return None

        return permissions.get_role(user, self.context['course']).name


# TODO: Merge userSerializer and OwnUserSerializer
class OwnUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'last_login', 'username', 'first_name', 'last_name', 'is_active', 'email', 'permissions',
                  'name', 'lti_id', 'profile_picture', 'is_teacher', 'grade_notifications', 'comment_notifications',
                  'verified_email')
        read_only_fields = ('id', )

    def get_name(self, user):
        return user.first_name + ' ' + user.last_name

    def get_permissions(self, user):
        # TODO: Use a serializer for this
        return permissions.get_all_user_permissions(user)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        exclude = ('author', 'users', )
        read_only_fields = ('id', )
        depth = 1


class AssignmentSerializer(serializers.ModelSerializer):
    deadline = serializers.SerializerMethodField()
    journal = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = '__all__'
        read_only_fields = ('id', )

    def get_deadline(self, assignment):
        # TODO: Check from which course it came from as well
        # TODO: When all assignments are graded, set deadline to next deadline?
        # If the user doesnt have a journal, take the deadline that is the first upcomming deadline
        if 'user' not in self.context or \
           permissions.has_assignment_permission(self.context['user'], assignment, 'can_grade_journal'):
            nodes = assignment.format.presetnode_set.all().order_by('deadline')
            if not nodes:
                return None
            return nodes[0].deadline

        # If the user has a journal, take the first upcomming not submitted deadline
        else:
            try:
                journal = Journal.objects.get(assignment=assignment, user=self.context['user'])
            except Journal.DoesNotExist:
                return None

            # TODO Incorporate assigment end date
            deadlines = journal.node_set.exclude(preset=None).values('preset__deadline').order_by('preset__deadline')
            if not deadlines:
                return None

            return deadlines[0]['preset__deadline']

    def get_journal(self, assignment):
        try:
            return Journal.objects.get(assignment=assignment, user=self.context['user']).pk
        except (KeyError, Journal.DoesNotExist):
            return None

    def get_stats(self, assignment):
        if 'user' not in self.context or \
           not permissions.has_assignment_permission(self.context['user'], assignment, 'can_grade_journal'):
            return None

        journals = JournalSerializer(assignment.journal_set.all(), many=True).data
        if not journals:
            return None
        stats = {}
        stats['needs_marking'] = sum([x['stats']['submitted'] - x['stats']['graded'] for x in journals])
        points = [x['stats']['acquired_points'] for x in journals]
        stats['average_points'] = round(st.mean(points), 2)
        return stats

    def get_course(self, assignment):
        if 'course' not in self.context:
            return None
        return CourseSerializer(self.context['course']).data


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'
        read_only_fields = ('id', )


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('id', )

    def get_author(self, comment):
        return UserSerializer(comment.author).data


class RoleSerializer(serializers.ModelSerializer):
    # TODO This even adds keys such as 'id', 'name' and 'course', prob not wanted?
    # Maybe all the permissions in a seperate variable would be nice
    class Meta:
        model = Role
        fields = '__all__'
        read_only_fields = ('id', )


class JournalSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()

    class Meta:
        model = Journal
        fields = '__all__'
        read_only_fields = ('id', )

    def get_student(self, journal):
        return UserSerializer(journal.user).data

    def get_stats(self, journal):
        entries = utils.get_journal_entries(journal)
        return {
            'acquired_points': utils.get_acquired_points(entries),
            'graded': utils.get_graded_count(entries),
            'submitted': utils.get_submitted_count(entries),
            'total_points': utils.get_max_points(journal),
        }


class JournalFormatSerializer(serializers.ModelSerializer):
    unused_templates = serializers.SerializerMethodField()
    templates = serializers.SerializerMethodField(source='available_templates')
    presets = serializers.SerializerMethodField()

    class Meta:
        model = JournalFormat
        fields = ('id', 'grade_type', 'max_points', 'unused_templates', 'templates', 'presets')
        read_only_fields = ('id', )

    def get_unused_templates(self, entry):
        return TemplateSerializer(entry.unused_templates.all(), many=True).data

    def get_templates(self, entry):
        return TemplateSerializer(entry.available_templates.all(), many=True).data

    def get_presets(self, entry):
        return PresetNodeSerializer(entry.presetnode_set.all().order_by('deadline'), many=True).data


class PresetNodeSerializer(serializers.ModelSerializer):
    deadline = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    template = serializers.SerializerMethodField()

    class Meta:
        model = PresetNode
        fields = ('id', 'type', 'deadline', 'target', 'template')
        read_only_fields = ('id', )

    def get_deadline(self, entry):
        return entry.deadline.strftime('%Y-%m-%d %H:%M')

    def get_target(self, entry):
        if entry.type == Node.PROGRESS:
            return entry.target
        return None

    def get_template(self, entry):
        if entry.type == Node.ENTRYDEADLINE:
            return TemplateSerializer(entry.forced_template).data
        return None


class EntrySerializer(serializers.ModelSerializer):
    template = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    editable = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = ('id', 'createdate', 'published', 'template', 'content', 'editable', 'grade', 'comments')
        read_only_fields = ('id', )

    def get_template(self, entry):
        return TemplateSerializer(entry.template).data

    def get_content(self, entry):
        return ContentSerializer(entry.content_set.all(), many=True).data

    def get_editable(self, entry):
        return entry.grade is None

    def get_grade(self, entry):
        # TODO: Add permission can_view_grade
        if 'user' not in self.context:
            return None
        if entry.published or permissions.has_assignment_permission(
                self.context['user'], entry.node.journal.assignment, 'can_grade_journal'):
            return entry.grade
        return None

    def get_comments(self, entry):
        if 'comments' not in self.context:
            return None
        return CommentSerializer(Comment.objects.filter(entry=entry), many=True).data


class TemplateSerializer(serializers.ModelSerializer):
    field_set = serializers.SerializerMethodField()

    class Meta:
        model = Template
        fields = '__all__'
        read_only_fields = ('id', )

    def get_field_set(self, template):
        return FieldSerializer(template.field_set.all(), many=True).data


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = '__all__'
        read_only_fields = ('id', )


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = '__all__'

#
# def participation_to_dict(participation):
#     """Convert participation to a dictionary.
#
#     Parameters
#     ----------
#     participation : Participation
#         The participation to convert.
#
#     Returns
#     -------
#     dictionary
#         Dictionary of the role and user dictionaries.
#
#     """
#     role_dict = {'role': participation.role.name}
#     user_dict = user_to_dict(participation.user)
#
#     return {**role_dict, **user_dict} if participation else None
#
#
# def course_to_dict(course):
#     """Convert course to a dictionary."""
#     return {
#         'cID': course.id,
#         'name': course.name,
#         'auth': user_to_dict(course.author),
#         'startdate': course.startdate,
#         'enddate': course.enddate,
#         'abbr': course.abbreviation
#     } if course else None
#
#
# def student_assignment_to_dict(assignment, user):
#     """Convert a student assignment to a dictionary."""
#     if not assignment:
#         return None
#     try:
#         journal = Journal.objects.get(assignment=assignment, user=user)
#     except Journal.DoesNotExist:
#         journal = None
#
#     assignment_dict = assignment_to_dict(assignment)
#     assignment_dict['journal'] = journal_to_dict(journal) if journal else None
#
#     return assignment_dict
#
#
#
# def journal_to_dict(journal):
#     """Convert a journal to a dictionary."""
#     entries = utils.get_journal_entries(journal)
#     return {
#         'jID': journal.id,
#         'student': user_to_dict(journal.user),
        # 'stats': {
        #     'acquired_points': utils.get_acquired_points(entries),
        #     'graded': utils.get_graded_count(entries),
        #     'submitted': utils.get_submitted_count(entries),
        #     'total_points': utils.get_max_points(journal),
        # }
#     } if journal else None
#
#
#
# def export_entry_to_dict(entry):
#     """Convert entry to exportable dictionary."""
#     if not entry:
#         return None
#
#     data = {
#         'createdate': entry.createdate.strftime('%d-%m-%Y %H:%M'),
#         'grade': entry.grade
#     }
#
#     # Add the field-content combinations.
#     for field, content in zip(entry.template.field_set.all(), entry.content_set.all()):
#         data.update({field.title: content.data})
#
#     # Add the comments.
#     comments = [{entrycomment.author.username: entrycomment.text}
#                 for entrycomment in Comment.objects.filter(entry=entry)]
#     data.update({'comments': comments})
#
#     return data

#
# def format_to_dict(format):
#     """Convert format to dictionary."""
#     return {
#         'max_points': format.max_points,
#         'unused_templates': [template_to_dict(template) for template in format.unused_templates.all()],
#         'templates': [template_to_dict(template) for template in format.available_templates.all()],
#         'presets': [preset_to_dict(preset) for preset in format.presetnode_set.all().order_by('deadline')],
#     } if format else None
#
#
# def preset_to_dict(preset):
#     """Convert preset node to dictionary."""
#     if not preset:
#         return None
#
#     base = {
#         'pID': preset.id,
#         'type': preset.type,
#         'deadline': preset.deadline.strftime('%Y-%m-%d %H:%M'),
#     }
#
#     if preset.type == Node.PROGRESS:
#         result = {**base, **{'target': preset.target}}
#     elif preset.type == Node.ENTRYDEADLINE:
#         result = {**base, **{'template': template_to_dict(preset.forced_template)}}
#
#     return result
#
#
# def entrycomment_to_dict(entrycomment):
#     """Convert entrycomment to dictionary."""
#     return {
#         'ecID': entrycomment.id,
#         'eID': entrycomment.entry.id,
#         'author': user_to_dict(entrycomment.author),
#         'text': entrycomment.text,
#         'published': entrycomment.published,
#         'timestamp': entrycomment.timestamp
#     } if entrycomment else None
#
