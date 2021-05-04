#!/usr/bin/env python3

"""
Keep the data of users and trees, and present a REST api to talk
to the world.

REST call examples:
  GET    /users       Get all users
  GET    /users/{id}  Get the user information identified by "id"
  POST   /users       Create a new user
  PUT    /users/{id}  Update the user information identified by "id"
  DELETE /users/{id}  Delete user by "id"
"""

# The structure that we want to follow is:
#
# user
#   id: int
#   username: str
#   name: str
#   password: str
#   owns: list of ints (tree ids)
#   reads: list of ints (tree ids)
#
# tree
#   id: int
#   name: str
#   description: str
#   birth: datetime
#   newick: str
#   owner: int (user id)
#   readers: list of ints (user ids)

import os
os.chdir(os.path.abspath(os.path.dirname(__file__)))

import sys
sys.path.insert(0, '..')

import re
from math import pi
from functools import partial
from datetime import datetime
from contextlib import contextmanager
import gzip
import json

from flask import Flask, request, jsonify, g, redirect, url_for
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_compress import Compress
import sqlalchemy
from itsdangerous import TimedJSONWebSignatureSerializer as JSONSigSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from ete4 import Tree
from ete4.parser.newick import NewickError
from ete4.smartview.ete import nexus, draw, gardening as gdn


db = None  # call initialize() to fill these up
serializer = None  # this one is used for the token auth


# Set up the authentication (see https://flask-httpauth.readthedocs.io/).

auth_basic = HTTPBasicAuth()
auth_token = HTTPTokenAuth('Bearer')
auth = MultiAuth(auth_basic, auth_token)

@auth_basic.verify_password
def verify_password(username, password):
    res = dbget('id,password', 'users WHERE username=?', username)
    if len(res) == 1:
        g.user_id = res[0]['id']
        return check_password_hash(res[0]['password'], password)
    else:
        return False

@auth_token.verify_token
def verify_token(token):
    try:
        g.user_id = serializer.loads(token)
        return True
    except:
        return False


# Customized exception.

class InvalidUsage(Exception):
    def __init__(self, message, status_code=400):
        super().__init__()
        self.message = 'Error: ' + message
        self.status_code = status_code


# REST api.

class Login(Resource):
    def post(self):
        "Return info about the user if successfully logged"
        data = get_fields(required=['username', 'password'])
        username = data['username']
        fields = 'id,name,password'

        res = dbget(fields, 'users WHERE username=?', username)
        if len(res) == 0:
            raise InvalidUsage('bad user/password', 401)
        r0 = res[0]

        if not check_password_hash(r0['password'], data['password']):
            raise InvalidUsage('bad user/password', 401)

        token = serializer.dumps(r0['id']).decode('utf8')
        return {'id': r0['id'],
                'username': username,
                'name': r0['name'],
                'token': token}


class Users(Resource):
    def get(self, user_id=None):
        "Return info about the user (or all users if no id given)"
        if user_id is None:
            return [get_user(uid) for uid in sorted(dbget0('id', 'users'))]
        else:
            return get_user(user_id)

    @auth.login_required
    def post(self):
        "Add user"
        admin_id = 1
        if g.user_id != admin_id:
            raise InvalidUsage('no permission to add', 403)

        data = get_fields(required=['username', 'password'],
            valid_extra=['name'])

        data['password'] = generate_password_hash(data['password'])
        data.setdefault('name', 'Random User')

        cols, vals = zip(*data.items())
        try:
            qs = '(%s)' % ','.join('?' * len(vals))
            dbexe('INSERT INTO users %r VALUES %s' % (tuple(cols), qs), vals)
        except sqlalchemy.exc.IntegrityError as e:
            raise InvalidUsage(f'database exception adding user: {e}')

        uid = dbget0('id', 'users WHERE username=?', data['username'])
        return {'message': 'ok', 'id': uid}, 201

    @auth.login_required
    def put(self, user_id):
        "Modify user"
        admin_id = 1
        if g.user_id not in [user_id, admin_id]:
            raise InvalidUsage('no permission to modify', 403)

        data = get_fields(
            valid_extra=['username', 'name', 'password'])

        if 'password' in data:
            data['password'] = generate_password_hash(data['password'])

        cols, vals = zip(*data.items())
        qs = ','.join('%s=?' % x for x in cols)
        res = dbexe('UPDATE users SET %s WHERE id=%d' % (qs, user_id), vals)

        if res.rowcount != 1:
            raise InvalidUsage(f'unknown user id {user_id}', 409)

        return {'message': 'ok'}

    @auth.login_required
    def delete(self, user_id):
        "Delete user and all references to her"
        admin_id = 1
        if g.user_id not in [user_id, admin_id]:
            raise InvalidUsage('no permission to delete', 403)

        with shared_connection([dbget0, dbexe]) as [get0, exe]:
            res = exe('DELETE FROM users WHERE id=?', user_id)
            if res.rowcount != 1:
                raise InvalidUsage(f'unknown user id {user_id}', 404)

            for tid in get0('id_tree', 'user_owns_trees WHERE id_user=?', user_id):
                del_tree(tid)
            # NOTE: we could instead move them to a list of orphaned trees.

            exe('DELETE FROM user_owns_trees WHERE id_user=?', user_id)
            exe('DELETE FROM user_reads_trees WHERE id_user=?', user_id)

        return {'message': 'ok'}


class Drawers(Resource):
    def get(self, name=None):
        "Return data from the drawer (or info about all drawers if no id given)"
        rule = request.url_rule.rule  # shortcut
        if rule == '/drawers':
            return [d.__name__[len('Drawer'):] for d in draw.get_drawers()]
        elif rule == '/drawers/<string:name>':
            try:
                drawer_class = next(d for d in draw.get_drawers()
                    if d.__name__[len('Drawer'):] == name)
                return {'type': drawer_class.TYPE,
                        'npanels': drawer_class.NPANELS}
            except StopIteration:
                raise InvalidUsage(f'not a valid drawer: {name}')


class Trees(Resource):
    # NOTE: If we wanted to enforce that only the 'readers' (or owner) of a
    #   tree have access to it, we would need to add  @auth.login_required
    #   and check that g.user_id is a reader (or the owner, or admin).
    def get(self, tree_id=None):
        "Return data from the tree (or info about all trees if no id given)"
        rule = request.url_rule.rule  # shortcut
        if rule == '/trees':
            return [get_tree(pid) for pid in dbget0('id', 'trees')]
        elif rule == '/trees/<string:tree_id>':
            return get_tree(tree_id)
        elif rule == '/trees/<string:tree_id>/newick':
            MAX_MB = 2
            return get_newick(tree_id, MAX_MB)
        elif rule == '/trees/<string:tree_id>/search':
            nresults, nparents = store_search(tree_id, request.args.copy())
            return {'message': 'ok', 'nresults': nresults, 'nparents': nparents}
        elif rule == '/trees/<string:tree_id>/draw':
            drawer = get_drawer(tree_id, request.args.copy())
            return list(drawer.draw())
        elif rule == '/trees/<string:tree_id>/size':
            width, height = load_tree(tree_id).size
            return {'width': width, 'height': height}
        elif rule == '/trees/<string:tree_id>/properties':
            t = load_tree(tree_id)
            properties = set()
            for node in t.traverse():
                properties |= node.properties.keys()
            return list(properties)
        elif rule == '/trees/<string:tree_id>/nodecount':
            t = load_tree(tree_id)
            tnodes = tleaves = 0
            for node in t.traverse():
                tnodes += 1
                if node.is_leaf():
                    tleaves += 1
            return {'tnodes': tnodes, 'tleaves': tleaves}

    @auth.login_required
    def post(self):
        "Add tree(s)"
        ids = add_trees_from_request()
        return {'message': 'ok', 'ids': ids}, 201

    @auth.login_required
    def put(self, tree_id):
        "Modify tree"
        rule = request.url_rule.rule  # shortcut

        if rule == '/trees/<string:tree_id>':
            modify_tree_fields(tree_id)
            return {'message': 'ok'}
        elif rule == '/trees/<string:tree_id>/sort':
            node_id, key_text, reverse = request.json
            sort(tree_id, node_id, key_text, reverse)
            return {'message': 'ok'}
        elif rule == '/trees/<string:tree_id>/root_at':
            tid, subtree = get_tid(tree_id)
            if subtree:
                raise InvalidUsage('operation not allowed with subtree')
            node_id = request.json
            t = load_tree(tid)
            app.trees[tid] = gdn.root_at(gdn.get_node(t, node_id))
            return {'message': 'ok'}
        elif rule == '/trees/<string:tree_id>/move':
            try:
                t = load_tree(tree_id)
                node_id, shift = request.json
                gdn.move(gdn.get_node(t, node_id), shift)
                return {'message': 'ok'}
            except AssertionError as e:
                raise InvalidUsage(f'cannot move ${node_id}: {e}')
        elif rule == '/trees/<string:tree_id>/remove':
            try:
                t = load_tree(tree_id)
                node_id = request.json
                gdn.remove(gdn.get_node(t, node_id))
                return {'message': 'ok'}
            except AssertionError as e:
                raise InvalidUsage(f'cannot remove ${node_id}: {e}')
        elif rule == '/trees/<string:tree_id>/rename':
            try:
                t = load_tree(tree_id)
                node_id, name = request.json
                gdn.get_node(t, node_id).name = name
                return {'message': 'ok'}
            except AssertionError as e:
                raise InvalidUsage(f'cannot rename ${node_id}: {e}')
        elif rule == '/trees/<string:tree_id>/reload':
            tid, subtree = get_tid(tree_id)
            if subtree:
                raise InvalidUsage('operation not allowed with subtree')
            del app.trees[tid]
            load_tree(tid)
            return {'message': 'ok'}


    @auth.login_required
    def delete(self, tree_id):
        "Delete tree and all references to it"
        try:
            tid = int(tree_id)

            assert dbcount('trees WHERE id=?', tid) == 1, 'unknown tree'

            admin_id = 1
            assert g.user_id in [get_owner(tid), admin_id], 'no permission'

            del_tree(tid)
            return {'message': 'ok'}
        except (ValueError, AssertionError) as e:
            raise InvalidUsage(f'for tree id {tree_id}: {e}')


class Info(Resource):
    @auth.login_required
    def get(self):
        "Return info about the currently logged user"
        return get_user(g.user_id)


class Id(Resource):
    def get(self, path):
        if not any(path.startswith(x) for x in ['users/', 'trees/']):
            raise InvalidUsage('invalid path %r' % path, 404)

        name = path.split('/', 1)[-1]
        if path.startswith('users/'):
            uids = dbget0('id', 'users WHERE username=?', name)
            if len(uids) != 1:
                raise InvalidUsage('unknown username %r' % name)
            return {'id': uids[0]}
        elif path.startswith('trees/'):
            pids = dbget0('id', 'trees WHERE name=?', name)
            if len(pids) != 1:
                raise InvalidUsage('unknown tree name %r' % name)
            return {'id': pids[0]}



# Auxiliary functions.

def load_tree(tree_id):
    "Add tree to app.trees and initialize it if not there, and return it"
    try:
        tid, subtree = get_tid(tree_id)

        if tid in app.trees:
            return gdn.get_node(app.trees[tid], subtree)

        newicks = dbget0('newick', 'trees WHERE id=?', tid)
        assert len(newicks) == 1

        t = Tree(newicks[0])
        gdn.standardize(t)

        app.trees[tid] = t

        return gdn.get_node(t, subtree)
    except (AssertionError, IndexError):
        raise InvalidUsage(f'unknown tree id {tree_id}', 404)


def get_drawer(tree_id, args):
    "Return the drawer initialized as specified in the args"
    valid_keys = ['x', 'y', 'w', 'h', 'panel', 'zx', 'zy', 'drawer', 'min_size',
                  'collapsed_ids', 'labels', 'rmin', 'amin', 'amax']

    try:
        assert all(k in valid_keys for k in args.keys()), 'invalid keys'

        get = lambda x, default: float(args.get(x, default))  # shortcut

        viewport = ([get(k, 0) for k in ['x', 'y', 'w', 'h']]
            if all(k in args for k in ['x', 'y', 'w', 'h']) else None)
        assert viewport is None or (viewport[2] > 0 and viewport[3] > 0), \
            'invalid viewport'  # width and height must be > 0

        panel = get('panel', 0)

        zoom = (get('zx', 1), get('zy', 1))
        assert zoom[0] > 0 and zoom[1] > 0, 'zoom must be > 0'

        drawer_name = args.get('drawer', 'RectLeafNames')
        drawer_class = next(d for d in draw.get_drawers()
            if d.__name__[len('Drawer'):] == drawer_name)

        drawer_class.MIN_SIZE = get('min_size', 6)
        assert drawer_class.MIN_SIZE > 0, 'min_size must be > 0'

        limits = (None if not drawer_name.startswith('Circ') else
            (get('rmin', 0), 0,
             get('amin', -180) * pi/180, get('amax', 180) * pi/180))

        collapsed_ids = set(tuple(int(i) for i in node_id.split(','))
            for node_id in json.loads(args.get('collapsed_ids', '[]')))

        labels = get_label_fns(json.loads(args.get('labels', '[]')))

        searches = app.searches.get(tree_id)

        return drawer_class(load_tree(tree_id), viewport, panel, zoom,
                            limits, collapsed_ids, labels, searches)
    except StopIteration:
        raise InvalidUsage(f'not a valid drawer: {drawer_name}')
    except (ValueError, AssertionError) as e:
        raise InvalidUsage(str(e))


def get_newick(tree_id, max_mb):
    "Return the newick representation of the given tree"

    newick = load_tree(tree_id).write()

    size_mb = len(newick) / 1e6
    if size_mb > max_mb:
        raise InvalidUsage('newick too big (%.3g MB)' % size_mb)

    return newick


def get_label_fns(labels):
    "Return a list of functions that when called on a node will label it"
    positions = set(pos for _,_,pos in labels)
    label_at = {pos: [label for label in labels if label[2] == pos]
                    for pos in positions}

    fns = []
    for pos, labels_pos in label_at.items():
        for i, label in enumerate(labels_pos):
            fns.append(get_label_fn(label, i, len(labels_pos)))

    return fns


def get_label_fn(label, i, n):
    "Return a function that given a node will put a label on it"
    # "label" is the i-th label of n for that postion.
    expression, nodetype, pos = label

    try:
        code = compile(expression, '<string>', 'eval')
    except SyntaxError as e:
        raise InvalidUsage(f'compiling expression: {e}')

    def label_fn(node, point, bdy, size, fit):
        box, anchor = (0, 0, 0, 0), (0, 0)

        if ((nodetype == "leaf" and not node.is_leaf()) or
            (nodetype == "internal" and node.is_leaf())):
            return box, anchor, '', ''

        text = str(safer_eval(code, {
            'name': node.name, 'is_leaf': node.is_leaf(),
            'length': node.dist, 'dist': node.dist, 'd': node.dist,
            'support': node.support,
            'properties': node.properties, 'p': node.properties,
            'get': dict.get, 'split': str.split,
            'children': node.children, 'ch': node.children,
            'regex': re.search,
            'len': len, 'sum': sum, 'abs': abs, 'float': float, 'pi': pi}))

        x, y = point
        dx, dy = size

        if pos == 'branch-top':
            box = (x + i * dx/n, y, dx/n, bdy)  # above the branch
            anchor = (0.5, 1)  # halfway x, bottom y
        elif pos == 'branch-bottom':
            box = (x + i * dx/n, y + bdy, dx/n, dy - bdy)  # below the branch
            anchor = (0.5, 0)  # halfway x, top y
        elif pos == 'branch-top-left':
            box = (x - (i + 1) * dx/n, y, dx/n, bdy)  # left of branch-top
            anchor = (1, 1)  # right x, bottom y
        elif pos == 'branch-bottom-left':
            box = (x - (i + 1) * dx/n, y + bdy, dx/n, dy - bdy)  # etc.
            anchor = (1, 0)  # right x, top y
        elif pos == 'float':
            box = (x + dx, y + i * dy/n, fit(text, dy), dy/n)  # right of node
            anchor = (0, bdy / dy)  # left x, branch position in y
        else:
            raise InvalidUsage(f'unkown position {pos}')

        text_type = 'label_' + expression

        return box, anchor, text, text_type

    return label_fn


def store_search(tree_id, args):
    "Store the results and parents of a search and return their numbers"
    if 'text' not in args:
        raise InvalidUsage('missing search text')

    text = args.pop('text').strip()
    func = get_search_function(text)

    try:
        results = set(node for node in load_tree(tree_id) if func(node))

        parents = set()
        for node in results:
            parent = node.up
            while parent and parent not in parents:
                parents.add(parent)
                parent = parent.up

        app.searches.setdefault(tree_id, {})[text] = (results, parents)

        return len(results), len(parents)
    except InvalidUsage:
        raise
    except Exception as e:
        raise InvalidUsage(f'evaluating expression: {e}')


def get_search_function(text):
    "Return a function of a node that returns True for the searched nodes"
    if text.startswith('/'):
        return get_command_search(text)  # command-based search
    elif text == text.lower():
        return lambda node: text in node.name.lower()  # case-insensitive search
    else:
        return lambda node: text in node.name  # case-sensitive search


def get_command_search(text):
    "Return the appropriate node search function according to the command"
    parts = text.split(None, 1)
    if parts[0] not in ['/r', '/e']:
        raise InvalidUsage('invalid command %r' % parts[0])
    if len(parts) != 2:
        raise InvalidUsage('missing argument to command %r' % parts[0])

    command, arg = parts
    if command == '/r':  # regex search
        return lambda node: re.search(arg, node.name)
    elif command == '/e':  # eval expression
        return get_eval_search(arg)
    else:
        raise InvalidUsage('invalid command %r' % command)


def get_eval_search(expression):
    "Return a function of a node that evaluates the given expression"
    try:
        code = compile(expression, '<string>', 'eval')
    except SyntaxError as e:
        raise InvalidUsage(f'compiling expression: {e}')

    return lambda node: safer_eval(code, {
        'name': node.name, 'is_leaf': node.is_leaf(),
        'length': node.dist, 'dist': node.dist, 'd': node.dist,
        'properties': node.properties, 'p': node.properties,
        'get': dict.get,
        'children': node.children, 'ch': node.children,
        'size': node.size, 'dx': node.size[0], 'dy': node.size[1],
        'regex': re.search,
        'len': len, 'sum': sum, 'abs': abs, 'float': float, 'pi': pi})


def safer_eval(code, context):
    "Return a safer version of eval(code, context)"
    for name in code.co_names:
        if name not in context:
            raise InvalidUsage('invalid use of %r during evaluation' % name)
    return eval(code, {'__builtins__': {}}, context)


def sort(tree_id, node_id, key_text, reverse):
    "Sort the (sub)tree corresponding to tree_id and node_id"
    t = load_tree(tree_id)

    try:
        code = compile(key_text, '<string>', 'eval')
    except SyntaxError as e:
        raise InvalidUsage(f'compiling expression: {e}')

    def key(node):
        return safer_eval(code, {
            'node': node, 'name': node.name, 'is_leaf': node.is_leaf(),
            'length': node.dist, 'dist': node.dist, 'd': node.dist,
            'size': node.size, 'dx': node.size[0], 'dy': node.size[1],
            'children': node.children, 'ch': node.children,
            'len': len, 'sum': sum, 'abs': abs})

    gdn.sort(gdn.get_node(t, node_id), key, reverse)


def add_trees_from_request():
    "Add trees to the database and return a dict of {name: id}"
    if request.form:
        trees = get_trees_from_form()
        owner = g.user_id
    else:
        data = get_fields(required=['name', 'newick'],
                          valid_extra=['description', 'owner'])
        trees = [data]
        owner = data.pop('owner', g.user_id)

    return {data['name']: add_tree(data, owner) for data in trees}


def get_trees_from_form():
    "Return list of dicts with tree info read from a form in the request"
    form = request.form
    if 'trees' in request.files:
        text = get_file_contents(request.files['trees'])
        try:
            trees = nexus.get_trees(text)
            return [{'name': name, 'newick': newick}
                        for name,newick in trees.items()]
        except nexus.NexusError:
            return [{'name': form['name'], 'newick': text,
                     'description': form.get('description', '')}]
    else:
        return [{'name': form['name'], 'newick': form['newick'],
                 'description': form.get('description', '')}]


def get_file_contents(fp):
    "Return the contents of a file received as formdata"
    try:
        data = fp.stream.read()
        if fp.filename.endswith('.gz'):
            data = gzip.decompress(data)
        return data.decode('utf-8').strip()
    except (gzip.BadGzipFile, UnicodeDecodeError) as e:
        raise InvalidUsage(f'when reading {fp.filename}: {e}')


def add_tree(data, owner):
    "Add tree to the database (with given data and owner) and return its id"
    admin_id = 1
    if g.user_id not in [owner, admin_id]:
        raise InvalidUsage('owner set different from current user')

    if dbcount('trees WHERE name=?', data['name']) != 0:
        raise InvalidUsage('existing tree name %r' % data['name'])

    try:
        # load it to validate
        Tree(data['newick']) 
    except NewickError as e:
        raise InvalidUsage(f'malformed tree - {e}')

    data['birth'] = datetime.now()  # add creation time

    tid = None  # will be filled later if it all works
    with shared_connection([dbget0, dbexe]) as [get0, exe]:
        cols, vals = zip(*data.items())
        try:
            qs = '(%s)' % ','.join('?' * len(vals))
            exe('INSERT INTO trees %r VALUES %s' % (tuple(cols), qs), vals)
        except sqlalchemy.exc.IntegrityError as e:
            raise InvalidUsage(f'database exception adding tree: {e}')

        tid = get0('id', 'trees WHERE name=?', data['name'])[0]

        exe('INSERT INTO user_owns_trees VALUES (%d, %d)' % (owner, tid))

    return tid


def modify_tree_fields(tree_id):
    "Modify in the database the tree fields that appear in a request"
    try:
        tid = int(tree_id)

        assert dbcount('trees WHERE id=?', tid) == 1, 'invalid id'

        admin_id = 1
        assert g.user_id in [get_owner(tid), admin_id], 'no permission'

        data = get_fields(valid_extra=[
            'name', 'description', 'newick', 'addReaders','delReaders'])

        add_readers(tid, data.pop('addReaders', None))
        del_readers(tid, data.pop('delReaders', None))
        if not data:
            return {'message': 'ok'}

        cols, vals = zip(*data.items())
        qs = ','.join('%s=?' % x for x in cols)
        res = dbexe('UPDATE trees SET %s WHERE id=%d' % (qs, tid), vals)

        assert res.rowcount == 1, f'unknown tree'
    except (ValueError, AssertionError) as e:
        raise InvalidUsage(f'for tree id {tree_id}: {e}')


# Database-access functions.

def dbexe(command, *args, conn=None):
    "Execute a sql command (using a given connection if given)"
    conn = conn or db.connect()
    return conn.execute(command, *args)


def dbcount(where, *args, conn=None):
    "Return the number of rows from the given table (and given conditions)"
    res = dbexe('SELECT COUNT(*) FROM %s' % where, *args, conn=conn)
    return res.fetchone()[0]


def dbget(what, where, *args, conn=None):
    "Return result of the query 'select what from where' as a list of dicts"
    res = dbexe('SELECT %s FROM %s' % (what, where), *args, conn=conn)
    return [dict(zip(what.split(','), x)) for x in res.fetchall()]


def dbget0(what, where, *args, conn=None):
    "Return a list of the single column of values from get()"
    assert ',' not in what, 'Use this function to select a single column only'
    return [x[what] for x in dbget(what, where, *args, conn=conn)]


@contextmanager
def shared_connection(functions):
    "Create a connection and yield the given functions but working with it"
    with db.connect() as conn:
        yield [partial(f, conn=conn) for f in functions]


# Manage basic fields (related to the SQL schema, like users, readers, etc.).

def get_user(uid):
    "Return all the fields of a given user as a dict"
    with shared_connection([dbget, dbget0]) as [get, get0]:
        users = get('id,username,name', 'users WHERE id=?', uid)
        if len(users) == 0:
            raise InvalidUsage(f'unknown user id {uid}', 404)

        user = users[0]

        user['trees_owner'] = get0('id_tree',
                                   'user_owns_trees WHERE id_user=?', uid)
        user['trees_reader'] = get0('id_tree',
                                    'user_reads_trees WHERE id_user=?', uid)

    return strip(user)


def get_tid(tree_id):
    "Return the tree id and the subtree id, with the appropriate types"
    try:
        if type(tree_id) == int:
            return tree_id, []
        else:
            tid, *subtree = tree_id.split(',')
            return int(tid), [int(n) for n in subtree]
    except ValueError:
        raise InvalidUsage(f'invalid tree id {tree_id}', 404)


def get_tree(tree_id):
    "Return all the fields of a given tree"
    tid, subtree = get_tid(tree_id)

    with shared_connection([dbget, dbget0]) as [get, get0]:
        trees = get('id,name,description,birth', 'trees WHERE id=?', tid)
        if len(trees) == 0:
            raise InvalidUsage(f'unknown tree id {tid}', 404)

        tree = trees[0]

        tree['owner'] = get0('id_user', 'user_owns_trees WHERE id_tree=?', tid)[0]
        tree['readers'] = get0('id_user', 'user_reads_trees WHERE id_tree=?', tid)
        tree['subtree'] = subtree

    return strip(tree)


def get_owner(tid):
    "Return owner id of the given tree"
    return dbget0('id_user', 'user_owns_trees WHERE id_tree=?', tid)


def del_tree(tid):
    "Delete a tree and everywhere where it appears referenced"
    exe = db.connect().execute
    exe('DELETE FROM trees WHERE id=?', tid)
    exe('DELETE FROM user_owns_trees WHERE id_tree=?', tid)
    exe('DELETE FROM user_reads_trees WHERE id_tree=?', tid)
    if tid in app.trees:
        del app.trees[tid]


def strip(d):
    "Return dictionary without the keys that have empty values"
    d_stripped = {}
    for k, v in d.items():
        if v:
            d_stripped[k] = d[k]
    return d_stripped


def add_readers(tid, uids):
    "Add readers (with user id in uids) to a tree (tid)"
    if not uids:
        return
    uids_str = '(%s)' % ','.join('%d' % x for x in uids)  # -> '(u1, u2, ...)'

    if dbcount('users WHERE id IN %s' % uids_str) != len(uids):
        raise InvalidUsage(f'nonexisting user in {uids_str}')
    if dbcount('user_reads_trees '
        'WHERE id_tree=%d AND id_user IN %s' % (tid, uids_str)) != 0:
        raise InvalidUsage('tried to add an existing reader')

    values = ','.join('(%d, %d)' % (uid, tid) for uid in uids)
    dbexe('INSERT INTO user_reads_trees (id_user, id_tree) VALUES %s' % values)


def del_readers(tid, uids):
    "Remove readers (with user id in uids) from a tree (tid)"
    if not uids:
        return
    uids_str = '(%s)' % ','.join('%d' % x for x in uids)  # -> '(u1, u2, ...)'

    if dbcount('user_reads_trees '
        'WHERE id_tree=%d AND id_user IN %s' % (tid, uids_str)) != len(uids):
        raise InvalidUsage(f'nonexisting user in {uids_str}')

    dbexe('DELETE FROM user_reads_trees WHERE '
        'id_user IN %s AND id_tree=?' % uids_str, tid)


def get_fields(required=None, valid_extra=None):
    "Return fields and raise exception if missing required or invalid present"
    if not request.json:
        raise InvalidUsage('missing json content')

    data = request.json.copy()

    if required and any(x not in data for x in required):
        raise InvalidUsage(f'must have the fields {required}')

    valid = (required or []) + (valid_extra or [])
    if not all(x in valid for x in data):
        raise InvalidUsage(f'can only have the fields {valid}')

    return data


# App initialization.

def create_example_database():
    db_path = app.config['DATABASE']

    os.system(f'sqlite3 {db_path} < create_tables.sql')
    os.system(f'sqlite3 {db_path} < sample_data.sql')

    for tfile in ['HmuY.aln2.tree', 'aves.tree', 'GTDB_bact_r95.tree']:
        os.system(f'./add_tree.py --db {db_path} ../examples/{tfile}')


def initialize():
    "Initialize the database and the flask app"
    global db, serializer

    app = Flask(__name__, instance_relative_config=True)
    configure(app)

    api = Api(app)
    add_resources(api)

    app.trees = {}  # to keep in memory loaded trees
    app.searches = {}  # to keep in memory the searches

    serializer = JSONSigSerializer(app.config['SECRET_KEY'], expires_in=3600)

    db = sqlalchemy.create_engine('sqlite:///' + app.config['DATABASE'])

    @app.route('/')
    def index():
        return redirect(url_for('static', filename='upload_tree.html'))

    @app.route('/help')
    def description():
        return ('<html>\n<head>\n<title>Description</title>\n</head>\n<body>\n'
            '<pre>' + __doc__ + '</pre>\n'
            '<p>For analysis, <a href="/static/gui.html">use our gui</a>!</p>\n'
            '</body>\n</html>')

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error):
        response = jsonify({'message': error.message})
        response.status_code = error.status_code
        return response

    api.handle_error = None
    # so our handling is called even when being served from gunicorn

    return app


def configure(app):
    "Set the configuration for the flask app"
    app.root_path = os.path.abspath('.')  # in case we launched from another dir

    CORS(app)  # allow cross-origin resource sharing (requests from other domains)

    Compress(app)  # send results using gzip

    app.config.from_mapping(
        SEND_FILE_MAX_AGE_DEFAULT=0,  # do not cache static files
        DATABASE=f'{app.instance_path}/trees.db',
        SECRET_KEY=' '.join(os.uname()))  # for testing, or else use config.py

    if os.path.exists(f'{app.instance_path}/config.py'):
        app.config.from_pyfile(f'{app.instance_path}/config.py')  # overrides


def add_resources(api):
    "Add all the REST endpoints"
    add = api.add_resource  # shortcut
    add(Login, '/login')
    add(Users, '/users', '/users/<int:user_id>')
    add(Drawers, '/drawers', '/drawers/<string:name>')
    add(Trees,
        '/trees',
        '/trees/<string:tree_id>',
        '/trees/<string:tree_id>/newick',
        '/trees/<string:tree_id>/draw',
        '/trees/<string:tree_id>/size',
        '/trees/<string:tree_id>/properties',
        '/trees/<string:tree_id>/nodecount',
        '/trees/<string:tree_id>/search',
        '/trees/<string:tree_id>/sort',
        '/trees/<string:tree_id>/root_at',
        '/trees/<string:tree_id>/move',
        '/trees/<string:tree_id>/remove',
        '/trees/<string:tree_id>/rename',
        '/trees/<string:tree_id>/reload')
    add(Info, '/info')
    add(Id, '/id/<path:path>')



app = initialize()

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']):
        create_example_database()

    app.run(debug=True, use_reloader=False)

# But for production it's better if we serve it with something like:
#   gunicorn server:app
