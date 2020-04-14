"""
models.py.

Database file
"""
import os
import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField, CIEmailField, CITextField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Sum
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now

import VLE.permissions as permissions
import VLE.utils.file_handling as file_handling
from VLE.tasks.email import send_push_notification
from VLE.utils import sanitization
from VLE.utils.error_handling import (VLEBadRequest, VLEParticipationError, VLEPermissionError, VLEProgrammingError,
                                      VLEUnverifiedEmailError)


class Instance(models.Model):
    """Global settings for the running instance."""
    allow_standalone_registration = models.BooleanField(
        default=True
    )
    name = models.TextField(
        default='eJournal'
    )

    def to_string(self, user=None):
        return self.name


def gen_url(node=None, journal=None, assignment=None, course=None, user=None):
    if not (node or journal or assignment or course):
        raise VLEProgrammingError('(gen_url) no object was supplied')

    if journal is None and node is not None:
        journal = node.journal
    if assignment is None and journal is not None:
        assignment = journal.assignment
    if course is None and assignment is not None:
        if user is None:
            raise VLEProgrammingError('(gen_url) if course is not supplied, user needs to be supplied')
        course = assignment.get_active_course(user)
        if course is None:
            raise VLEParticipationError(assignment, user)

    url = '{}/Home/Course/{}'.format(settings.BASELINK, course.pk)
    if assignment:
        url += '/Assignment/{}'.format(assignment.pk)
        if journal:
            url += '/Journal/{}'.format(journal.pk)
            if node:
                url += '?nID={}'.format(node.pk)

    return url


# https://stackoverflow.com/a/2257449
def access_gen(size=128, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))


class FileContext(models.Model):
    """FileContext.

    FileContext is a file uploaded by the user stored in MEDIA_ROOT/uID/<category>/?[id/]<filename>
        Where category is selected from {course, assignment, journal}

    - file: the actual filefield contain a reference to the physical file.
    - file_name: The name of the file (not unique and no parts of the path to the file included).
    - author: The user who uploaded the file. Can be null so the File persist on user deletion.
    - assignment: The assignment that the File is linked to (e.g. assignment description).
    - content: The content that the File is linked to. Can be rich text or a dedicated file field.
    - course: The course that the File is linked to (e.g. course description).
    - journal: The journal that the File is linked to (e.g. comment).
    - creation_date: The time and date the file was uploaded.
    """
    file = models.FileField(
        null=False,
        upload_to=file_handling.get_file_path
    )
    in_rich_text = models.BooleanField(
        default=False
    )
    access_id = models.CharField(
        null=False,
        default=access_gen,
        max_length=128,
        unique=True,
    )
    file_name = models.TextField(
        null=False
    )
    author = models.ForeignKey(
        'User',
        null=True,
        on_delete=models.SET_NULL
    )
    assignment = models.ForeignKey(
        'Assignment',
        on_delete=models.CASCADE,
        null=True
    )
    content = models.ForeignKey(
        'Content',
        on_delete=models.CASCADE,
        null=True
    )
    comment = models.ForeignKey(
        'Comment',
        on_delete=models.CASCADE,
        null=True
    )
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        null=True
    )
    journal = models.ForeignKey(
        'Journal',
        on_delete=models.CASCADE,
        null=True
    )
    is_temp = models.BooleanField(
        default=True
    )

    creation_date = models.DateTimeField(editable=False)
    last_edited = models.DateTimeField()

    def download_url(self, access_id=False):
        if access_id:
            return '{}/files/{}?access_id={}'.format(settings.API_URL, self.pk, self.access_id)
        return '/files/{}/'.format(self.pk)

    def cascade_from_user(self, user):
        return self.author is user and self.assignment is None and self.course is None and self.journal is None

    def save(self, *args, **kwargs):
        if self._state.adding:
            if not self.creation_date:
                self.creation_date = timezone.now()
            if not self.author:
                raise VLEProgrammingError('FileContext author should be set on creation')
        self.last_edited = timezone.now()

        return super(FileContext, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.file.delete()
        super(FileContext, self).delete(*args, **kwargs)

    def to_string(self, user=None):
        return "FileContext"


@receiver(models.signals.post_delete, sender=FileContext)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes file from filesystem when corresponding `FileContext` object is deleted."""
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)


class User(AbstractUser):
    """User.

    User is an entity in the database with the following features:
    - full_name: full name of the user
    - email: email of the user.
    - verified_email: Boolean to indicate if the user has validated their email address.
    - password: the hash of the password of the user.
    - lti_id: the DLO id of the user.
    """

    full_name = models.CharField(
        null=False,
        max_length=200
    )
    username = CITextField(
        unique=True,
        max_length=150,
    )
    email = CIEmailField(
        blank=True,
        unique=True,
        null=True,
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
    is_teacher = models.BooleanField(
        default=False
    )
    feedback_file = models.FileField(
        null=True,
        blank=True,
        upload_to=file_handling.get_feedback_file_path
    )
    is_test_student = models.BooleanField(
        default=False
    )

    def check_permission(self, permission, obj=None, message=None):
        """
        Throws a VLEPermissionError when the user does not have the specified permission, as defined by
        has_permission.
        """
        if not self.has_permission(permission, obj):
            raise VLEPermissionError(permission, message)

    def has_permission(self, permission, obj=None):
        """
        Returns whether the user has the given permission.
        If obj is None, it tests the general permissions.
        If obj is a Course, it tests the course permissions.
        If obj is an Assignment, it tests the assignment permissions.
        Raises a VLEProgramming error when misused.
        """
        if obj is None:
            return permissions.has_general_permission(self, permission)
        if isinstance(obj, Course):
            return permissions.has_course_permission(self, permission, obj)
        if isinstance(obj, Assignment):
            return permissions.has_assignment_permission(self, permission, obj)
        raise VLEProgrammingError("Permission object must be of type None, Course or Assignment.")

    def check_verified_email(self):
        if not self.verified_email:
            raise VLEUnverifiedEmailError()

    def check_participation(self, obj):
        if not self.is_participant(obj):
            raise VLEParticipationError(obj, self)

    def is_supervisor_of(self, user):
        if self.is_superuser:
            return True

        return permissions.is_user_supervisor_of(self, user)

    def is_participant(self, obj):
        if self.is_superuser:
            return True
        if isinstance(obj, Course):
            return Course.objects.filter(pk=obj.pk, users=self).exists()
        if isinstance(obj, Assignment):
            return Assignment.objects.filter(pk=obj.pk, courses__users=self).exists()
        raise VLEProgrammingError("Participant object must be of type Course or Assignment.")

    def check_can_view(self, obj):
        if not self.can_view(obj):
            raise VLEPermissionError(message='You are not allowed to view {}'.format(obj.to_string(user=self)))

    def can_view(self, obj):
        if self.is_superuser:
            return True

        if isinstance(obj, Course):
            return self.is_participant(obj)

        elif isinstance(obj, Assignment):
            if self.is_participant(obj):
                if self.has_permission('can_have_journal', obj) and obj.assigned_groups.exists() and \
                   not obj.assigned_groups.filter(participation__user=self).exists():
                    return False
                return obj.is_published or self.has_permission('can_view_unpublished_assignment', obj)
            return False
        elif isinstance(obj, Journal):
            if not obj.authors.filter(user=self).exists():
                return self.has_permission('can_view_all_journals', obj.assignment)
            else:
                return self.has_permission('can_have_journal', obj.assignment)

        elif isinstance(obj, Comment):
            if not self.can_view(obj.entry.node.journal):
                return False
            if obj.published:
                return True
            return self.has_permission('can_grade', obj.entry.node.journal.assignment)

        elif isinstance(obj, User):
            if self == obj:
                return True
            if permissions.is_user_supervisor_of(self, obj):
                return True
            if permissions.is_user_supervisor_of(obj, self):
                return True
            if Journal.objects.filter(authors__user__in=[self]).filter(authors__user__in=[obj]).exists():
                return True

        return False

    def check_can_edit(self, obj):
        if not permissions.can_edit(self, obj):
            raise VLEPermissionError(message='You are not allowed to edit {}'.format(str(obj)))

    def to_string(self, user=None):
        if user is None:
            return "User"
        if not user.can_view(self):
            return "User"

        return self.username + " (" + str(self.pk) + ")"

    def save(self, *args, **kwargs):
        if not self.email and not self.is_test_student:
            raise ValidationError('A legitimate user requires an email adress.')

        if self._state.adding:
            if self.is_test_student and settings.LTI_TEST_STUDENT_FULL_NAME not in self.full_name:
                raise ValidationError('Test user\'s full name deviates on creation.')
        else:
            pre_save = User.objects.get(pk=self.pk)
            if pre_save.is_test_student and not self.is_test_student:
                raise ValidationError('A test user is expected to remain a test user.')

        # Enforce unique constraint
        if self.email == '':
            self.email = None

        if isinstance(self.email, str):
            self.email = self.email.lower()
        if isinstance(self.username, str):
            self.username = self.username.lower()

        super(User, self).save(*args, **kwargs)


@receiver(models.signals.post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Create matching preferences whenever a user object is created."""
    if created:
        Preferences.objects.create(user=instance)


@receiver(models.signals.post_delete, sender=User)
def auto_delete_feedback_file_on_user_delete(sender, instance, **kwargs):
    """Deletes feedback file from filesystem when corresponding `User` object is deleted."""
    if instance.feedback_file:
        if os.path.isfile(instance.feedback_file.path):
            os.remove(instance.feedback_file.path)


@receiver(models.signals.post_delete, sender=User)
def delete_dangling_files(sender, instance, **kwargs):
    """Deletes FileContext instances which are only of interest to the deleted user."""
    for f in FileContext.objects.filter(author=instance):
        if f.cascade_from_user(instance):
            f.delete()


class Preferences(models.Model):
    """Preferences.

    Describes the preferences of a user:
    - show_format_tutorial: whether or not to show the assignment format tutorial.
    - grade_notifications: whether or not to receive grade notifications via email.
    - comment_notifications: whether or not to receive comment notifications via email.
    - upcoming_deadline_notifications: whether or not to receive upcoming deadline notifications via email.
    - hide_version_alert: latest version number for which a version alert has been dismissed.
    """
    DAILY = 'd'
    WEEKLY = 'w'
    PUSH = 'p'
    OFF = 'o'
    FREQUENCIES = (
        (DAILY, 'd'),
        (WEEKLY, 'w'),
        (PUSH, 'p'),
        (OFF, 'o'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True
    )
    # QUESTION: are these valid defaults?
    new_grade_notifications = models.TextField(
        max_length=1,
        choices=FREQUENCIES,
        default=PUSH,
    )
    new_comment_notifications = models.TextField(
        max_length=1,
        choices=FREQUENCIES,
        default=DAILY,
    )
    new_assignment_notifications = models.TextField(
        max_length=1,
        choices=FREQUENCIES,
        default=WEEKLY,
    )
    new_course_notifications = models.TextField(
        max_length=1,
        choices=FREQUENCIES,
        default=WEEKLY,
    )
    new_entry_notifications = models.TextField(
        max_length=1,
        choices=FREQUENCIES,
        default=DAILY,
    )
    new_preset_node_notifications = models.TextField(
        max_length=1,
        choices=FREQUENCIES,
        default=DAILY,
    )
    upcoming_deadline_notifications = models.BooleanField(
        default=True
    )
    show_format_tutorial = models.BooleanField(
        default=True
    )
    auto_select_ungraded_entry = models.BooleanField(
        default=True
    )
    auto_proceed_next_journal = models.BooleanField(
        default=False
    )
    hide_version_alert = models.TextField(
        max_length=20,
        null=True,
    )
    SAVE = 's'
    PUBLISH = 'p'
    GRADE_BUTTON_OPTIONS = (
        (SAVE, 's'),
        (PUBLISH, 'p'),
    )
    grade_button_setting = models.TextField(
        max_length=1,
        choices=GRADE_BUTTON_OPTIONS,
        default=PUBLISH,
    )
    PUBLISH_AND_PUBLISH_GRADE = 'g'
    COMMENT_SEND_BUTTON_OPTIONS = (
        (SAVE, 's'),
        (PUBLISH, 'p'),
        (PUBLISH_AND_PUBLISH_GRADE, 'g'),
    )
    comment_button_setting = models.TextField(
        max_length=2,
        choices=COMMENT_SEND_BUTTON_OPTIONS,
        default=SAVE,
    )

    def to_string(self, user=None):
        return "Preferences"


class Notification(models.Model):
    NEW_COMMENT = 'comm'
    NEW_ASSIGNMENT = 'assi'
    NEW_COURSE = 'cour'
    NEW_GRADE = 'grad'
    NEW_ENTRY = 'entr'
    NEW_PRESET_NODE = 'prst'
    # UPCOMING_DEADLINE = 'up_d'
    TYPES = {
        NEW_COURSE: {
            'name': 'new_course_notifications',
            'content': {
                'heading': 'New course',
                'main_content': 'You were added to a course.',
                'extra_content': None,
                'button_text': 'View Course',
            },
            'plural': 'You were added to {} new courses.',
            'singular': 'You were added to a new course.',
        },
        NEW_ASSIGNMENT: {
            'name': 'new_assignment_notifications',
            'content': {
                'heading': 'New assignment',
                'main_content': 'Your teacher published a new assignment.',
                'extra_content': None,
                'button_text': 'View Assignment',
            },
            'plural': 'You were added to {} new assignments.',
            'singular': 'You were added to a new assignment.',
        },
        NEW_PRESET_NODE: {
            'name': 'new_preset_node_notifications',
            'content': {
                'heading': 'Your timeline is updated',
                'main_content': 'A new node was added to your timeline.',
                'extra_content': None,
                'button_text': 'View Node',
            },
            'plural': '{} new nodes were added to your timeline.',
            'singular': 'A new node was added to your timeline.',
        },
        NEW_ENTRY: {
            'name': 'new_entry_notifications',
            'content': {
                'heading': 'New entry',
                'main_content': 'Someone posted a new entry in a journal.',
                'extra_content': None,
                'button_text': 'View Entry',
            },
            'plural': '{} new entries were posted.',
            'singular': 'A new entry was posted.',
        },
        NEW_GRADE: {
            'name': 'new_grade_notifications',
            'content': {
                'heading': 'New grade',
                'main_content': 'You have received a new grade on a journal.',
                'extra_content': None,
                'button_text': 'View Grade',
            },
            'plural': 'You received {} new grades.',
            'singular': 'You received a new grade.',
        },
        NEW_COMMENT: {
            'name': 'new_comment_notifications',
            'content': {
                'heading': 'New comment',
                'main_content': 'You have received a new comment on a journal.',
                'extra_content': None,
                'button_text': 'View Comment',
            },
            'plural': '{} new comments were posted.',
            'singular': 'A new comment was posted.',
        },
        # UPCOMING_DEADLINE: {
        #     'name': 'upcoming_deadline_notifications',
        # },
    }

    type = models.TextField(
        max_length=4,
        choices=((type, dic['name']) for type, dic in TYPES.items()),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    url = models.TextField()
    message = models.TextField()
    sent = models.BooleanField(
        default=False
    )
    creation_date = models.DateTimeField(
        editable=False,
        auto_now_add=True
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super(Notification, self).save(*args, **kwargs)

        if is_new:
            # Send notification on creation if user preference is set to push
            if getattr(self.user.preferences, Notification.TYPES[self.type]['name']) == Preferences.PUSH:
                send_push_notification.delay(self.pk)


class Course(models.Model):
    """Course.

    A Course entity has the following features:
    - name: name of the course.
    - author: the creator of the course.
    - abbreviation: a max three letter abbreviation of the course name.
    - startdate: the date that the course starts.
    - active_lti_id: (optional) the active VLE id of the course linked through LTI which receives grade updates.
    - lti_id_set: (optional) the set of VLE lti_id_set which permit basic access.
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

    active_lti_id = models.TextField(
        null=True,
        unique=True,
        blank=True,
    )

    # These LTI assignments belong to this course.
    assignment_lti_id_set = ArrayField(
        models.TextField(),
        default=list,
    )

    def add_assignment_lti_id(self, lti_id):
        if lti_id not in self.assignment_lti_id_set:
            self.assignment_lti_id_set.append(lti_id)

    def has_lti_link(self):
        return self.active_lti_id is not None

    def to_string(self, user=None):
        if user is None:
            return "Course"
        if not user.can_view(self):
            return "Course"

        return self.name + " (" + str(self.pk) + ")"


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
    )

    class Meta:
        """Meta data for the model: unique_together."""
        unique_together = ('lti_id', 'course')

    def to_string(self, user=None):
        if user is None:
            return "Group"
        if not user.can_view(self.course):
            return "Group"
        return "{} ({})".format(self.name, self.pk)


class Role(models.Model):
    """Role.

    A complete overview of the role requirements can be found here:
    https://docs.google.com/spreadsheets/d/1M7KnEKL3cG9PMWfQi9HIpRJ5xUMou4Y2plnRgke--Tk

    A role defines the permissions of a user group within a course.
    - name: name of the role
    - list of permissions (can_...)
    """
    GENERAL_PERMISSIONS = [
        'can_edit_institute_details',
        'can_add_course'
    ]
    COURSE_PERMISSIONS = [
        'can_edit_course_details',
        'can_delete_course',

        'can_edit_course_roles',
        'can_view_course_users',
        'can_add_course_users',
        'can_delete_course_users',

        'can_add_course_user_group',
        'can_delete_course_user_group',
        'can_edit_course_user_group',

        'can_add_assignment',
        'can_delete_assignment',
    ]
    ASSIGNMENT_PERMISSIONS = [
        'can_edit_assignment',
        'can_grade',
        'can_publish_grades',

        'can_view_all_journals',
        'can_view_unpublished_assignment',
        'can_view_grade_history',

        'can_manage_journals',
        'can_have_journal',

        'can_comment',
        'can_edit_staff_comment',
    ]
    PERMISSIONS = COURSE_PERMISSIONS + ASSIGNMENT_PERMISSIONS

    name = models.TextField()

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    can_edit_course_details = models.BooleanField(default=False)
    can_delete_course = models.BooleanField(default=False)
    can_edit_course_roles = models.BooleanField(default=False)
    can_view_course_users = models.BooleanField(default=False)
    can_add_course_users = models.BooleanField(default=False)
    can_delete_course_users = models.BooleanField(default=False)
    can_add_course_user_group = models.BooleanField(default=False)
    can_delete_course_user_group = models.BooleanField(default=False)
    can_edit_course_user_group = models.BooleanField(default=False)
    can_add_assignment = models.BooleanField(default=False)
    can_delete_assignment = models.BooleanField(default=False)

    can_edit_assignment = models.BooleanField(default=False)
    can_manage_journals = models.BooleanField(default=False)
    can_view_all_journals = models.BooleanField(default=False)
    can_grade = models.BooleanField(default=False)
    can_publish_grades = models.BooleanField(default=False)
    can_view_grade_history = models.BooleanField(default=False)
    can_have_journal = models.BooleanField(default=False)
    can_comment = models.BooleanField(default=False)
    can_edit_staff_comment = models.BooleanField(default=False)
    can_view_unpublished_assignment = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.can_add_course_users and not self.can_view_course_users:
            raise ValidationError('A user needs to be able to view course users in order to add them.')

        if self.can_delete_course_users and not self.can_view_course_users:
            raise ValidationError('A user needs to be able to view course users in order to remove them.')

        if self.can_edit_course_user_group and not self.can_view_course_users:
            raise ValidationError('A user needs to be able to view course users in order to manage user groups.')

        if self.can_view_all_journals and self.can_have_journal:
            raise ValidationError('Teaching staff is not allowed to have a journal in their own course.')

        if self.can_grade and not self.can_view_all_journals:
            raise ValidationError('A user needs to be able to view journals in order to grade them.')

        if self.can_publish_grades and not (self.can_view_all_journals and self.can_grade):
            raise ValidationError('A user needs to be able to view and grade journals in order to publish grades.')

        if self.can_view_grade_history and not (self.can_view_all_journals and self.can_grade):
            raise ValidationError('A user needs to be able to view and grade journals in order to see a history\
                                   of grades.')

        if self.can_comment and not (self.can_view_all_journals or self.can_have_journal):
            raise ValidationError('A user requires a journal to comment on.')

        if self.can_edit_staff_comment and self.can_have_journal:
            raise ValidationError('Users who can edit staff comments are not allowed to have a journal themselves.')

        if self.can_edit_staff_comment and not self.can_comment:
            raise ValidationError('A user needs to be able to comment in order to edit other comments.')

        super(Role, self).save(*args, **kwargs)

    def to_string(self, user=None):
        if user is None:
            return "Role"
        if not user.can_view(self.course):
            return "Role"

        return "{} ({})".format(self.name, self.pk)

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
        on_delete=models.CASCADE,
        related_name='role',
    )
    groups = models.ManyToManyField(
        Group,
        default=None,
    )

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        notify_user = kwargs.pop('notify_user', True)
        super(Participation, self).save(*args, **kwargs)

        # Instance is being created (not modified)
        if is_new:
            existing = AssignmentParticipation.objects.filter(user=self.user).values('assignment')
            for assignment in Assignment.objects.filter(courses__in=[self.course]).exclude(pk__in=existing):
                AssignmentParticipation.objects.create(assignment=assignment, user=self.user)
            if notify_user:
                Notification.objects.create(
                    type=Notification.NEW_COURSE,
                    user=self.user,
                    url=gen_url(course=self.course, user=self.user)
                )

    class Meta:
        """Meta data for the model: unique_together."""

        unique_together = ('user', 'course',)

    def to_string(self, user=None):
        if user is None:
            return "Participation"
        if not user.can_view(self.course):
            return "Participation"

        return "user: {}, course: {}, role: {}".format(
            self.user.to_string(user=user), self.course.to_string(user=user), self.role.to_string(user=user))


class Assignment(models.Model):
    """Assignment.

    An Assignment entity has the following features:
    - name: name of the assignment.
    - description: description for the assignment.
    - courses: a foreign key linked to the courses this assignment
    is part of.
    - format: a one-to-one key linked to the format this assignment
    holds. The format determines how a students' journal is structured.
    - active_lti_id: (optional) the active VLE id of the assignment linked through LTI which receives grade updates.
    - lti_id_set: (optional) the set of VLE assignment lti_id_set which permit basic access.
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
    is_published = models.BooleanField(default=False)
    points_possible = models.IntegerField(
        'points_possible',
        default=10
    )
    unlock_date = models.DateTimeField(
        'unlock_date',
        null=True,
        blank=True
    )
    due_date = models.DateTimeField(
        'due_date',
        null=True,
        blank=True
    )
    lock_date = models.DateTimeField(
        'lock_date',
        null=True,
        blank=True
    )
    courses = models.ManyToManyField(Course)
    assigned_groups = models.ManyToManyField(Group)

    format = models.OneToOneField(
        'Format',
        on_delete=models.CASCADE
    )

    active_lti_id = models.TextField(
        null=True,
        unique=True,
        blank=True,
    )
    lti_id_set = ArrayField(
        models.TextField(),
        default=list,
    )

    is_group_assignment = models.BooleanField(default=False)
    remove_grade_upon_leaving_group = models.BooleanField(default=False)
    can_set_journal_name = models.BooleanField(default=False)
    can_set_journal_image = models.BooleanField(default=False)
    can_lock_journal = models.BooleanField(default=False)

    def has_lti_link(self):
        return self.active_lti_id is not None

    def is_locked(self):
        return self.unlock_date and self.unlock_date > now() or self.lock_date and self.lock_date < now()

    def add_course(self, course):
        if not self.courses.filter(pk=course.pk).exists():
            self.courses.add(course)
            existing = AssignmentParticipation.objects.filter(assignment=self).values('user')
            for user in course.users.exclude(pk__in=existing):
                AssignmentParticipation.objects.create(assignment=self, user=user)

    def save(self, *args, **kwargs):
        self.description = sanitization.strip_script_tags(self.description)

        active_lti_id_modified = False
        type_changed = False

        # Instance is being created (not modified)
        if self._state.adding:
            active_lti_id_modified = self.active_lti_id is not None
        else:
            if self.pk:
                pre_save = Assignment.objects.get(pk=self.pk)
                active_lti_id_modified = pre_save.active_lti_id != self.active_lti_id

                if pre_save.is_published and not self.is_published and pre_save.has_entries():
                    raise ValidationError('Cannot unpublish an assignment that has entries.')
                if pre_save.is_group_assignment != self.is_group_assignment:
                    if pre_save.has_entries():
                        raise ValidationError('Cannot change the type of an assignment that has entries.')
                    else:
                        type_changed = True
            # A copy is being made of the original instance
            else:
                self.active_lti_id = None
                self.lti_id_set = []

        if active_lti_id_modified:
            # Reset all sourcedid if the active lti id is updated.
            AssignmentParticipation.objects.filter(assignment=self).update(sourcedid=None, grade_url=None)

            if self.active_lti_id is not None and self.active_lti_id not in self.lti_id_set:
                self.lti_id_set.append(self.active_lti_id)

            other_assignments_with_lti_id_set = Assignment.objects.filter(
                lti_id_set__contains=[self.active_lti_id]).exclude(pk=self.pk)
            if other_assignments_with_lti_id_set.exists():
                raise ValidationError(
                    "An lti_id should be unique, and only part of a single assignment's lti_id_set.")

        is_new = self._state.adding
        if not self._state.adding and self.pk:
            old_publish = Assignment.objects.get(pk=self.pk).is_published
        else:
            old_publish = self.is_published

        super(Assignment, self).save(*args, **kwargs)

        if type_changed:
            # Delete all journals if assignment type changes
            Journal.objects.filter(assignment=self).delete()

        if type_changed or not old_publish and self.is_published:
            # Create journals if it is changed to (or published as) a non group assignment
            if not self.is_group_assignment:
                users = self.courses.values('users').distinct()
                if is_new:
                    existing = []
                    for user in users:
                        AssignmentParticipation.objects.create(assignment=self, user=user['users'])
                else:
                    existing = Journal.objects.filter(assignment=self).values('authors__user')
                for user in users.exclude(pk__in=existing):
                    ap = AssignmentParticipation.objects.get_or_create(
                        assignment=self, user=User.objects.get(pk=user['users']))[0]
                    if not Journal.objects.filter(assignment=self, authors__in=[ap]).exists():
                        journal = Journal.objects.create(assignment=self)
                        journal.authors.add(ap)

        # Send notifications once an assignment is published
        if (is_new or not old_publish) and self.is_published:
            for ap in AssignmentParticipation.objects.filter(assignment=self):
                if ap.user.has_permission('can_have_journal', self):
                    Notification.objects.create(
                        type=Notification.NEW_ASSIGNMENT,
                        user=ap.user,
                        url=gen_url(assignment=self, user=ap.user)
                    )
        # Delete notifications if a teacher unpublishes an assignment after publishing
        elif old_publish and not self.is_published:
            Notification.objects.filter(
                type=Notification.NEW_ASSIGNMENT,
                url__contains='Assignment/{}'.format(self.pk)
            ).delete()

    def get_active_lti_course(self):
        """"Query for retrieving the course which matches the active lti id of the assignment."""
        courses = self.courses.filter(assignment_lti_id_set__contains=[self.active_lti_id])
        return courses.first()

    def get_active_course(self, user):
        """"Query for retrieving the course which is most relevant to the assignment."""
        # If there are no courses connected, return none
        if not self.courses:
            return None

        # Get matching LTI course if possible
        active_courses = self.courses.filter(assignment_lti_id_set__contains=[self.active_lti_id])
        for course in active_courses:
            if user.can_view(course):
                return course

        # Else get course that started the most recent
        most_recent_courses = self.courses.filter(startdate__lte=timezone.now()).order_by('-startdate')
        for course in most_recent_courses:
            if user.can_view(course):
                return course

        # Else get the course that starts the soonest
        starts_first_courses = self.courses.filter(startdate__gt=timezone.now()).order_by('startdate')
        for course in starts_first_courses:
            if user.can_view(course):
                return course

        # Else get the first course without start date
        for course in self.courses.filter(startdate__isnull=True).order_by('pk'):
            if user.can_view(course):
                return course

        return None

    def get_lti_id_from_course(self, course):
        """Gets the assignment lti_id that belongs to the course assignment pair if it exists."""
        if not isinstance(course, Course):
            raise VLEProgrammingError("Expected instance of type Course.")

        intersection = list(set(self.lti_id_set).intersection(course.assignment_lti_id_set))
        return intersection[0] if intersection else None

    def set_active_lti_course(self, course):
        active_lti_id = self.get_lti_id_from_course(course)
        if active_lti_id:
            self.active_lti_id = active_lti_id
            self.save()
        else:
            raise VLEBadRequest("This course is not connected to the assignment")

    def add_lti_id(self, lti_id, course):
        if self.get_lti_id_from_course(course) is not None:
            raise VLEBadRequest('Assignment already used in course.')
        # Update assignment
        self.active_lti_id = lti_id
        if not self.courses.filter(pk=course.pk).exists():
            self.courses.add(course)
        self.save()
        # Update course
        course.add_assignment_lti_id(lti_id)
        course.save()

    def has_entries(self):
        return Entry.objects.filter(node__journal__assignment=self).exists()

    def to_string(self, user=None):
        if user is None:
            return "Assignment"
        if not user.can_view(self):
            return "Assignment"

        return "{} ({})".format(self.name, self.pk)


class AssignmentParticipation(models.Model):
    """AssignmentParticipation

    A user that is connected to an assignment
    this can then be used as a participation for a journal
    """

    journal = models.ForeignKey(
        'Journal',
        on_delete=models.SET_NULL,
        related_name='authors',
        null=True,
    )

    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )

    assignment = models.ForeignKey(
        'Assignment',
        on_delete=models.CASCADE
    )

    sourcedid = models.TextField(null=True)
    grade_url = models.TextField(null=True)

    def needs_lti_link(self):
        return self.assignment.active_lti_id is not None and self.sourcedid is None

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super(AssignmentParticipation, self).save(*args, **kwargs)

        # Instance is being created (not modified)
        if is_new:
            if self.assignment.is_published and not self.assignment.is_group_assignment and not self.journal:
                journal = Journal.objects.create(assignment=self.assignment)
                journal.authors.add(self)

    def to_string(self, user=None):
        if user is None or not user.can_view(self.assignment):
            return "Participant"

        return "{0} in {1}".format(self.user.username, self.assignment.name)

    class Meta:
        """A class for meta data.

        - unique_together: assignment and author must be unique together.
        """
        unique_together = ('assignment', 'user',)


class JournalManager(models.Manager):
    def get_queryset(self):
        """Filter on only journals with can_have_journal and that are in the assigned to groups"""
        query = super(JournalManager, self).get_queryset()
        return query.annotate(
            p_user=F('assignment__courses__participation__user'),
            p_group=F('assignment__courses__participation__groups'),
            can_have_journal=F('assignment__courses__participation__role__can_have_journal')
        ).filter(
            # Filter on only can_have_journal
            Q(assignment__is_group_assignment=True) | Q(p_user__in=F('authors__user'), can_have_journal=True),
        ).filter(
            # Filter on only assigned groups
            Q(assignment__is_group_assignment=True) | Q(p_group__in=F('assignment__assigned_groups')) |
            Q(assignment__assigned_groups=None),
        ).annotate(
            # Reset group, as that could lead to distinct not working
            p_group=F('pk'), p_user=F('pk'), can_have_journal=F('pk'),
        ).distinct().order_by('pk')


class Journal(models.Model):
    """Journal.

    A journal is a collection of Nodes that holds the student's
    entries, deadlines and more. It contains the following:
    - assignment: a foreign key linked to an assignment.
    - user: a foreign key linked to a user.
    """
    UNLIMITED = 0
    all_objects = models.Manager()
    objects = JournalManager()

    assignment = models.ForeignKey(
        'Assignment',
        on_delete=models.CASCADE,
    )

    bonus_points = models.FloatField(
        default=0,
    )

    author_limit = models.IntegerField(
        default=1
    )

    name = models.TextField(
        null=True,
    )

    image = models.TextField(
        null=True,
    )

    locked = models.BooleanField(
        default=False,
    )

    LMS_grade = models.IntegerField(
        default=0,
    )

    # NOTE: Any suggestions for a clear warning msg for all cases?
    outdated_link_warning_msg = 'This journal has an outdated LMS uplink and can no longer be edited. Visit  ' \
        + 'eJournal from an updated LMS connection.'

    def get_grade(self):
        return round(self.bonus_points + (
            self.node_set.filter(entry__grade__published=True)
            .values('entry__grade__grade')
            .aggregate(Sum('entry__grade__grade'))['entry__grade__grade__sum'] or 0), 2)

    def needs_lti_link(self):
        return any(author.needs_lti_link() for author in self.authors.all())

    def get_name(self):
        if self.name is not None:
            return self.name

        return self.get_full_names()

    def get_image(self):
        if self.image:
            return self.image

        user_with_pic = self.authors.all().exclude(user__profile_picture=settings.DEFAULT_PROFILE_PICTURE).first()
        if user_with_pic is not None:
            return user_with_pic.user.profile_picture

        return settings.DEFAULT_PROFILE_PICTURE

    def get_full_names(self):
        return ', '.join(self.authors.values_list('user__full_name', flat=True))

    def reset(self):
        Node.objects.filter(journal=self).delete()

        preset_nodes = self.assignment.format.presetnode_set.all()
        for preset_node in preset_nodes:
            Node.objects.create(type=preset_node.type, journal=self, preset=preset_node)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if self.name is None:
            if self.assignment.is_group_assignment:
                self.name = 'Journal {}'.format(Journal.objects.filter(assignment=self.assignment).count() + 1)
        super(Journal, self).save(*args, **kwargs)
        # On create add preset nodes
        if is_new:
            preset_nodes = self.assignment.format.presetnode_set.all()
            for preset_node in preset_nodes:
                Node.objects.create(type=preset_node.type, journal=self, preset=preset_node)

    @property
    def published_nodes(self):
        return self.node_set.filter(entry__grade__published=True).order_by('entry__grade__creation_date')

    @property
    def unpublished_nodes(self):
        return self.node_set.filter(
            Q(entry__grade__isnull=True) | Q(entry__grade__published=False),
            entry__isnull=False).order_by('entry__last_edited')

    def to_string(self, user=None):
        if user is None:
            return "Journal"
        if not user.can_view(self):
            return "Journal"

        return "the {0} journal of {1}".format(self.assignment.name, self.get_full_names())


class Node(models.Model):
    """Node.

    The Node is an Timeline component.
    It can represent many things.
    There are three types of nodes:
    -Progress
        A node that merely is a deadline,
        and contains no entry. This deadline
        contains a 'target point amount'
        which should be reached before the
        due date has passed.
        This type of node has to be predefined in
        the Format. In the Format it is assigned a
        due date and a 'target point amount'.
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
        the Format. In the Format it is assigned an
        unlock/lock date, a due date and a 'forced template'.
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
        on_delete=models.SET_NULL,
    )

    def to_string(self, user=None):
        return "Node"


class Format(models.Model):
    """Format.

    Format of a journal.
    The format determines how a students' journal is structured.
    See PresetNodes for attached 'default' nodes.
    """

    def to_string(self, user=None):
        return "Format"


class PresetNode(models.Model):
    """PresetNode.

    A preset node is a node that has been pre-defined by the teacher.
    It contains the following features:
    - description: user defined text description of the preset node.
    - type: the type of the preset node (progress or entrydeadline node).
    - unlock_date: the date from which the preset node can be filled in.
    - due_date: the due date for this preset node.
    - lock_date: the date after which the preset node can no longer be fulfilled.
    - forced_template: the template for this preset node - null if PROGRESS node.
    - format: a foreign key linked to a format.
    """

    TYPES = (
        (Node.PROGRESS, 'progress'),
        (Node.ENTRYDEADLINE, 'entrydeadline'),
    )

    description = models.TextField(
        null=True,
    )

    type = models.TextField(
        max_length=4,
        choices=TYPES,
    )

    target = models.FloatField(
        null=True,
    )

    unlock_date = models.DateTimeField(
        null=True
    )

    due_date = models.DateTimeField()

    lock_date = models.DateTimeField(
        null=True
    )

    forced_template = models.ForeignKey(
        'Template',
        on_delete=models.SET_NULL,
        null=True,
    )

    format = models.ForeignKey(
        'Format',
        on_delete=models.CASCADE
    )

    def is_locked(self):
        return self.unlock_date is not None and self.unlock_date > now() or self.lock_date and self.lock_date < now()

    def to_string(self, user=None):
        return "PresetNode"


class Entry(models.Model):
    """Entry.

    An Entry has the following features:
    - creation_date: the date and time when the entry was posted.
    - last_edited: the date and time when the etry was last edited
    """
    NEEDS_SUBMISSION = 'Submission needs to be sent to VLE'
    SENT_SUBMISSION = 'Submission is successfully received by VLE'
    NEEDS_GRADE_PASSBACK = 'Grade needs to be sent to VLE'
    LINK_COMPLETE = 'Everything is sent to VLE'
    TYPES = (
        (NEEDS_SUBMISSION, 'entry_submission'),
        (SENT_SUBMISSION, 'entry_submitted'),
        (NEEDS_GRADE_PASSBACK, 'grade_submission'),
        (LINK_COMPLETE, 'done'),
    )

    # TODO Should not be nullable
    template = models.ForeignKey(
        'Template',
        on_delete=models.SET_NULL,
        null=True,
    )
    grade = models.ForeignKey(
        'Grade',
        on_delete=models.SET_NULL,
        related_name='+',
        null=True,
    )

    creation_date = models.DateTimeField(editable=False)
    author = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        related_name='entries',
        null=True,
    )

    last_edited = models.DateTimeField()
    last_edited_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        related_name='last_edited_entries',
        null=True,
    )

    vle_coupling = models.TextField(
        default=NEEDS_SUBMISSION,
        choices=TYPES,
    )

    def is_locked(self):
        return (self.node.preset and self.node.preset.is_locked()) or self.node.journal.assignment.is_locked()

    def is_editable(self):
        return not self.is_graded() and not self.is_locked()

    def is_graded(self):
        return not (self.grade is None or self.grade.grade is None)

    def save(self, *args, **kwargs):
        if not self.pk:
            now = timezone.now()
            self.creation_date = now
            self.last_edited = now

            for user in permissions.get_supervisors_of(self.node.journal):
                Notification.objects.create(
                    type=Notification.NEW_ENTRY,
                    user=user,
                    url=gen_url(node=self.node, user=user)
                )

        return super(Entry, self).save(*args, **kwargs)

    def to_string(self, user=None):
        return "Entry"


class Grade(models.Model):
    """Grade.

    Used to keep a history of grades.
    """
    entry = models.ForeignKey(
        'Entry',
        editable=False,
        related_name='+',
        on_delete=models.CASCADE
    )
    grade = models.FloatField(
        null=True,
        editable=False
    )
    published = models.BooleanField(
        default=False,
        editable=False
    )
    creation_date = models.DateTimeField(
        editable=False,
        auto_now_add=True
    )
    author = models.ForeignKey(
        'User',
        null=True,
        editable=False,
        on_delete=models.SET_NULL
    )

    def save(self, *args, **kwargs):
        self.creation_date = timezone.now()
        super(Grade, self).save(*args, **kwargs)

        if self.published:
            for author in self.entry.node.journal.authors.all():
                Notification.objects.create(
                    type=Notification.NEW_GRADE,
                    user=author.user,
                    url=gen_url(node=self.entry.node, user=author.user)
                )

    def to_string(self, user=None):
        return "Grade"


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

    def to_string(self, user=None):
        return self.name + " is on " + self.count


class Template(models.Model):
    """Template.

    A template for an Entry.
    """

    name = models.TextField()

    format = models.ForeignKey(
        'Format',
        on_delete=models.CASCADE
    )

    preset_only = models.BooleanField(
        default=False
    )

    archived = models.BooleanField(
        default=False
    )

    def to_string(self, user=None):
        return "Template"


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
    DATE = 'd'
    DATETIME = 'dt'
    SELECTION = 's'
    FILE_TYPES = [PDF, FILE, IMG]
    TYPES = (
        (TEXT, 'text'),
        (RICH_TEXT, 'rich text'),
        (IMG, 'img'),
        (PDF, 'pdf'),
        (FILE, 'file'),
        (VIDEO, 'vid'),
        (URL, 'url'),
        (DATE, 'date'),
        (DATETIME, 'datetime'),
        (SELECTION, 'selection')
    )
    type = models.TextField(
        max_length=4,
        choices=TYPES,
        default=TEXT,
    )
    title = models.TextField()
    description = models.TextField(
        null=True
    )
    options = models.TextField(
        null=True
    )
    location = models.IntegerField()
    template = models.ForeignKey(
        'Template',
        on_delete=models.CASCADE
    )
    required = models.BooleanField()

    def to_string(self, user=None):
        return "{} ({})".format(self.title, self.id)


class Content(models.Model):
    """Content.

    Defines the content of an Entry
    """

    entry = models.ForeignKey(
        'Entry',
        on_delete=models.CASCADE
    )
    # Question: Why can this be null?
    field = models.ForeignKey(
        'Field',
        on_delete=models.SET_NULL,
        null=True
    )
    data = models.TextField(
        null=True
    )

    def save(self, *args, **kwargs):
        self.data = sanitization.strip_script_tags(self.data)

        return super(Content, self).save(*args, **kwargs)

    def to_string(self, user=None):
        return "Content"


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
    published = models.BooleanField(
        default=True
    )
    creation_date = models.DateTimeField(editable=False)
    last_edited = models.DateTimeField()
    last_edited_by = models.ForeignKey(
        'User',
        related_name='last_edited_by',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def can_edit(self, user):
        """
        Returns whether the given user is allowed to edit the comment:
            - Has to be the author or super_user
            - Otheriwse has to have the permission 'can_edit_staff_comment' and edit a non journal author comment.
              Because staff members can't have a journal themselves, checking if the author is not the owner of the
              journal the comment is posted to suffices.
        Raises a VLEProgramming error when misused.
        """
        if not isinstance(user, User):
            raise VLEProgrammingError("Expected instance of type User.")

        if user == self.author or user.is_superuser:
            return True

        return user.has_permission('can_edit_staff_comment', self.entry.node.journal.assignment) and \
            not self.entry.node.journal.authors.filter(user=self.author).exists()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.creation_date = timezone.now()
            if self.published:
                if self.entry.node.journal.authors.filter(user=self.author).exists():  # student comment
                    for user in permissions.get_supervisors_of(self.entry.node.journal):
                        Notification.objects.create(
                            type=Notification.NEW_COMMENT,
                            user=user,
                            url=gen_url(node=self.entry.node, user=user)
                        )
                else:  # supervisor comment
                    for author in self.entry.node.journal.authors.all():
                        Notification.objects.create(
                            type=Notification.NEW_COMMENT,
                            user=author.user,
                            url=gen_url(node=self.entry.node, user=author.user)
                        )
        self.last_edited = timezone.now()
        self.text = sanitization.strip_script_tags(self.text)
        return super(Comment, self).save(*args, **kwargs)

    def to_string(self, user=None):
        return "Comment"
