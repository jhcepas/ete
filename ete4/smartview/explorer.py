#!/usr/bin/env python3

"""
Web server to explore trees interactively.

The main endpoints are for the static files to serve the frontend
(that uses javascript), and for exposing an api to manipulate the
trees in the backend.
"""

import sys
import os
import re
import json
import gzip, bz2, zipfile, tarfile
import socket
from math import pi
import webbrowser
from threading import Thread
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt
from wsgiref.simple_server import make_server, WSGIRequestHandler

import brotli

from bottle import (
    get, post, put, delete, redirect, static_file,
    request, response, error, abort, HTTPError, default_app)

DIR_BIN = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(DIR_BIN))  # so we can import ete w/o install

from ete4 import newick, nexus, operations as ops, treematcher as tm
from . import draw
from .layout import Layout, BASIC_LAYOUT, update_style

DIR_LIB = os.path.dirname(os.path.abspath(draw.__file__))


# Make sure we send the errors as json too.
@error(400)
@error(404)
def json_error(error):
    response.content_type = 'application/json'
    return json.dumps({'message': error.body})


def req_json():
    """Return what request.json would return, but gracefully aborting."""
    try:
        return json.loads(request.body.read())
    except json.JSONDecodeError as e:
        abort(400, f'bad json content: {e}')


def nice_html(content, title='Tree Explorer'):
    """Return the content as part of a nice-looking html page."""
    return f"""
<!DOCTYPE html>
<html><head><title>{title}</title>
<link rel="icon" type="image/png" href="/static/icon.png">
<link rel="stylesheet" href="/static/upload.css"></head>
<body><div class="centered">{content}</div></body></html>"""


# Routes.

@get('/')
def callback():
    if g_trees:
        if len(g_trees) == 1:
            name = list(g_trees.keys())[0]
            redirect(f'/static/gui.html?tree={name}')
        else:
            trees = '\n'.join('<li><a href="/static/gui.html?tree='
                              f'{name}">{name}</li>' for name in g_trees)
            return nice_html(f'<h1>Loaded Trees</h1><ul>\n{trees}\n</ul>')
    else:
        return nice_html("""<h1>Tree Explorer</h1>
<p>No trees loaded.</p>
<p>See the <a href="/help">help page</a> for more information.</p>""")

@get('/help')
def callback():
    return nice_html("""<h1>Help</h1>
You can go to the <a href="/static/upload.html">upload page</a>, see
a <a href="/">list of loaded trees</a>, or
<a href="http://etetoolkit.org/">consult the documentation</a>.""")

@get('/static/<path:path>')
def callback(path):
    return static_file(path, f'{DIR_LIB}/static')


@get('/api')
def callback():
    """Get all the available api endpoints and their documentation."""
    exclude = {"/", "/help", "/static/<path:path>"}  # excluded endpoints
    return {r.rule: r.callback.__doc__
            for r in default_app().routes if r.rule not in exclude}


@get('/trees')
def callback():
    """Get information about all the loaded trees."""
    response.content_type = 'application/json'
    return json.dumps([{'name': name, 'id': name} for name in g_trees])

# TODO: In the future we should not need this, since now the only
# property of a tree is its name, and we use it for its tree_id.
@get('/trees/<tree_id>')
def callback(tree_id):
    """Get information about the requested tree."""
    if tree_id in g_trees:
        return {'name': tree_id}
    else:
        abort(404, f'unknown tree {tree_id}')

@get('/trees/<tree_id>/size')
def callback(tree_id):
    """Get tree size as {'width': w, 'height': h}."""
    width, height = load_tree(tree_id).size
    return {'width': width, 'height': height}

@get('/trees/<tree_id>/nodecount')
def callback(tree_id):
    """Get the total number of nodes and leaves of the given tree."""
    t = load_tree(tree_id)
    return {'nnodes': sum(1 for node in t.traverse()),
            'nleaves': sum(1 for node in t.leaves())}

@get('/trees/<tree_id>/properties')
def callback(tree_id):
    """Get a list of the available properties for the tree."""
    t = load_tree(tree_id)
    props = set()
    for node in t.traverse():
        props |= node.props.keys()

    response.content_type = 'application/json'
    return json.dumps(list(props))

@get('/trees/<tree_id>/layouts')
def callback(tree_id):
    """Get the layout names and default options, available for the tree."""
    name, _ = get_tid(tree_id)  # "name" or "tid" is what identifies the tree
    layouts = g_layouts.get(name, [])  # layouts available for the tree
    return {layout.name: {'active': layout.active} for layout in layouts}

@get('/trees/<tree_id>/style')
def callback(tree_id):
    """Get the style of the tree according to all the active layouts."""
    try:
        args = request.query  # shortcut
        assert list(args.keys()) == ['active'], 'missing list of active layouts'

        active = set(json.loads(args['active']))

        t = load_tree(tree_id)

        name, _ = get_tid(tree_id)  # "name" or "tid" is what identifies the tree

        # Get the style of the tree according to all the layouts.
        style = {}
        for layout in g_layouts.get(name, []):
            if layout.name in active:
                for element in layout.draw_tree(t):
                    if type(element) is dict:
                        update_style(style, element)

        # Susbstitute aliases for their corresponding styles.
        aliasable_keys = {'box', 'dot', 'hz-line', 'vt-line', 'collapsed'}
        for k, v in style.items():
            if type(v) is str and k in aliasable_keys:
                aliases = set(style.get('aliases', {}).keys())
                assert v in aliases, f'unknown style "{v}" among {aliases}'
                style[k] = style['aliases'][v]
        # NOTE: The principal use of "aliases" is for the styles coming out of
        # calling draw_node() in the layouts. This is just an extra.

        # We remove is-leaf-fn because it is a function (thus not serializable).
        style.pop('is-leaf-fn', None)

        # We keep other parts like "aliases" if they are in the style, even if
        # the gui will not do anything with them.

        return style
    except (ValueError, AssertionError) as e:
        abort(400, str(e))

@get('/trees/<tree_id>/draw')
def callback(tree_id):
    """Get all the drawing commands to represent the tree."""
    try:
        kwargs = get_drawing_kwargs(tree_id, request.query)

        graphics = json.dumps(list(draw.draw(**kwargs))).encode('utf8')

        response.content_type = 'application/json'
        if g_config['compress']:
            response.add_header('Content-Encoding', 'br')
            return brotli.compress(graphics)
        else:
            return graphics
    except (AssertionError, SyntaxError) as e:
        abort(400, f'when drawing: {e}')

@get('/trees/<tree_id>/search')
def callback(tree_id):
    """Store a search, saving matching nodes so they can be later drawn."""
    nresults, nparents = store_search(tree_id, request.query)
    return {'message': 'ok', 'nresults': nresults, 'nparents': nparents}

@get('/trees/<tree_id>/newick')
def callback(tree_id):
    """Get the newick string that represents the tree."""
    MAX_MB = 2
    response.content_type = 'application/json'
    return json.dumps(get_newick(tree_id, MAX_MB))

@put('/trees/<tree_id>/clear_searches')
def callback(tree_id):
    """Remove all saved searches."""
    g_searches.clear()
    return {'message': 'ok'}

@put('/trees/<tree_id>/sort')
def callback(tree_id):
    """Sort the nodes in the tree according to the criteria in the request."""
    node_id, key_text, reverse = req_json()
    sort(tree_id, node_id, key_text, reverse)
    return {'message': 'ok'}

@put('/trees/<tree_id>/set_outgroup')
def callback(tree_id):
    """Set the requested node as an outgroup in the tree."""
    tid, subtree = get_tid(tree_id)
    if subtree:
        abort(400, 'operation not allowed with subtree')
    node_id = req_json()
    t = load_tree(tid)
    try:
        ops.set_outgroup(t[node_id])
        ops.update_sizes_all(t)
        return {'message': 'ok'}
    except AssertionError as e:
        abort(400, f'cannot root at {node_id}: {e}')

@put('/trees/<tree_id>/move')
def callback(tree_id):
    """Move the requested node up/down within its siblings."""
    try:
        t = load_tree(tree_id)
        node_id, shift = req_json()
        ops.move(t[node_id], shift)
        return {'message': 'ok'}
    except AssertionError as e:
        abort(400, f'cannot move {node_id}: {e}')

@put('/trees/<tree_id>/remove')
def callback(tree_id):
    """Remove the requested node (including descendants) from the tree."""
    try:
        t = load_tree(tree_id)
        node_id = req_json()
        ops.remove(t[node_id])
        ops.update_sizes_all(t)
        return {'message': 'ok'}
    except AssertionError as e:
        abort(400, f'cannot remove {node_id}: {e}')

@put('/trees/<tree_id>/rename')
def callback(tree_id):
    """Change name of the requested node in the tree."""
    try:
        t = load_tree(tree_id)
        node_id, name = req_json()
        t[node_id].name = name
        return {'message': 'ok'}
    except AssertionError as e:
        abort(400, f'cannot rename {node_id}: {e}')

@put('/trees/<tree_id>/edit')
def callback(tree_id):
    """Edit content (with newick notation) of the requested node in the tree."""
    try:
        t = load_tree(tree_id)
        node_id, content = req_json()
        node = t[node_id]
        node.props = newick.get_props(content, is_leaf=True)
        ops.update_sizes_all(t)
        return {'message': 'ok'}
    except (AssertionError, newick.NewickError) as e:
        abort(400, f'cannot edit {node_id}: {e}')

@put('/trees/<tree_id>/to_dendrogram')
def callback(tree_id):
    """Convert tree to dendrogram (remove all branch distances)."""
    node_id = req_json()
    t = load_tree(tree_id)
    ops.to_dendrogram(t[node_id])
    ops.update_sizes_all(t)
    return {'message': 'ok'}

@put('/trees/<tree_id>/to_ultrametric')
def callback(tree_id):
    """Convert tree to ultrametric (all leaves ending at the same distance)."""
    try:
        node_id = req_json()
        t = load_tree(tree_id)
        ops.to_ultrametric(t[node_id])
        ops.update_sizes_all(t)
        return {'message': 'ok'}
    except AssertionError as e:
        abort(400, f'cannot convert to ultrametric {tree_id}: {e}')

@post('/trees')
def callback():
    """Add a new tree."""
    ids = add_trees_from_request()
    response.status = 201
    return {'message': 'ok', 'ids': ids}

@delete('/trees/<tree_id>')
def callback(tree_id):
    """Remove a tree."""
    try:
        remove_tree(tree_id)
        return {'message': 'ok'}
    except KeyError as e:
        abort(404, f'unknown tree {tree_id}')


# Logic.

# Global variables.
g_trees = {}  # 'name' -> Tree
g_config = {'compress': False}  # global configuration
g_layouts = {}  # 'name' -> list of available layouts
g_searches = {}  # 'searched_text' -> ({result nodes}, {parent nodes})
g_threads = {}  # {'server': (thread, server)}

def load_tree(tree_id):
    """Add tree to g_trees and initialize it if not there, and return it."""
    try:
        tid, subtree = get_tid(tree_id)
        return g_trees[tid][subtree]
    except (KeyError, IndexError):
        abort(404, f'unknown tree id {tree_id}')


def get_tid(tree_id):
    """Return the tree id and the subtree id, with the appropriate types."""
    # Example: 'my_tree,1,0,1,1' -> ('my_tree', [1, 0, 1, 1])
    try:
        tid, *subtree = tree_id.split(',')
        return tid, [int(n) for n in subtree]
    except ValueError:
        abort(404, f'invalid tree id {tree_id}')


def get_newick(tree_id, max_mb):
    """Return the newick representation of the given tree."""
    t = load_tree(tree_id)

    nw = newick.dumps(t)

    size_mb = len(nw) / 1e6
    if size_mb > max_mb:
        abort(400, 'newick too big (%.3g MB)' % size_mb)

    return nw


def sort(tree_id, node_id, key_text, reverse):
    """Sort the (sub)tree corresponding to tree_id and node_id."""
    t = load_tree(tree_id)

    try:
        code = compile(key_text, '<string>', 'eval')
    except SyntaxError as e:
        abort(400, f'compiling expression: {e}')

    def key(node):
        return safer_eval(code, {
            'node': node, 'name': node.name, 'is_leaf': node.is_leaf,
            'length': node.dist, 'dist': node.dist, 'd': node.dist,
            'size': node.size, 'dx': node.size[0], 'dy': node.size[1],
            'children': node.children, 'ch': node.children,
            'len': len, 'sum': sum, 'abs': abs})

    ops.sort(t[node_id], key, reverse)


# Drawing arguments.

def get_drawing_kwargs(tree_id, args):
    """Return the drawing arguments initialized as specified in the args."""
    valid_keys = ['x', 'y', 'w', 'h', 'zx', 'zy',
                  'layouts', 'labels', 'collapsed_shape', 'collapsed_ids',
                  'shape', 'node_height_min', 'content_height_min',
                  'rmin', 'amin', 'amax']
    try:
        assert all(k in valid_keys for k in args.keys()), 'invalid keys'

        get = lambda x, default: float(args.get(x, default))  # shortcut

        tree = load_tree(tree_id)

        name, _ = get_tid(tree_id)  # "name" or "tid" is what identifies the tree

        # Active layouts.
        layout_names = json.loads(args.get('layouts', '[]'))  # active layouts
        layouts = [a for a in g_layouts.get(name, []) if a.name in layout_names]

        # Things that can be set in a tree style, and we override from the gui.
        shape = args.get('shape', 'rectangular')

        collapsed_shape = args.get('collapsed_shape', 'skeleton')

        node_height_min = get('node_height_min', 10)
        assert node_height_min > 0, 'node_height_min must be > 0'

        content_height_min = get('content_height_min', 5)
        assert content_height_min > 0, 'content_height_min must be > 0'

        overrides = {  # overrides of the tree style from the gui
            'shape': shape,
            'collapsed-shape': collapsed_shape,
            'node-height-min': node_height_min,
            'content-height-min': content_height_min}

        if shape == 'circular':
            overrides.update({
                'radius': get('rmin', 0),
                'angle-start': get('amin', -180),
                'angle-end': get('amax', 180)})

        # Get the rest: labels, viewport, zoom, collapsed_ids, searches.
        labels = json.loads(args.get('labels', '[]'))

        viewport = ([get(k, 0) for k in ['x', 'y', 'w', 'h']]
            if all(k in args for k in ['x', 'y', 'w', 'h']) else None)
        assert viewport is None or (viewport[2] > 0 and viewport[3] > 0), \
            'invalid viewport'  # width and height must be > 0

        zoom = (get('zx', 1), get('zy', 1))
        assert zoom[0] > 0 and zoom[1] > 0, 'zoom must be > 0'

        collapsed_ids = set(tuple(int(i) for i in node_id.split(',') if i != '')
            for node_id in json.loads(args.get('collapsed_ids', '[]')))

        searches = g_searches.get(tree_id)

        return {'tree': tree,
                'layouts': layouts,
                'overrides': overrides,
                'labels': labels,
                'viewport': viewport,
                'zoom': zoom,
                'collapsed_ids': collapsed_ids,
                'searches': searches}
    except (ValueError, AssertionError) as e:
        abort(400, str(e))


# Search.

def store_search(tree_id, args):
    """Store the results and parents of a search and return their numbers."""
    if 'text' not in args:
        abort(400, 'missing search text')

    text = args.pop('text').strip()
    func = get_search_function(text)

    try:
        tree = load_tree(tree_id)
        results = set(node for node in tree.traverse() if func(node))

        parents = set()  # all ancestors leading to the result nodes
        for node in results:
            current = node.up  # current node that we examine
            while current is not tree and current not in parents:
                parents.add(current)
                current = current.up  # go to its parent

        g_searches.setdefault(tree_id, {})[text] = (results, parents)

        return len(results), len(parents)
    except HTTPError:
        raise
    except Exception as e:
        abort(400, f'evaluating expression: {e}')


def get_search_function(text):
    """Return a function of a node that returns True for the searched nodes."""
    if text.startswith('/'):  # command-based search
        return get_command_search(text)
    elif text == text.lower():  # case-insensitive search
        return lambda node: text in node.props.get('name', '').lower()
    else:  # case-sensitive search
        return lambda node: text in node.props.get('name', '')


def get_command_search(text):
    """Return the appropriate node search function according to the command."""
    parts = text.split(None, 1)
    if parts[0] not in ['/r', '/e', '/t']:
        abort(400, 'invalid command %r' % parts[0])
    if len(parts) != 2:
        abort(400, 'missing argument to command %r' % parts[0])

    command, arg = parts
    if command == '/r':  # regex search
        return lambda node: re.search(arg, node.props.get('name', ''))
    elif command == '/e':  # eval expression
        return get_eval_search(arg)
    elif command == '/t':  # topological search
        return get_topological_search(arg)
    else:
        abort(400, 'invalid command %r' % command)


def get_eval_search(expression):
    """Return a function of a node that evaluates the given expression."""
    try:
        code = compile(expression, '<string>', 'eval')
    except SyntaxError as e:
        abort(400, f'compiling expression: {e}')

    return lambda node: safer_eval(code, {
        'node': node, 'parent': node.up, 'up': node.up,
        'name': node.name, 'is_leaf': node.is_leaf,
        'length': node.dist, 'dist': node.dist, 'd': node.dist,
        'properties': node.props, 'props': node.props, 'p': node.props,
        'get': dict.get,
        'children': node.children, 'ch': node.children,
        'size': node.size, 'dx': node.size[0], 'dy': node.size[1],
        'regex': re.search,
        'startswith': str.startswith, 'endswith': str.endswith,
        'upper': str.upper, 'lower': str.lower, 'split': str.split,
        'any': any, 'all': all, 'len': len,
        'sum': sum, 'abs': abs, 'float': float, 'pi': pi})


def safer_eval(code, context):
    """Return a safer version of eval(code, context)."""
    for name in code.co_names:
        if name not in context:
            abort(400, 'invalid use of %r during evaluation' % name)
    return eval(code, {'__builtins__': {}}, context)


def get_topological_search(pattern):
    """Return a function of a node that sees if it matches the given pattern."""
    try:
        tree_pattern = tm.TreePattern(pattern)
    except newick.NewickError as e:
        abort(400, 'invalid pattern %r: %s' % (pattern, e))

    return lambda node: tm.match(tree_pattern, node)


# Add trees.

def add_trees_from_request():
    """Add trees to the global var g_trees and return a dict of {name: id}."""
    try:
        if request.content_type.startswith('application/json'):
            trees = [req_json()]  # we have only one tree
            parser = newick.PARSER_DEFAULT
        else:
            trees = get_trees_from_form()
            parser = get_parser(request.forms['internal'])

        names = {}
        for tree in trees:
            t = newick.loads(tree['newick'], parser)
            ops.update_sizes_all(t)
            name = tree['name'].replace(',', '_')  # "," is used for subtrees
            names[name] = name  # tree ids are already equal to their names...
            g_trees[name] = t
            g_layouts[name] = [BASIC_LAYOUT]

        return names
        # TODO: tree ids are already equal to their names, so in the future
        # we could remove the need to send back their "ids".
    except (newick.NewickError, ValueError) as e:
        abort(400, f'malformed tree - {e}')


def get_parser(internal):
    """Return parser given the internal nodes main property interpretation."""
    p = {'name': newick.NAME, 'support': newick.SUPPORT}[internal]  # (()p:d);
    return dict(newick.PARSER_DEFAULT, internal=[p, newick.DIST])


def get_trees_from_form():
    """Return list of dicts with tree info read from a form in the request."""
    if 'trees' in request.files:
        try:
            fu = request.files['trees']  # bottle FileUpload object
            return get_trees_from_file(fu.filename, fu.file)
        except (gzip.BadGzipFile, UnicodeDecodeError) as e:
            abort(400, f'when reading {fupload.filename}: {e}')
    else:
        return [{'name': request.forms['name'],
                 'newick': request.forms['newick']}]


def get_trees_from_file(filename, fileobject=None):
    """Return list of {'name': ..., 'newick': ...} extracted from file."""
    fileobject = fileobject or open(filename, 'rb')

    trees = []
    def extend(btext, fname):
        name = os.path.splitext(os.path.basename(fname))[0]  # /d/n.e -> n
        trees.extend(get_trees_from_nexus_or_newick(btext, name))

    if filename.endswith('.zip'):
        zf = zipfile.ZipFile(fileobject)
        for fname in zf.namelist():
            extend(zf.read(fname), fname)
    elif filename.endswith('.tar'):
        tf = tarfile.TarFile(fileobj=fileobject)
        for fname in tf.getnames():
            extend(tf.extractfile(fname).read(), fname)
    elif filename.endswith('.tar.gz') or filename.endswith('.tgz'):
        tf = tarfile.TarFile(fileobj=gzip.GzipFile(fileobj=fileobject))
        for fname in tf.getnames():
            extend(tf.extractfile(fname).read(), fname)
    elif filename.endswith('.gz'):
        extend(gzip.GzipFile(fileobj=fileobject).read(), filename)
    elif filename.endswith('.bz2'):
        extend(bz2.BZ2File(fileobject).read(), filename)
    else:
        extend(fileobject.read(), filename)

    return trees


def get_trees_from_nexus_or_newick(btext, name_newick):
    """Return list of {'name': ..., 'newick': ...} extracted from btext."""
    text = btext.decode('utf8').strip()

    try:  # we first try to read it as a nexus file
        trees = nexus.get_trees(text)
        return [{'name': name, 'newick': nw} for name, nw in trees.items()]
    except nexus.NexusError:  # if it isn't, we assume the text is a newick
        return [{'name': name_newick, 'newick': text}]  # only one tree!


# Explore.

def explore(tree, name=None, layouts=None,
            host='127.0.0.1', port=None, verbose=False,
            compress=None, keep_server=False, open_browser=True,
            **kwargs):
    """Run the web server, add tree and open a browser to visualize it."""
    add_tree(tree, name, layouts, kwargs)

    if compress is not None:
        g_config['compress'] = compress  # global configuration

    # Launch the thread with the http server (if not already running).
    if 'server' not in g_threads:
        thread, server = start_server(host, port, verbose, keep_server)
        g_threads['server'] = (thread, server)
        host, port = server.server_address  # port may have changed
        print(f'Explorer now available at http://{host}:{port}')
    else:
        _, server = g_threads['server']
        host, port = server.server_address
        print(f'Existing explorer available at http://{host}:{port}')

    if open_browser:
        _, server = g_threads['server']
        host, port = server.server_address
        open_browser_window(host, port)


def add_tree(tree, name=None, layouts=None, extra_style=None):
    """Add tree, layouts, etc to the global variables, and return its name."""
    name = name or make_name()  # in case we didn't receive one

    ops.update_sizes_all(tree)  # update all internal sizes (ready to draw!)

    g_trees[name] = tree  # add tree to the global dict of trees

    g_layouts[name] = layouts if layouts is not None else [BASIC_LAYOUT]

    if extra_style:
        style = {k.replace('_', '-'): v for k, v in extra_style.items()}
        g_layouts[name].append(Layout(name='extra arguments', draw_tree=style))

    return name


def remove_tree(name):
    """Remove all global references to the tree."""
    g_trees.pop(name)
    g_layouts.pop(name)


def start_server(host='127.0.0.1', port=None, verbose=False, keep_server=False):
    """Create a thread running the web server and return it and the server."""
    port = port or get_next_available_port(host)
    assert port, 'could not find any port available'

    # Override the function that logs requests, if we are not verbose.
    if not verbose:
        WSGIRequestHandler.log_request = lambda *args, **kwargs: None

    # Create explicitly the web sever (uses internally WSGIRequestHandler).
    server = make_server(host, port, default_app())

    thread = Thread(
        daemon=not keep_server,  # the server persists if it's not a daemon
        target=server.serve_forever)

    thread.start()

    return thread, server


def get_next_available_port(host='127.0.0.1', port_min=5000, port_max=6000):
    """Return the next available port where we can put a server socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in range(port_min, port_max):
        try:
            sock.bind((host, port))  # try to bind to the specified port
            sock.close()
            return port
        except socket.error:
            pass


def make_name():
    """Return a unique tree name like 'tree-<number>'."""
    tnames = [name for name in g_trees
              if name.startswith('tree-') and name[len('tree-'):].isdecimal()]
    n = max((int(name[len('tree-'):]) for name in tnames), default=0) + 1
    return f'tree-{n}'


def open_browser_window(host='127.0.0.1', port=5000):
    """Try to open a browser window in a different process."""
    try:
        webbrowser.open(f'http://{host}:{port}')
    except webbrowser.Error:
        pass  # it's ok if we don't succeed


def stop_server():
    """Stop the running server."""
    if 'server' in g_threads:
        # Without a server, we won't need to remember anything about the trees.
        names = list(g_trees.keys())  # copied so g_trees can be modified
        for name in names:
            remove_tree(name)

        # Find the thread with the server and do a proper shutdown.
        thread, server = g_threads.pop('server')

        server.server_close()
        server.shutdown()
        thread.join()



if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)
    add = parser.add_argument  # shortcut
    add('FILE', help='file with the newick tree representation')
    add('-i', '--internal', choices=['name', 'support'], default='support',
        help='how to interpret the content of internal nodes')
    add('-c', '--compress', action='store_true', help='send compressed data')
    add('-p', '--port', type=int, help='server port number')
    add('-v', '--verbose', action='store_true', help='be verbose')
    args = parser.parse_args()

    try:
        # Read tree(s) and add them to g_trees.
        for tree in get_trees_from_file(args.FILE):
            t = newick.loads(tree['newick'], get_parser(args.internal))
            ops.update_sizes_all(t)
            name = tree['name'].replace(',', '_')  # "," is used for subtrees
            g_trees[name] = t
            g_layouts[name] = [BASIC_LAYOUT]

        # Set the global config options.
        g_config['compress'] = args.compress

        # Launch the http server in a thread and open the browser.
        port = args.port or get_next_available_port()
        assert port, 'could not find any port available'

        if not args.verbose:
            WSGIRequestHandler.log_request = lambda *args, **kwargs: None
        server = make_server('127.0.0.1', port, default_app())
        Thread(daemon=True, target=server.serve_forever).start()

        open_browser_window(port=port)

        print(f'Explorer available at http://127.0.0.1:{port}')
        input('Press enter to stop the server and finish.\n')
    except (FileNotFoundError, newick.NewickError, ValueError) as e:
        sys.exit(f'Error using tree from {args.FILE}: {e}')
    except (OSError, OverflowError) as e:
        sys.exit(f'Error listening at port {port}: {e}')
    except AssertionError as e:
        sys.exit(e)
    except (KeyboardInterrupt, EOFError):
        pass  # bye!
