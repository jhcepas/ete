"""
Definition of the basic elements for a tree representation (Layout and
Decoration), extra labels (Label), and the default tree style.
"""

from collections import namedtuple
from dataclasses import dataclass, field
from functools import lru_cache
import inspect
import copy

from .faces import Face, PropFace


# Layouts have all the information needed to represent a tree.
#
# They compose. Using several layouts will add extra graphic
# representations, and/or overwrite some styles from previous layouts.
#
# They have a name and two functions providing the style and decorations of:
# - the full tree (for example rectangular/circular, with scale, etc.)
# - each visible node (called for each node) or group of collapsed sibling nodes

class Layout:
    """Contains all the info about how to represent a tree."""

    def __init__(self, name, draw_tree=None, draw_node=None, cache_size=None,
                 active=True):
        self.cache_size = cache_size  # used to cache functions in the setters

        # Name. This is mainly to activate/deactivate the layout in the gui.
        assert type(name) is str
        self.name = name

        # Tree representation (style and decorations).
        self.draw_tree = draw_tree

        # Node representation (style and decorations).
        self.draw_node = draw_node

        # Set if the layout should be initially active in the gui.
        self.active = active  # TODO: Find a better place for this

    @property
    def draw_tree(self):
        return self._draw_tree

    @draw_tree.setter
    def draw_tree(self, value):
        if value is None:
            self._draw_tree = lambda tree: [DEFAULT_TREE_STYLE]
        elif type(value) is dict:
            self._draw_tree = lambda tree: [DEFAULT_TREE_STYLE, value]
        elif callable(value):
            @lru_cache(maxsize=self.cache_size)
            def cached_draw_tree(tree):
                return [DEFAULT_TREE_STYLE] + to_elements(value(tree))
            self._draw_tree = cached_draw_tree
        else:
            raise ValueError('draw_tree can be either a dict or a function')

    @property
    def draw_node(self):
        return self._draw_node

    @draw_node.setter
    def draw_node(self, value):
        assert value is None or callable(value)

        if value is None:
            self._draw_node = lambda node, collapsed: []
            return

        f = value  # nicer name, since it is a function

        # We use an auxiliary function to cache its results.
        arity = len(inspect.signature(f).parameters)
        if arity == 1:  # f(node) (unspecified what to do with collapsed)
            @lru_cache(maxsize=self.cache_size)
            def cached_draw_node(node, collapsed):
                if not collapsed:
                    return to_elements(f(node))  # get just for the node
                else:
                    return [x for n in collapsed   # get from all siblings
                                for x in to_elements(f(n))]
        elif arity == 2:  # f(node, collapsed) (fully specified)
            @lru_cache(maxsize=self.cache_size)
            def cached_draw_node(node, collapsed):
                return to_elements(f(node, collapsed))
        else:
            raise ValueError('draw_node can have only 1 or 2 arguments.')

        self._draw_node = cached_draw_node  # use the auxiliary caching function


def to_elements(xs):
    """Return a list of the elements of iterable xs as Decorations/dicts."""
    # Normally xs is already a list of decorations/dicts.
    if xs is None:  # but xs can be None (a draw_node() didn't return anything)
        return []

    if type(xs) is dict:
        return [xs]

    if not hasattr(xs, '__iter__'):  # or it can be a single element
        return [xs if type(xs) is Decoration else Decoration(xs)]

    # Return elements, wrapped as Decorations if they need it.
    return [x if type(x) in [Decoration, dict] else Decoration(x) for x in xs]


DEFAULT_TREE_STYLE = {  # the default style of a tree
    'show-popup-props': ['dist', 'support'],
    'aliases': {  # to name styles that can be referenced in draw_node
        'dist': {'fill': '#888'},
        'support': {'fill': '#f88'},  # a light red
    }
}

# A tree style can have things like:
#   my_tree_style = {
#      'shape': 'circular',  # or 'rectangular'
#      'radius': 5,
#      'angle-start': -pi/2,
#      'angle-end': pi/2,  # alternatively we can give 'angle-span'
#      'node-height-min': 10,
#      'content-height-min': 5,
#      'collapsed': {'shape': 'outline', 'fill-opacity': 0.8},
#      'show-popup-props': None,  # all defined properties
#      'hide-popup-props': ['support'],  # except support
#      'is-leaf-fn': lambda node: node.level > 4,
#      'box': {'fill': 'green', 'opacity': 0.1, 'stroke': 'blue', 'border': 2},
#      'dot': {'shape': 'hexagon', 'fill': 'red'},
#      'hz-line': {'stroke-width': 2},
#      'vt-line': {'stroke': '#ffff00'},
#      'aliases': {
#          'support': {'fill': 'green'},  # changes the default one
#          'my-leaf': {'fill': 'blue', 'font-weight': 'bold'},
#   }
#
# Some properties will be used directly by the backend:
#   - shape, node-height-min, content-height-min,
#     radius, angle-start, angle-end, angle-span,
#     show-popup-props, hide-popup-props, is-leaf-fn
# Most  will be controlled by the css class of the element in the frontend:
#   - box, dot, hz-line, vt-line
# And the "aliases" part will tell the frontend which styles are referenced.

def update_style(style, style_new):
    """Update the style dictionary merging properly with style_new."""
    subdicts = {k for k in style_new if type(style_new[k]) is dict and
                                        type(style.get(k)) is dict}
    style.update((k, copy.deepcopy(v)) for k, v in style_new.items()
                     if k not in subdicts)
    for k in subdicts:
        update_style(style[k], style_new[k])


# A decoration is a face with a position ("top", "bottom", "right",
# etc.), a column (an integer used for relative order with other faces
# in the same position), and an anchor point (to fine-tune the
# position of things like texts within them).

@dataclass
class Decoration:
    face: Face
    position: str
    column: int
    anchor: tuple

    def __init__(self, face, position='top', column=0, anchor=None):
        self.face = face
        self.position = position
        self.column = column
        self.anchor = anchor or default_anchors[position]

default_anchors = {'top':     (-1, 1),   # left, bottom
                   'bottom':  (-1, -1),  # left, top
                   'right':   (-1, 0),   # left, middle
                   'left':    ( 1, 0),   # right, middle
                   'aligned': (-1, 0)}   # left, middle


# The default layout.

def default_draw_node(node, collapsed):
    if not collapsed:
        face_dist = PropFace('dist', '%.2g', style='dist')
        yield Decoration(face_dist, position='top')

        face_support = PropFace('support', '%.2g', style='support')
        yield Decoration(face_support, position='bottom')

    if node.is_leaf or collapsed:
        yield Decoration(PropFace('name'), position='right')

BASIC_LAYOUT = Layout(name='basic', draw_node=default_draw_node)


# Description of a label that we want to add to the representation of a node.

Label = namedtuple('Label', 'code style node_type position column anchor fs_max')
