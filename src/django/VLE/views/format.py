"""
format.py.

In this file are all the Format api requests.
"""
from rest_framework import viewsets

import VLE.utils.generic_utils as utils
import VLE.utils.responses as response
from VLE.models import Assignment, Field, Group, PresetNode
from VLE.serializers import AssignmentDetailsSerializer, FormatSerializer
from VLE.utils import file_handling


class FormatView(viewsets.ViewSet):
    """Format view.

    This class creates the following api paths:
    GET /formats/ -- gets all the formats
    PATCH /formats/<pk> -- partially update an format
    """

    def retrieve(self, request, pk):
        """Get the format attached to an assignment.

        Arguments:
        request -- the request that was sent
        pk -- the assignment id

        Returns a json string containing the format as well as the
        corresponding assignment name and description.
        """
        assignment = Assignment.objects.get(pk=pk)

        request.user.check_can_view(assignment)
        request.user.check_permission('can_edit_assignment', assignment)

        serializer = FormatSerializer(assignment.format)
        assignment_details = AssignmentDetailsSerializer(assignment, context={'user': request.user})

        return response.success({'format': serializer.data, 'assignment_details': assignment_details.data})

    def partial_update(self, request, pk):
        """Update an existing journal format.

        Arguments:
        request -- request data
            templates -- the list of templates to bind to the format
            presets -- the list of presets to bind to the format
            removed_presets -- presets to be removed
            removed_templates -- templates to be removed
        pk -- assignment ID

        Returns:
        On failure:
            unauthorized -- when the user is not logged in
            not found -- when the assignment does not exist
            forbidden -- User not allowed to edit this assignment
            unauthorized -- when the user is unauthorized to edit the assignment
            bad_request -- when there is invalid data in the request
        On success:
            success -- with the new assignment data

        """
        assignment_details, templates, presets, removed_templates, removed_presets \
            = utils.required_params(request.data, 'assignment_details', 'templates', 'presets',
                                    'removed_templates', 'removed_presets')

        assignment = Assignment.objects.get(pk=pk)
        format = assignment.format

        request.user.check_permission('can_edit_assignment', assignment)

        is_published, can_set_journal_name, can_set_journal_image, can_lock_journal = \
            utils.optional_typed_params(
                assignment_details, (bool, 'is_published'),
                (bool, 'can_set_journal_name'), (bool, 'can_set_journal_image'), (bool, 'can_lock_journal'))

        # Remove data that must not be changed by the serializer
        req_data = assignment_details or {}
        req_data.pop('author', None)

        for key in req_data:
            if req_data[key] == '':
                req_data[key] = None

        # Update the assignment details
        assigned_groups = req_data.pop('assigned_groups', [])
        if len(assigned_groups) > 0:
            assignment.assigned_groups.set([])
            for group in assigned_groups:
                assignment.assigned_groups.add(Group.objects.get(pk=group['id']))
        else:
            assignment.assigned_groups.set([])
        serializer = AssignmentDetailsSerializer(assignment, data=req_data, context={'user': request.user},
                                                 partial=True)
        if not serializer.is_valid():
            return response.bad_request('Invalid assignment data.')
        serializer.save()

        new_ids = utils.update_templates(format, templates)
        utils.update_presets(assignment, presets, new_ids)

        utils.delete_presets(removed_presets)
        utils.archive_templates(removed_templates)

        file_handling.establish_rich_text(request.user, assignment.description, assignment=assignment)
        for field in Field.objects.filter(template__format=format):
            file_handling.establish_rich_text(request.user, field.description, assignment=assignment)
        for node in PresetNode.objects.filter(format=format):
            file_handling.establish_rich_text(request.user, node.description, assignment=assignment)

        file_handling.remove_unused_user_files(request.user)
        serializer = FormatSerializer(format)
        assignment_details = AssignmentDetailsSerializer(assignment, context={'user': request.user})

        return response.success({'format': serializer.data, 'assignment_details': assignment_details.data})
