"""
Test the functionality of server.py. To run with pytest.

The backend server must be running for the tests to run properly.
"""

import sys
from os.path import abspath, dirname
sys.path.insert(0, f'{abspath(dirname(__file__))}/../../..')

from contextlib import contextmanager
import urllib.request as req
import urllib.error
from urllib.parse import quote
import json

import pytest

urlbase = 'http://localhost:5000/'


# Helper functions.

def request(*args, **kwargs):
    "Return the json response from a url, accessed by basic authentication."
    mgr = req.HTTPPasswordMgrWithDefaultRealm()
    mgr.add_password(None, urlbase, 'admin', 'abc')
    opener = req.build_opener(req.HTTPBasicAuthHandler(mgr))
    headers = {'Content-Type': 'application/json'}
    r = req.Request(urlbase + args[0], *args[1:], **kwargs, headers=headers)
    return json.loads(opener.open(r).read().decode('utf8'))


def get(*args, **kwargs):
    assert 'data' not in kwargs, 'Error: requests with data should be POST'
    return request(*args, **kwargs, method='GET')


def post(*args, **kwargs):
    assert 'data' in kwargs, 'Error: POST requests must have data'
    return request(*args, **kwargs, method='POST')


def put(*args, **kwargs):
    return request(*args, **kwargs, method='PUT')


def delete(*args, **kwargs):
    return request(*args, **kwargs, method='DELETE')


def jdumps(obj):
    return json.dumps(obj).encode('utf8')


def add_test_user(fields=None):
    try:
        get('id/users/test_user')
        raise Exception('test_user already exists.')
    except urllib.error.HTTPError:
        pass

    data = {
        'username': 'test_user',
        'name': 'Random User', 'password': 'booo'}
    if fields:
        data.update(fields)

    return post('users', data=jdumps(data))


def del_test_user():
    uid = get('id/users/test_user')['id']
    return delete('users/%s' % uid)


@contextmanager
def test_user(fields=None):
    add_test_user(fields)
    try:
        yield
    finally:
        del_test_user()


def add_test_tree(fields=None):
    try:
        get('id/trees/test_tree')
        raise Exception('tree "test_tree" already exists.')
    except urllib.error.HTTPError:
        pass

    data = {
        'name': 'test_tree',
        'description': 'This is an empty descritpion.',
        'newick': '(b)a;'}
    if fields:
        data.update(fields)

    return post('trees', data=jdumps(data))


def del_test_tree():
    pid =  get('id/trees/test_tree')['id']
    return delete('trees/%s' % pid)


@contextmanager
def test_tree(fields=None):
    add_test_tree(fields)
    try:
        yield
    finally:
        del_test_tree()


# The tests.

def test_not_found():
    with pytest.raises(urllib.error.HTTPError) as e:
        url = urlbase + 'nonexistent'
        req.urlopen(url)
    assert (e.value.getcode(), e.value.msg) == (404, 'NOT FOUND')


def test_unauthorized():
    with pytest.raises(urllib.error.HTTPError) as e:
        url = urlbase + 'users/1'
        req.urlopen(req.Request(url, method='DELETE'))
    assert (e.value.getcode(), e.value.msg) == (401, 'UNAUTHORIZED')


def test_auth_basic():
    put('trees/1', data=jdumps({'description': 'Changed in a test.'}))
    # If we are not authenticated, that request will raise an error.


def test_auth_bearer():
    data = jdumps({'username': 'admin', 'password': 'abc'})
    res = post('login', data=data)
    auth_txt = 'Bearer ' + res['token']
    r = req.Request(urlbase + 'info', headers={'Authorization': auth_txt})
    req.urlopen(r)
    # If we are not authenticated, the request will raise an error.


def test_get_users():
    res = get('users')
    assert type(res) == list
    assert all(x in res[0] for x in 'id username name'.split())
    assert res[0]['id'] == 1
    assert res[0]['username'] == 'admin'


def test_get_trees():
    res = get('trees')
    assert type(res) == list
    keys = 'id name description birth owner readers'.split()
    sample_tree = next(t for t in res if t['name'] == 'Sample Tree')
    assert all(x in sample_tree for x in keys)
    assert sample_tree['id'] == 1
    assert sample_tree['owner'] == 1


def test_add_del_user():
    res = add_test_user()
    assert res['message'] == 'ok'

    res = del_test_user()
    assert res['message'] == 'ok'


def test_add_del_tree():
    res = add_test_tree()
    assert res['message'] == 'ok'

    res = del_test_tree()
    assert res['message'] == 'ok'


def test_change_user():
    with test_user():
        uid = get('id/users/test_user')['id']
        assert get('users/%s' % uid)['name'] == 'Random User'

        res = put('users/%s' % uid, data=jdumps({'name': 'Newman'}))
        assert res['message'] == 'ok'

        assert get('users/%s' % uid)['name'] == 'Newman'


def test_change_tree():
    with test_tree():
        tid = get('id/trees/test_tree')['id']
        assert get('trees/%s' % tid)['name'] == 'test_tree'

        res = put('trees/%s' % tid, data=jdumps({'description': 'changed'}))
        assert res['message'] == 'ok'

        assert get('trees/%s' % tid)['description'] == 'changed'


def test_add_del_readers():
    with test_user():
        uid = get('id/users/test_user')['id']
        with test_tree():
            tid = get('id/trees/test_tree')['id']
            res = put('trees/%s' % tid,
                data=jdumps({'addReaders': [uid]}))
            assert res['message'] == 'ok'

            assert uid in get('trees/%s' % tid)['readers']

            res = put('trees/%s' % tid,
                data=jdumps({'delReaders': [uid]}))
            assert res['message'] == 'ok'


def test_get_info():
    assert get('info') == get('users/1')


def test_existing_user():
    with test_user():
        with pytest.raises(urllib.error.HTTPError) as e:
            data = jdumps({
                'username': 'test_user', 'name': 'Random User',
                'password': 'booo'})  # duplicated user
            post('users', data=data)
        assert e.value.code == 400
        res = json.loads(e.value.file.read())
        assert res['message'].startswith('Error: database exception adding user')


def test_missing_username_in_new_user():
    with pytest.raises(urllib.error.HTTPError) as e:
        data = jdumps({
            'name': 'Random User', 'password': 'booo'})  # missing: username
        post('users', data=data)
    assert e.value.code == 400
    res = json.loads(e.value.file.read())
    assert res['message'].startswith('Error: must have the fields')


def test_adding_invalid_fields_in_new_user():
    with pytest.raises(urllib.error.HTTPError) as e:
        data = jdumps({'username': 'test_user',
            'name': 'Random User', 'password': 'booo',
            'invalid': 'should not go'})  # invalid
        post('users', data=data)
    assert e.value.code == 400
    res = json.loads(e.value.file.read())
    assert res['message'].startswith('Error: can only have the fields')


def test_change_password():
    with test_user():
        # Change password.
        uid = get('id/users/test_user')['id']
        password_new = 'new_shiny_password'
        data = jdumps({'password': password_new})
        put('users/%s' % uid, data=data)

        # Use new password to connect.
        mgr = req.HTTPPasswordMgrWithDefaultRealm()
        mgr.add_password(None, urlbase, 'test_user', password_new)
        opener = req.build_opener(req.HTTPBasicAuthHandler(mgr))
        headers = {'Content-Type': 'application/json'}
        r = req.Request(urlbase + 'users/%s' % uid, headers=headers,
            method='PUT', data=jdumps({'name': 'Re-logged and changed name'}))
        res = json.loads(opener.open(r).read().decode('utf8'))
        assert res['message'] == 'ok'
        # If we are not authenticated, that request will raise an error.


def test_get_unknown_tree():
    nonexistent_tree_id = 22342342
    for endpoint in ['', '/newick', '/draw', '/size']:
        with pytest.raises(urllib.error.HTTPError) as e:
            get(f'trees/{nonexistent_tree_id}{endpoint}')
        assert e.value.code == 404
        res = json.loads(e.value.file.read())
        assert res['message'].startswith('Error: unknown tree id')


def test_get_known_tree():
    valid_elements = ['nodebox', 'outline', 'line', 'arc', 'circle', 'text']

    trees = [x['id'] for x in get('trees')]

    newicks_checked = False

    for tid in trees:
        try:
            newick = get(f'trees/{tid}/newick')
            assert newick.startswith('(') and newick.endswith(';')
            newicks_checked = True
        except urllib.error.HTTPError as e:
            assert e.code == 400
            res = json.loads(e.file.read())
            assert res['message'].startswith('Error: newick too big')


        elements = get(f'trees/{tid}/draw')
        assert all(x[0] in valid_elements for x in elements)
        assert set(get(f'trees/{tid}/size').keys()) == {'width', 'height'}

    assert newicks_checked  # make sure we checked at least one!


def test_get_drawers():
    drawers = get('/drawers')
    assert type(drawers) == list
    existing_drawers = [
        'Rect', 'Circ', 'RectLabels', 'CircLabels',
        'RectLeafNames', 'CircLeafNames', 'AlignNames', 'AlignHeatMap']
    assert all(x in drawers for x in existing_drawers)


def test_drawer_arguments():
    valid_requests = [
        'x=1&y=-1&w=1&h=1',
        'zx=3&zy=6',
        'drawer=Rect',
        'min_size=8',
        'panel=1',
        'rmin=5&amin=-180&amax=180',
        'x=1&y=-1&w=1&h=1&drawer=Rect&min_size=8&panel=1&zx=3&zy=6']

    invalid_requests_and_error = [
        ('x=1&y=-1&w=1&h=-1', 'invalid viewport'),
        ('zx=-3', 'zoom must be > 0'),
        ('drawer=Nonexistent', 'not a valid drawer'),
        ('min_size=-4', 'min_size must be > 0'),
        ('nonexistentarg=4', 'invalid keys')]

    for qs in valid_requests:
        get(f'trees/1/draw?{qs}')  # does not raise an exception

    for qs, error in invalid_requests_and_error:
        with pytest.raises(urllib.error.HTTPError) as e:
            get(f'trees/1/draw?{qs}')
        assert e.value.code == 400
        res = json.loads(e.value.file.read())
        assert res['message'].startswith('Error: ' + error)


def test_search():
    valid_requests = [
        'text=A',
        'text=%s' % quote('/r (A|B)'),
        'text=%s' % quote('/e is_leaf or d > 1')]

    invalid_requests_and_error = [
        ('', 'missing search text'),
        ('text=/', 'invalid command'),
        ('text=%s' % quote('/e open("/etc/passwd")'), 'invalid use of'),
        ('text=%s' % quote('/e __import__("os").execv("/bin/echo", ["0wN3d"])'),
         'invalid use of')]

    for qs in valid_requests:
        get(f'trees/1/search?{qs}')  # does not raise an exception

    for qs, error in invalid_requests_and_error:
        with pytest.raises(urllib.error.HTTPError) as e:
            get(f'trees/1/search?{qs}')
        assert e.value.code == 400
        res = json.loads(e.value.file.read())
        assert res['message'].startswith('Error: ' + error)
