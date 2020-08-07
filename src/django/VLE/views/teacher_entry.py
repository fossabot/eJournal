"""
teacher_entry.py.

In this file are all the entry api requests.
"""
from rest_framework import viewsets

import VLE.factory as factory
import VLE.serializers as serialize
import VLE.utils.entry_utils as entry_utils
import VLE.utils.file_handling as file_handling
import VLE.utils.generic_utils as utils
import VLE.utils.responses as response
from VLE.models import Assignment, Entry, Field, FileContext, TeacherEntry, Template
from VLE.utils import grading


class TeacherEntryView(viewsets.ViewSet):
    """Entry view.

    This class creates the following api paths:
    POST /teacherentries/ -- create a new entry
    PATCH /teacherentries/<pk> -- partially update an entry
    """

    def create(self, request):
        """Create a new teacher entry.

        Deletes remaining temporary user files if successful.

        Arguments:
        request -- the request that was sent with
            assignment_id -- the assignment id to which the entry belongs
            template_id -- the template id to create the entry with
            content -- the list of {tag, data} tuples to bind data to a template field.
            journal_ids -- the journal ids of all journals to which the entry should be added
        """
        assignment_id, template_id, content_list, journal_ids = utils.required_params(
            request.data, "assignment_id", "template_id", "content", "journal_ids")

        assignment = Assignment.objects.get(pk=assignment_id)
        template = Template.objects.get(pk=template_id)

        request.user.check_permission('can_post_teacher_entries', assignment)

        # Check if the template is available. Preset-only templates are also available for teacher entries.
        if not assignment.format.template_set.filter(archived=False, pk=template.pk).exists():
            return response.forbidden('Entry template is not available.')

        entry_utils.check_fields(template, content_list)

        teacher_entry = factory.make_teacher_entry(template)

        try:
            files_to_establish = []
            for content in content_list:
                field_id, = utils.required_typed_params(content, (int, 'id'))
                field = Field.objects.get(pk=field_id)
                data, = utils.required_params(content, 'data')
                if data is not None and field.type == field.FILE:
                    data, = utils.required_typed_params(data, (str, 'id'))

                created_content = factory.make_content(teacher_entry, data, field)

                if field.type == field.FILE:
                    if field.required and not data:
                        raise FileContext.DoesNotExist
                    if data:
                        files_to_establish.append(
                            (FileContext.objects.get(pk=int(data)), created_content))

                # Establish all files in the rich text editor
                if field.type == Field.RICH_TEXT:
                    files_to_establish += [(f, created_content) for f in file_handling.get_files_from_rich_text(data)]

        # If anything fails during creation of the teacher_entry, delete the teacher_entry
        except Exception as e:
            teacher_entry.delete()

            # If it is a file issue, raise with propper response, else respond with the exception that was raised
            if type(e) == FileContext.DoesNotExist:
                return response.bad_request('One of your files was not correctly uploaded, please try again.')
            else:
                raise e

        for (file, content) in files_to_establish:
            file_handling.establish_file(
                request.user, file.access_id, content=content, in_rich_text=content.field.type == Field.RICH_TEXT)

        # Delete old user files
        file_handling.remove_unused_user_files(request.user)

        # TODO TEACHERENTRY: Add entry to all student journals along with specified grade.

        return response.created({
            'teacher_entry': serialize.TeacherEntrySerializer(teacher_entry).data
        })

    def partial_update(self, request, *args, **kwargs):
        """Update an existing teacher entry.

        Arguments:


        Returns:


        """
        content_list, = utils.required_params(request.data, 'content')
        entry_id, = utils.required_typed_params(kwargs, (int, 'pk'))
        entry = Entry.objects.get(pk=entry_id)
        journal = entry.node.journal
        assignment = journal.assignment

        if assignment.is_locked():
            return response.forbidden('The assignment is locked, entries can no longer be edited/changed.')
        request.user.check_permission('can_have_journal', assignment)
        if not (journal.authors.filter(user=request.user).exists() or request.user.is_superuser):
            return response.forbidden('You are not allowed to edit someone else\'s entry.')
        if entry.is_graded():
            return response.bad_request('You are not allowed to edit graded entries.')
        if entry.is_locked():
            return response.bad_request('You are not allowed to edit locked entries.')
        if len(journal.needs_lti_link) > 0:
            return response.forbidden(journal.outdated_link_warning_msg)

        # Check for required fields
        entry_utils.check_fields(entry.template, content_list)

        # Attempt to edit the entries content.
        files_to_establish = []
        for content in content_list:
            field_id, = utils.required_typed_params(content, (int, 'id'))
            data, = utils.required_params(content, 'data')
            field = Field.objects.get(pk=field_id)
            if data is not None and field.type == field.FILE:
                data, = utils.required_typed_params(data, (str, 'id'))

            old_content = entry.content_set.filter(field=field)
            changed = False
            if old_content.exists():
                old_content = old_content.first()
                if old_content.field.pk != field_id:
                    return response.bad_request('The given content does not match the accompanying field type.')
                if not data:
                    old_content.data = None
                    old_content.save()
                    continue

                changed = old_content.data != data
                if changed:
                    entry_utils.patch_entry_content(request.user, entry, old_content, field, data, assignment)
            # If there was no content in this field before, create new content with the new data.
            # This can happen with non-required fields, or when the given data is deleted.
            else:
                old_content = factory.make_content(entry, data, field)
                changed = True

            if changed:
                if field.type == field.FILE:
                    if field.required and not data:
                        raise FileContext.DoesNotExist
                    if data:
                        files_to_establish.append(
                            (FileContext.objects.get(pk=int(data)), old_content))

                # Establish all files in the rich text editor
                if field.type == Field.RICH_TEXT:
                    files_to_establish += [(f, old_content) for f in file_handling.get_files_from_rich_text(data)]

        for (file, content) in files_to_establish:
            file_handling.establish_file(
                request.user, file.access_id, content=content, in_rich_text=content.field.type == Field.RICH_TEXT)

        file_handling.remove_unused_user_files(request.user)
        grading.task_journal_status_to_LMS.delay(journal.pk)
        entry.last_edited_by = request.user
        entry.save()

        return response.success({'entry': serialize.EntrySerializer(entry, context={'user': request.user}).data})

    def destroy(self, request, *args, **kwargs):
        """Delete a teacher entry and all instances of it.

        Arguments:
        request -- request data
        pk -- entry ID

        Returns:
        On failure:
            not found -- when the course does not exist
            unauthorized -- when the user is not logged in
            forbidden -- when the user is not in the course
        On success:
            success -- with a message that the course was deleted
        """
        pk, = utils.required_typed_params(kwargs, (int, 'pk'))

        teacher_entry = TeacherEntry.objects.get(pk=pk)
        assignment = teacher_entry.assignment

        request.user.check_permission('can_have_journal', assignment, 'You are not allowed to post or delete teacher '
                                      'entries.')

        return response.success(description='Successfully deleted teacher entry.')
