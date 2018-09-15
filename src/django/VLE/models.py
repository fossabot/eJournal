"""
models.py.

Database file
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from VLE.utils.file_handling import get_path


class UserFile(models.Model):
    """UserFile.

    UserFile is a file uploaded by the user stored in MEDIA_ROOT/uID/aID/...
    - author: The user who uploaded the file.
    - file_name: The name of the file (no parts of the path to the file included).
    - creation_date: The time and date the file was uploaded.
    - content_type: The mimetype supplied by the user (unvalidated).
    - assignment: The assignment that the UserFile is linked to.
    """
    file = models.FileField(
        null=False,
        upload_to=get_path
    )
    file_name = models.TextField(
        null=False
    )
    author = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        null=False
    )
    creation_date = models.DateTimeField(
        auto_now_add=True
    )
    content_type = models.TextField(
        null=False
    )
    assignment = models.ForeignKey(
        'Assignment',
        on_delete=models.CASCADE,
        null=False
    )

    def __str__(self):
        """toString."""
        return self.file_name


class User(AbstractUser):
    """User.

    User is an entity in the database with the following features:
    - email: email of the user.
    - verified_email: Boolean to indicate if the user has validated their email adress.
    - USERNAME_FIELD: username of the username.
    - password: the hash of the password of the user.
    - lti_id: the DLO id of the user.
    """

    email = models.EmailField(
        unique=True,
    )
    verified_email = models.BooleanField(
        default=False
    )
    lti_id = models.TextField(
        null=True,
        unique=True,
        blank=True,
    )
    profile_picture = models.TextField(
        null=True
    )
    is_teacher = models.BooleanField(default=False)
    grade_notifications = models.BooleanField(
        default=True
    )
    comment_notifications = models.BooleanField(
        default=False
    )

    def __str__(self):
        """toString."""
        return self.username + " (" + str(self.id) + ")"


class Course(models.Model):
    """Course.

    A Course entity has the following features:
    - name: name of the course.
    - author: the creator of the course.
    - abbrevation: a max three letter abbrevation of the course name.
    - startdate: the date that the course starts.
    - lti_id: the id of the course linked over LTI.
    """

    name = models.TextField()
    abbreviation = models.TextField(
        max_length=10,
        default='XXXX',
    )

    author = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )

    users = models.ManyToManyField(
        'User',
        related_name='participations',
        through='Participation',
        through_fields=('course', 'user'),
    )

    startdate = models.DateField(
        null=True,
    )
    enddate = models.DateField(
        null=True,
    )

    lti_id = models.TextField(
        null=True,
        unique=True,
    )

    def __str__(self):
        """toString."""
        return self.name + " (" + str(self.id) + ")"


class Group(models.Model):
    """Group.

    A Group entity has the following features:
    - name: the name of the group
    - course: the course where the group belongs to
    """
    name = models.TextField()

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    lti_id = models.TextField(
        null=True,
        unique=False,
    )

    class Meta:
        """Meta data for the model: unique_together."""
        unique_together = ('name', 'course')

    def __str__(self):
        return self.name


class Role(models.Model):
    """Role.

    A complete overview of the role requirements can be found here:
    https://docs.google.com/spreadsheets/d/1M7KnEKL3cG9PMWfQi9HIpRJ5xUMou4Y2plnRgke--Tk

    A role defines the permissions of a user group within a course.
    - name: name of the role
    - list of permissions (can_...)
    """

    name = models.TextField()
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    # GLOBAL: is_superuser
    # GLOBAL: can_edit_institute

    # Course permissions.
    can_edit_course_roles = models.BooleanField(default=False)
    # GLOBAL: can_add_course
    can_view_course_participants = models.BooleanField(default=False)
    can_add_course_participants = models.BooleanField(default=False)
    can_edit_course = models.BooleanField(default=False)
    can_delete_course = models.BooleanField(default=False)

    # Assignment permissions
    can_add_assignment = models.BooleanField(default=False)
    can_edit_assignment = models.BooleanField(default=False)
    can_view_assignment_participants = models.BooleanField(default=False)
    can_delete_assignment = models.BooleanField(default=False)
    can_publish_assignment_grades = models.BooleanField(default=False)

    # Journal permissions.
    can_grade_journal = models.BooleanField(default=False)
    can_publish_journal_grades = models.BooleanField(default=False)
    can_edit_journal = models.BooleanField(default=False)
    can_comment_journal = models.BooleanField(default=False)

    def __str__(self):
        """toString."""
        return str(self.name) + " (" + str(self.id) + ")"

    class Meta:
        """Meta data for the model: unique_together."""

        unique_together = ('name', 'course',)


class Participation(models.Model):
    """Participation.

    A participation defines the way a user interacts within a certain course.
    The user is now linked to the course, and has a set of permissions
    associated with its role.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    role = models.ForeignKey(
        Role,
        null=True,
        on_delete=models.CASCADE,
        related_name='role',
    )
    group = models.ForeignKey(
        Group,
        null=True,
        on_delete=models.CASCADE,
        default=None,
    )

    class Meta:
        """Meta data for the model: unique_together."""

        unique_together = ('user', 'course',)

    def __str__(self):
        """toString."""
        return "usr: " + str(self.user) + ", crs: " + str(self.course) + ", role: " + str(self.role)


class Assignment(models.Model):
    """Assignment.

    An Assignment entity has the following features:
    - name: name of the assignment.
    - description: description for the assignment.
    - courses: a foreign key linked to the courses this assignment
    is part of.
    - format: a one-to-one key linked to the format this assignment
    holds. The format determines how a students' journal is structured.
    - lti_id: The lti id of the assignment linked over lti.
    """

    name = models.TextField()
    description = models.TextField(
        null=True,
    )
    author = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )
    points_possible = models.IntegerField(
        'points_possible',
        null=True,
        blank=True
    )
    lti_id = models.TextField(
        'lti_id',
        null=True
    )
    courses = models.ManyToManyField(Course)

    format = models.OneToOneField(
        'Format',
        on_delete=models.CASCADE
    )

    def __str__(self):
        """toString."""
        return self.name + " (" + str(self.id) + ")"


class Journal(models.Model):
    """Journal.

    A journal is a collection of Nodes that holds the student's
    entries, deadlines and more. It contains the following:
    - assignment: a foreign key linked to an assignment.
    - user: a foreign key linked to a user.
    """

    assignment = models.ForeignKey(
        'Assignment',
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )

    sourcedid = models.TextField(
        'sourcedid',
        null=True
    )

    grade_url = models.TextField(
        'grade_url',
        null=True
    )

    def __str__(self):
        """toString."""
        return self.assignment.name + " from " + self.user.username

    class Meta:
        """A class for meta data.

        - unique_together: assignment and user must be unique together.
        """

        unique_together = ('assignment', 'user',)


class Node(models.Model):
    """Node.

    The Node is an EDAG component.
    It can represent many things.
    There are three types of nodes:
    -Progress
        A node that merely is a deadline,
        and contains no entry. This deadline
        contains a 'target point amount'
        which should be reached before the
        deadline has passed.
        This type of node has to be predefined in
        the Format. In the Format it is assigned a
        deadline and a 'target point amount'.
    -Entry
        A node that is merely an entry,
        and contains no deadline. The entry
        can count toward a total
        'received point amount' which is deadlined
        by one or more Progress nodes.
        This type node can be created by the student
        an unlimited amount of times. It holds one
        of the by format predefined 'global templates'.
    -Entrydeadline
        A node that is both an entry and a deadline.
        This node is entirely separate from the
        Progress and Entry node.
        This type of node has to be predefined in
        the Format. In the Format it is assigned a
        deadline and a 'forced template'.
    """

    PROGRESS = 'p'
    ENTRY = 'e'
    ENTRYDEADLINE = 'd'
    ADDNODE = 'a'
    TYPES = (
        (PROGRESS, 'progress'),
        (ENTRY, 'entry'),
        (ENTRYDEADLINE, 'entrydeadline'),
    )

    type = models.TextField(
        max_length=4,
        choices=TYPES,
    )

    entry = models.OneToOneField(
        'Entry',
        null=True,
        on_delete=models.SET_NULL,
    )

    journal = models.ForeignKey(
        'Journal',
        on_delete=models.CASCADE,
    )

    preset = models.ForeignKey(
        'PresetNode',
        null=True,
        on_delete=models.CASCADE,
    )


class Format(models.Model):
    """Format.

    Format of a journal.
    The format determines how a students' journal is structured.
    See PresetNodes for attached 'default' nodes.
    - available_templates are those available in 'Entry' nodes.
      'Entrydeadline' nodes hold their own forced template.
    """

    PERCENTAGE = 'PE'
    GRADE = 'GR'
    TYPES = (
        (PERCENTAGE, 'percentage'),
        (GRADE, 'from 0 to 10'),
    )
    grade_type = models.TextField(
        max_length=2,
        choices=TYPES,
        default=PERCENTAGE,
    )
    max_points = models.IntegerField(
        default=10
    )
    unused_templates = models.ManyToManyField(
        'Template',
        related_name='unused_templates',
    )

    available_templates = models.ManyToManyField(
        'Template',
        related_name='available_templates',
    )

    def __str__(self):
        """toString."""
        return str(self.pk)


class PresetNode(models.Model):
    """PresetNode.

    A preset node is a node that has been pre-defined by the teacher.
    It contains the following features:
    - type: the type of the preset node (progress or entrydeadline node).
    - deadline: the deadline for this preset node.
    - forced_template: the template for this preset node - null if PROGRESS node.
    - format: a foreign key linked to a format.
    """

    TYPES = (
        (Node.PROGRESS, 'progress'),
        (Node.ENTRYDEADLINE, 'entrydeadline'),
    )

    type = models.TextField(
        max_length=4,
        choices=TYPES,
    )

    target = models.IntegerField(
        null=True,
    )

    deadline = models.DateTimeField()

    forced_template = models.ForeignKey(
        'Template',
        on_delete=models.SET_NULL,
        null=True,
    )

    format = models.ForeignKey(
        'Format',
        on_delete=models.CASCADE
    )


class Entry(models.Model):
    """Entry.

    An Entry has the following features:
    - journal: a foreign key linked to an Journal.
    - createdate: the date and time when the entry was posted.
    - late: if the entry was posted late or not.
    - TODO: edited_at
    """

    template = models.ForeignKey(
        'Template',
        on_delete=models.SET_NULL,
        null=True,
    )
    createdate = models.DateTimeField(
        default=now,
    )
    grade = models.FloatField(
        default=None,
        null=True,
    )
    published = models.BooleanField(
        default=False
    )

    def __str__(self):
        """toString."""
        return str(self.pk) + " " + str(self.grade)


class Counter(models.Model):
    """Counter.

    A single counter class which can be used to keep track of incremental values
    which do not belong to another object like the message ID for LTI messages.
    """

    name = models.TextField(
        null=False
    )
    count = models.IntegerField(
        default=0
    )

    def __str__(self):
        """toString."""
        return self.name + " is on " + self.count


class Template(models.Model):
    """Template.

    A template for an Entry.
    """

    name = models.TextField()
    max_grade = models.IntegerField(
        default=1,
    )

    def __str__(self):
        """toString."""
        return self.name


class Field(models.Model):
    """Field.

    Defines the fields of an Template
    """

    TEXT = 't'
    RICH_TEXT = 'rt'
    IMG = 'i'
    FILE = 'f'
    VIDEO = 'v'
    PDF = 'p'
    URL = 'u'
    TYPES = (
        (TEXT, 'text'),
        (RICH_TEXT, 'rich text'),
        (IMG, 'img'),
        (PDF, 'pdf'),
        (FILE, 'file'),
        (VIDEO, 'vid'),
        (URL, 'url')
    )
    type = models.TextField(
        max_length=4,
        choices=TYPES,
        default=TEXT,
    )
    title = models.TextField()
    location = models.IntegerField()
    template = models.ForeignKey(
        'Template',
        on_delete=models.CASCADE
    )
    required = models.BooleanField()

    def __str__(self):
        """toString."""
        return self.template.name + " type: " + str(self.type) + ", location: " + str(self.location)


class Content(models.Model):
    """Content.

    Defines the content of an Entry
    """

    entry = models.ForeignKey(
        'Entry',
        on_delete=models.CASCADE
    )
    field = models.ForeignKey(
        'Field',
        on_delete=models.SET_NULL,
        null=True
    )
    # TODO Consider a size limit 10MB unencoded posts? so 10 * 1024 * 1024 * 1.37?
    data = models.TextField(
        null=True
    )


class Comment(models.Model):
    """Comment.

    Comments contain the comments given to the entries.
    It is linked to a single entry with a single author and the comment text.
    """

    entry = models.ForeignKey(
        'Entry',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True
    )
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(
        default=True
    )
    last_edited = models.DateTimeField(
        default=None,
        null=True
    )
