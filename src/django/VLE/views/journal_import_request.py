from rest_framework import viewsets

import VLE.utils.generic_utils as utils
import VLE.utils.responses as response
from VLE.models import AssignmentParticipation, Entry, Journal, JournalImportRequest
from VLE.serializers import JournalImportRequestSerializer


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
            journal_target.import_request_target.all(), context={'user': request.user}, many=True)
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
