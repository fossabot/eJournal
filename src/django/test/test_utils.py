"""
test_utils.py.

Test helper functions.
"""

from django.urls import reverse
import json


import VLE.factory as factory


def set_up_user_and_auth(username, password):
    """Set up a teacher user.

    Arguments:
    username -- username for the user
    password -- password for the user

    Returns the user and its credentials
    """
    user = factory.make_user(username, password)
    return username, password, user


def set_up_users(name, n):
    """Set up some students.

    Arguments:
    name -- the base for the incremental names for the users
    n -- number of students to be made

    Returns a list of users with incremental naming.
    """
    users = []
    for i in range(n):
        users.append(factory.make_user(name + str(i), 'pass'))
    return users


def set_up_entries(template, n):
    """Set up some entries.

    Arguments:
    template -- the template to be used for the entries
    n -- number of entriest to be made

    Returns a list of entries that uses the same template.
    """
    entries = []
    for i in range(n):
        entries.append(factory.make_entry(template))
    return entries


def set_up_courses(name, n, author=None, lti_id=False):
    """Set up some courses.

    Arguments:
    name -- the base for the incremental names for the courses
    n -- number of courses to be made
    author -- the user who made the course and it automatically will be teacher
    lti_id -- a boolean to determine if to give lti ids

    Returns a list of courses.
    """
    courses = []
    if lti_id:
        for i in range(n):
            courses.append(factory.make_course(name + str(i), name[0] + str(i), author=author, lti_id=str(i)))
    else:
        for i in range(n):
            courses.append(factory.make_course(name + str(i), name[0] + str(i), author=author))
    return courses


def set_up_assignments(name, desc, n, course, lti_id=False):
    """Set up some assignments.

    Arguments:
    name -- the base for the incremental names for the assignments
    desc -- the base for the incremental description for the assignments
    n -- number of assignments to be made.
    lti_id -- a boolean to determine if to give lti ids

    Returns a list of assignments.
    """
    assignments = []
    if lti_id:
        for i in range(n):
            assignments.append(factory.make_assignment(name + str(i), desc + str(i),
                                                       lti_id=str(i), courses=[course]))
    else:
        for i in range(n):
            assignments.append(factory.make_assignment(name + str(i), desc + str(i), courses=[course]))
    return assignments


def logging_in(obj, username, password, status=200):
    """Login using username and password.

    Arguments:
    username -- username
    password -- password
    status -- status it checks for after login (default 200)

    Returns the loggin in user.
    """
    result = obj.client.post(reverse('token_obtain_pair'),
                             json.dumps({'username': username, 'password': password}),
                             content_type='application/json')
    obj.assertEquals(result.status_code, status)
    return result


def api_get_call(obj, url, login, status=200):
    """Send an get api call.

    Arguments:
    url -- url to send the call to
    login -- credentials of the logged in user
    status -- status it checks for after login (default 200)

    returns the whatever the api call returns
    """
    result = obj.client.get(url, {},
                            HTTP_AUTHORIZATION='Bearer {0}'.format(login.data['access']))
    obj.assertEquals(result.status_code, status)
    return result


def api_post_call(obj, url, params, login, status=200):
    """Send an get api call.

    Arguments:
    url -- url to send the call to
    params -- extra parameters that the api needs
    login -- credentials of the logged in user
    status -- status it checks for after login (default 200)

    returns the whatever the api call returns
    """
    result = obj.client.post(url, json.dumps(params), content_type='application/json',
                             HTTP_AUTHORIZATION='Bearer {0}'.format(login.data['access']))
    obj.assertEquals(result.status_code, status)
    return result