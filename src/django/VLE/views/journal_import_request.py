from rest_framework import viewsets

import VLE.utils.generic_utils as utils
import VLE.utils.responses as response
from VLE.models import AssignmentParticipation, Entry, Journal, JournalImportRequest, Comment, FileContext, Content
from VLE.serializers import JournalImportRequestSerializer
from django.core.files.base import ContentFile


class JournalImportRequestView(viewsets.ViewSet):
    def list(self, request):
        """
        Lists all journal import requests (JIR) for a given (import) target journal.

        JIRs are not (fully) serialized alongside their respective journals in order to speedup the
        assignment page, as JIRs occur infrequently.
        """
        journal_target_id, = utils.required_typed_params(request.query_params, (int, 'journal_target_id'))

        journal_target = Journal.objects.get(pk=journal_target_id)
        request.user.check_can_view(journal_target)

        # QUESTION: How to work with JIRs of which the requestee cannot see the source? The source journal IS serialized

        serializer = JournalImportRequestSerializer(
            journal_target.import_request_target.filter(state=JournalImportRequest.PENDING),
            context={'user': request.user},
            many=True
        )
        return response.success({'journal_import_requests': serializer.data})

    def create(self, request):
        journal_source_id, journal_target_id = utils.required_typed_params(
            request.data, (int, 'journal_source_id'), (int, 'journal_target_id'))

        if journal_source_id is journal_target_id:
            return response.bad_request('You cannot import a journal into itself.')

        journal_source = Journal.objects.get(pk=journal_source_id)
        journal_target = Journal.objects.get(pk=journal_target_id)
        ap_source = AssignmentParticipation.objects.filter(user=request.user, journal=journal_source)
        ap_target = AssignmentParticipation.objects.filter(user=request.user, journal=journal_target)

        if not ap_source.exists() or not ap_target.exists():
            return response.forbidden('You can only import from or into your own journals.')

        # QUESTION: Do we care about the lock state of the assignment source or destination?

        if not Entry.objects.filter(node__journal=journal_source).exists():
            return response.bad_request('Please select a non empty journal.')

        jir = JournalImportRequest.objects.create(source=journal_source, target=journal_target, author=request.user)

        serializer = JournalImportRequestSerializer(jir, many=False, context={'user': request.user})
        return response.created({'journal_import_request': serializer.data})

    def partial_update(self, request, *args, **kwargs):
        """
        Handles the processing of a pending JIR. There are three possible outcomes:

        - Decline the request
        - Approve import including any previous grades
        - Approve import without any of the previous grades

        The processed JIR instance is stored as history.
        """
        pk, = utils.required_typed_params(kwargs, (int, 'pk'))
        jir_action, = utils.required_typed_params(request.data, (str, 'jir_action'))

        jir = JournalImportRequest.objects.get(pk=pk, state=JournalImportRequest.PENDING)

        allowed_actions = [abbr for (abbr, _) in jir.STATES if (abbr not in [jir.PENDING, jir.EMPTY_WHEN_PROCESSED])]
        if jir_action not in allowed_actions:
            return response.bad_request('Unknown journal import request action.')

        # QUESTION: Does the approving user also need grade permissions (or atleast view permissions) of the source?
        # Since after the import, the source is viewable by the approving user.

        if not request.user.has_permission('can_grade', jir.target.assignment):
            return response.forbidden('You require the ability to grade the journal in order to approve the import.')

        source_entries = Entry.objects.filter(node__journal=jir.source)

        if not source_entries.exists():
            jir.state = jir.EMPTY_WHEN_PROCESSED

        # TODO JIR: Create differentiating labels indiciting the entry was imported
        for entry in source_entries:
            contents = Content.objects.filter(entry=entry)
            comments = Comment.objects.filter(node=entry.node)

            entry.pk = None
            # TODO JIR: Can we keep the old template or does it need to be duplicated to the new assignment
            if jir_action == jir.APPROVED_EXC_GRADES:
                entry.grade = None
            entry.save()

            node = entry.node
            # TODO JIR: If a link to presetnode exists can this be maintained? node.preset.format.assignment will diff
            node.pk = None
            node.entry = entry
            node.journal = jir.target
            node.save()

            # TODO JIR: Double check if the one to one relation Entry -- Node is correct on the entry side

            # TODO JIR, move to function (for testing)
            for comment in comments:
                comment.pk = None
                comment.node = node
                comment.save()

                # TODO JIR, check whether this approach accurately captures both attached files as embedded in text
                # TODO JIR, doublecheck if FCs indeed cannot be temp if comment context is set
                for old_fc in FileContext.objects.filter(comment=comment, is_temp=False):
                    new_fc = FileContext.objects.create(
                        file=ContentFile(old_fc.file.file.read(), name=old_fc.file_name),
                        file_name=old_fc.file_name,
                        author=old_fc.author,
                        is_temp=old_fc.is_temp,
                        creation_date=old_fc.creation_date,
                        last_edited=old_fc.last_edited,
                        comment=comment,
                        journal=jir.target,
                        in_rich_text=old_fc.in_rich_text
                    )

                    comment.text = comment.text.replace(
                        '?access_id={}'.format(old_fc.access_id), '?access_id={}'.format(new_fc.access_id))
                    comment.save()

            # TODO JIR, move to function (for testing), also copy any files associated with the content
            for content in contents:
                content.pk = None
                # Can the old Field link remain intact? field.template.format.assignment will be different
                content.entry = entry
                content.save()

                # TODO JIR, doublecheck if FCs indeed cannot be temp if comment context is set
                for old_fc in FileContext.objects.filter(content=content, is_temp=False):
                    new_fc = FileContext.objects.create(
                        file=ContentFile(old_fc.file.file.read(), name=old_fc.file_name),
                        file_name=old_fc.file_name,
                        author=old_fc.author,
                        is_temp=old_fc.is_temp,
                        creation_date=old_fc.creation_date,
                        last_edited=old_fc.last_edited,
                        content=content,
                        journal=jir.target,
                        in_rich_text=old_fc.in_rich_text
                    )

            # TODO JIR: Notify teacher of new entry / grades
            # grading.task_journal_status_to_LMS.delay(journal.pk)

        jir.processor = request.user
        jir.save()

        return response.success(description='Successfully update journal import request.')
