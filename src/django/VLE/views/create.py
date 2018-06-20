from rest_framework.decorators import api_view
from django.http import JsonResponse

from VLE.serializers import *
import VLE.factory as factory
import VLE.utils as utils


@api_view(['POST'])
def create_new_course(request):
    """Create a new course

    Arguments:
    request -- the request that was send with
        name -- name of the course
        abbr -- abbreviation of the course
        startdate -- optional date when the course starts
        lti_id -- optional lti_id to link the course to

    On success, returns a json string containing the course.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'result': '401 Authentication Error'}, status=401)

    try:
        name, abbr = utils.get_required_post_params(request.data, "name", "abbr")
        startdate, lti_id = utils.get_optional_post_params(request.data, "startdate", "lti_id")
    except KeyError:
        return utils.keyerror_json("name", "abbr")

    course = factory.make_course(name, abbr, startdate, request.user, lti_id)

    return JsonResponse({'result': 'success', 'course': course_to_dict(course)})


@api_view(['POST'])
def create_new_assignment(request):
    """Create a new assignment

    Arguments:
    request -- the request that was send with
        name -- name of the assignment
        description -- description of the assignment
        cID -- id of the course the assignment belongs to

    On success, returns a json string containing the assignment.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'result': '401 Authentication Error'}, status=401)

    try:
        name, description, cID = utils.get_required_post_params(request.data, "name", "description", "cID")
        assignment = factory.make_assignment(name, description, cID, request.user)
    except KeyError:
        return utils.keyerror_json("name", "description", "cID")

    return JsonResponse({'result': 'success', 'assignment': assignment_to_dict(assignment)})


@api_view(['POST'])
def create_journal(request):
    """Create a new journal

    Arguments:
    request -- the request that was send with
    aID -- the assignment id
    """
    if not request.user.is_authenticated:
        return JsonResponse({'result': '401 Authentication Error'}, status=401)

    try:
        aID = utils.get_required_post_params(request.data, "aID")
    except KeyError:
        return utils.keyerror_json("aID")

    assignment = Assignment.objects.get(pk=aID)
    journal = factory.make_journal(assignment, request.user)

    return JsonResponse({'result': 'success', 'journal': journal_to_dict(journal)})


@api_view(['POST'])
def create_entry(request):
    """Create a new entry
    TODO: How to match new Entry (Deadline) with a pre-existing Node?
    Arguments:
    request -- the request that was send with
    jID -- the journal id
    """
    if not request.user.is_authenticated:
        return JsonResponse({'result': '401 Authentication Error'}, status=401)

    try:
        jID, tID = utils.get_required_post_params(request.data, "jID", "tID")
        nID = utils.get_optional_post_params(request.data, "nID")
    except KeyError:
        return utils.keyerror_json("jID", "tID")

    try:
        journal = Journal.objects.get(pk=jID, user=request.user)

        template = EntryTemplate.objects.get(pk=request.data['tID'])

        # TODO: content.

        # TODO: Check if node can still be created (deadline passed? graded?)
        if nID:
            node = Node.objects.get(pk=nID, journal=journal)
            if node.type == Node.PROGRESS:
                return JsonResponse({'result': '400 Bad Request',
                                     'description': 'Passed node is a Progress node.'},
                                    status=400)

            node.entry = make_entry(template)

        else:
            entry = make_entry(template)
            node = make_node(journal, entry)

        return JsonResponse({'result': 'success', 'node': node_to_dict(node)}, status=200)
    except (Journal.DoesNotExist, EntryTemplate.DoesNotExist, Node.DoesNotExist):
        return JsonResponse({'result': '400 Bad Request',
                             'description': 'Journal, Template or Node does not exist.'},
                            status=400)
