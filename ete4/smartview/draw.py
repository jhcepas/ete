"""
Classes and functions for drawing a tree.
"""

from math import sin, cos, pi, sqrt, atan2

from ..core import operations as ops
from .coordinates import Size, Box, make_box, get_xs, get_ys
from .layout import Decoration, Label, update_style
from .faces import EvalTextFace
from . import graphics as gr


def draw(tree, layouts, overrides=None, labels=None,
         viewport=None, zoom=(1, 1), collapsed_ids=None, searches=None):
    """Yield graphic commands to draw the tree."""
    style = {}  # tree style
    decos = []  # tree decorations

    # Merge the style from all layouts, and get all decorations.
    for layout in layouts:
        for element in layout.draw_tree(tree):
            if type(element) is dict:
                update_style(style, element)
            else:
                decos.append(element)

    # NOTE: No need to susbstitute aliased values for their "aliases"
    # style, as opposed to the /style endpoint in explorer.py.
    # Those tree styles are applied (via gui.js) through css manipulation.

    # Override tree style (with options that normally come from the gui).
    style.update(overrides)

    # TODO: Draw the decos.

    drawer_class = {'rectangular': DrawerRect,
                    'circular':    DrawerCirc}[style['shape']]

    draw_node_fns = [layout.draw_node for layout in layouts]

    drawer_obj = drawer_class(tree, style, draw_node_fns, labels,
                              viewport, zoom, collapsed_ids, searches)

    yield from drawer_obj.draw()


class Drawer:
    """Base class (needs subclassing with extra functions to draw)."""

    def __init__(self, tree, tree_style=None, draw_node_fns=None, labels=None,
                 viewport=None, zoom=(1, 1), collapsed_ids=None, searches=None):
        self.tree = tree
        self.tree_style = tree_style or {}
        self.draw_node_fns = draw_node_fns or []
        self.labels = [read_label(label) for label in (labels or [])]
        self.viewport = Box(*viewport) if viewport else None
        self.zoom = zoom
        self.collapsed_ids = collapsed_ids or set()  # manually collapsed
        self.searches = searches or {}  # looks like {text: (results, parents)}

        # Get some useful constants from the tree style.

        # Any node that has less pixels will be collapsed.
        self.node_height_min = self.tree_style.get('node-height-min', 10)

        # Any content with less pixels won't be shown.
        self.content_height_min = self.tree_style.get('content-height-min', 5)

        # xmin, ymin, ymax used only for the circular mode for the moment.
        self.xmin, self.ymin, self.ymax = 0, 0, 0

    def draw(self):
        """Yield commands to draw the tree."""
        self.collapsed = []  # nodes that are curretly collapsed together
        self.outline = None  # box surrounding the current collapsed nodes
        self.nodeboxes = []  # boxes surrounding all nodes and collapsed boxes
        self.nodes_dx = [0]  # nodes dx, from root to current (with subnodes)
        self.bdy_dys = [[]]  # lists of branch dys and total dys
        self.xmax_reached = 0  # maximum x value we reached in the tree

        point = self.xmin, self.ymin

        for it in ops.walk(self.tree):
            graphics = []  # list that will contain the graphic elements to draw

            if it.first_visit:
                point = self.on_first_visit(point, it, graphics)
            else:
                point = self.on_last_visit(point, it, graphics)

            yield from graphics

        if self.collapsed:
            yield from self.flush_collapsed()  # send the remaining drawings

        # We have been collecting in postorder the boxes surrounding the nodes.
        # Draw them now in preorder (so they stack nicely, small over big ones).
        yield from self.nodeboxes[::-1]

        yield gr.set_xmax(self.xmax_reached)

    def on_first_visit(self, point, it, graphics):
        """Update list of graphics to draw and return new position."""
        box_node = make_box(point, self.node_size(it.node))
        x, y = point

        # Skip if not in viewport.
        if not self.is_visible(box_node):
            self.bdy_dys[-1].append( (box_node.dy / 2, box_node.dy) )
            it.descend = False  # skip children
            return x, y + box_node.dy

        # Deal with collapsed nodes.
        is_leaf_fn = self.tree_style.get('is-leaf-fn')
        is_collapsed = (it.node_id in self.collapsed_ids or
                        is_leaf_fn and is_leaf_fn(it.node))

        if self.collapsed and (is_collapsed or not self.is_small(self.outline)):
            graphics += self.flush_collapsed()  # don't stack more collapsed

        if is_collapsed or self.is_small(box_node):
            self.nodes_dx[-1] = max(self.nodes_dx[-1], box_node.dx)
            self.collapsed.append(it.node)
            self.outline = stack(self.outline, box_node)
            self.clip_outline()  # make sure self.outline has a reasonable box
            it.descend = False  # skip children
            return x, y + box_node.dy

        # If we arrive here, the node will be fully drawn (eventually).

        if self.collapsed:  # if there were previously collapsed nodes...
            graphics += self.flush_collapsed()  # draw and reset them

        self.bdy_dys.append([])  # we will store new branch dys and total dys

        dx, dy = self.content_size(it.node)
        if it.node.is_leaf:
            return self.on_last_visit((x + dx, y + dy), it, graphics)
        else:
            self.nodes_dx.append(0)  # keep track of the extra dx from children
            return x + dx, y

    def on_last_visit(self, point, it, graphics):
        """Update list of graphics to draw and return new position."""
        # This node (it.node) is being visited in post-order.
        if self.collapsed:  # we flush any pending collapsed nodes first
            graphics += self.flush_collapsed()

        x_after, y_after = point                         # before +--dx--+
        dx, dy = self.content_size(it.node)              #      dy|      |
        x_before, y_before = x_after - dx, y_after - dy  #        +------+ after

        style, content_graphics, xmax = self.draw_content(it.node,
                                                          (x_before, y_before))
        graphics += content_graphics
        self.xmax_reached = max(self.xmax_reached, xmax)

        # dx of the node including all its graphics and its children's.
        ndx = ((max(xmax, x_after) - x_before) if it.node.is_leaf else
               (dx + self.nodes_dx.pop()))
        self.nodes_dx[-1] = max(self.nodes_dx[-1], ndx)  # keep track of max(dx)

        box = Box(x_before, y_before, ndx, dy)
        result_of = [text for text,(results,_) in self.searches.items()
                        if it.node in results]
        self.nodeboxes += self.draw_nodebox(it.node, it.node_id, box, result_of,
                                            style.get('box', ''))

        return x_before, y_after

    def draw_content(self, node, point):
        """Return the node content's style, graphic commands and its xmax."""
        x, y = point
        dx, dy = self.content_size(node)
        box = Box(x, y, dx, dy)

        if not self.is_visible(box):
            return {}, [], x + dx

        commands = []  # will contain the graphics commands to return

        # Find branch dy to first child (bdy0), last (bdy1), and self (bdy).
        bdy_dys = self.bdy_dys.pop()  # bdy_dys[i] == (bdy, dy)

        if bdy_dys:
            bdy0 = bdy_dys[0][0]  # branch dy to first child

            dy_butlast = dy - bdy_dys[-1][1]  # dy of combined children but last
            bdy1 = dy_butlast + bdy_dys[-1][0]  # branch dy to last child
        else:
            bdy0 = bdy1 = dy / 2  # branch dys of the first and last children

        bdy = (bdy0 + bdy1) / 2  # this node's branch dy
        self.bdy_dys[-1].append( (bdy, dy) )

        # Get the drawing commands and style that the user wants for this node.
        style, node_commands, xmax = self.draw_nodes([node], box, bdy)

        # Draw the branch line ("hz_line").
        if dx > 0:
            parent_of = [text for text,(_,parents) in self.searches.items()
                             if node in parents]
            commands += self.draw_hz_line((x, y + bdy), (x + dx, y + bdy),
                                          parent_of,
                                          style=style.get('hz-line', ''))

        # Draw a line spanning all children ("vt_line").
        if bdy0 != bdy1:
            commands += self.draw_vt_line((x + dx, y + bdy0),
                                          (x + dx, y + bdy1),
                                          style=style.get('vt-line', ''))

        # Draw a dot on the node tip.
        dot_center = (x + dx, y + bdy)
        if self.is_visible(make_box(dot_center, (0, 0))):
            commands.append(gr.draw_nodedot(dot_center, dy_max=min(bdy, dy-bdy),
                                            style=style.get('dot', '')))

        return style, commands + node_commands, xmax

    def flush_collapsed(self):
        """Yield representation and graphics from collapsed nodes."""
        # This includes all the graphics for representing the collapsed nodes,
        # and empties self.outline and self.collapsed.
        result_of = [text for text,(results,parents) in self.searches.items()
            if any(node in results or node in parents
                   for node in self.collapsed)]

        graphics = []  # will contain the graphic commands to draw

        node0 = self.collapsed[0]
        uncollapse = len(self.collapsed) == 1 and node0.is_leaf  # single leaf?

        if not uncollapse:  # normal case: we represent the collapsed nodes
            graphics += self.draw_collapsed()  # it updates self.bdy_dys too

            style, collapsed_graphics, xmax = self.draw_nodes(
                self.collapsed, self.outline, self.outline.dy / 2)

            graphics += collapsed_graphics
        else:  # forced uncollapse: we simply draw node0's content
            self.bdy_dys.append([])  # empty list of extra bdy_dys to add
            x, y, _, _ = self.outline
            style, content_graphics, xmax = self.draw_content(node0, (x, y))
            graphics += content_graphics

        self.xmax_reached = max(self.xmax_reached, xmax)

        self.collapsed = []  # reset the list of currently collapsed nodes

        x, y, dx, dy = self.outline
        ndx = xmax - x

        self.nodes_dx[-1] = max(self.nodes_dx[-1], ndx)

        self.outline = None  # reset the outline box
        nodebox = Box(x, y, max(dx, ndx), dy)

        name, props = (('(collapsed)', {}) if not uncollapse else
                       (node0.name, self.get_nodeprops(node0)))
        box = gr.draw_nodebox(nodebox, name, props, node0.id, result_of,
                              style.get('collapsed', ''))
        self.nodeboxes.append(box)

        yield from graphics

    def draw_collapsed(self, *args, **kwargs):
        """Yield collapsed nodes representation."""
        # This is the shape of the outline. It also updates self.bdy_dys.
        x, y, dx, dy = self.outline
        _, zy = self.zoom

        shape = self.tree_style.get('collapsed-shape', 'skeleton')

        if shape == 'skeleton':
            points = points_from_nodes(self.collapsed, (x, y),
                                       self.content_height_min/zy,
                                       *args, **kwargs)  # for subclasses

            y1 = points[-1][1]  # last point's y (it is at branch position)
            self.bdy_dys[-1].append( (y1 - y, dy) )

            yield gr.draw_skeleton(points)
        elif shape == 'outline':
            self.bdy_dys[-1].append( (dy/2, dy) )

            yield gr.draw_outline(self.outline)
        else:
            raise ValueError(f'unrecognized collapsed shape: {shape!r}')

    def get_nodeprops(self, node):
        """Return the node properties that we want to show with the nodebox."""
        style = self.tree_style  # shortcut

        # Not present? use defaults; None? use all; else, use whatever they are.
        shown = (style['show-popup-props'] if 'show-popup-props' in style else
                 ['dist', 'support'])  # defaults
        shown = shown if shown is not None else node.props.keys()

        hidden = style.get('hide-popup-props') or []  # nothing special for None

        return {k: str(node.props[k]) for k in shown
                    if k in node.props and k not in hidden}
        # NOTE: So the properties appear in the order given in included.

    def draw_nodes(self, nodes, box, bdy, circular):  # bdy: branch dy (height)
        """Return style, graphic commands, and xmax for representing nodes."""
        style = {}  # style
        decos = []  # decorations

        # Add style and decorations from draw_node_fns (from layouts).
        for draw_node in self.draw_node_fns:
            for element in draw_node(nodes[0], tuple(self.collapsed)):
                # NOTE: draw_node() is cached: tuple(...) works (can be hashed).
                if type(element) is dict:
                    style.update(element)
                else:
                    decos.append(element)  # from layouts

        # Add decorations from labels.
        is_leaf = nodes[0].is_leaf or self.collapsed  # for is_valid_label()
        decos.extend(make_deco(label) for label in self.labels
                     if is_valid_label(label, is_leaf))

        # Get the graphic commands, and xmax, from applying the decorations.
        commands, xmax = draw_decorations(decos, nodes, self.xmin, box, bdy,
                                          self.zoom, self.content_height_min,
                                          collapsed=self.collapsed,
                                          circular=circular)

        return style, commands, xmax

def read_label(label):
    """Return a Label from the label description as a tuple."""
    expression, node_type, position, column, (ax, ay), fs_max = label

    assert node_type in ['leaf', 'internal', 'any'], \
        f'invalid node type: {node_type}'
    assert position in ['top', 'bottom', 'left', 'right', 'aligned'], \
        f'invalid position: {position}'

    def to_num(a):
        return float(a) if a is not None else None

    return Label(
        code=compile(expression, '<string>', 'eval'),
        style='label_'+expression,  # will be used to set its looks in css
        node_type=node_type,  # type of nodes to apply this label to
        position=position,  # top, bottom, left, right, aligned
        column=int(column),  # to locate relative to others in the same position
        anchor=(to_num(ax), to_num(ay)),  # point used for anchoring
        fs_max=fs_max)  # maximum font size (height in pixels)


class DrawerRect(Drawer):
    """Drawer for a rectangular representation."""

    def __init__(self, tree, tree_style=None, draw_node_fns=None, labels=None,
                 viewport=None, zoom=(1, 1), collapsed_ids=None, searches=None):
        super().__init__(tree, tree_style, draw_node_fns, labels,
                         viewport, zoom, collapsed_ids, searches)
        # We don't really need to define this function, but we do it
        # for symmetry, because in DrawerCirc it needs to do more things.

    def is_visible(self, box):
        """Return True if the node in box will produce something visible."""
        if not self.viewport:
            return True  # everything is visible if viewport is unrestricted

        return intersects_segment(get_ys(self.viewport), get_ys(box))
        # NOTE: If we didn't care about aligned items, we could restrict more:
        #   return intersects_box(self.viewport, box)

    def clip_outline(self):
        """Clip borders of outline to make sure that its box is reasonable."""
        pass  # this function exists only for symmetry with DrawerCirc

    def draw_collapsed(self):
        """Yield collapsed nodes representation with all the skeleton points."""
        yield from super().draw_collapsed()
        # For symmetry with DrawerCirc.

    def node_size(self, node):
        """Return the size of a node (its content and its children)."""
        return Size(node.size[0], node.size[1])

    def content_size(self, node):
        """Return the size of the node's content."""
        return Size(dist(node), node.size[1])

    def is_small(self, box):
        zx, zy = self.zoom
        return box.dy * zy < self.node_height_min

    def draw_hz_line(self, p1, p2, parent_of, style):
        """Yield a "horizontal line" representing a length."""
        line = gr.draw_hz_line(p1, p2, parent_of, style)
        if not self.viewport or intersects_box(self.viewport, get_rect(line)):
            yield line

    def draw_vt_line(self, p1, p2, style):
        """Yield a "vertical line" spanning children, from p1 to p2."""
        line = gr.draw_vt_line(p1, p2, style)
        if not self.viewport or intersects_box(self.viewport, get_rect(line)):
            yield line

    def draw_nodebox(self, node, node_id, box, result_of, style):
        props = self.get_nodeprops(node)
        yield gr.draw_nodebox(box, node.name, props, node_id, result_of, style)

    def draw_nodes(self, nodes, box, bdy):  # bdy: branch dy (height)
        """Return graphic commands for the contents of nodes, and xmax."""
        return super().draw_nodes(nodes, box, bdy, circular=False)


class DrawerCirc(Drawer):
    """Drawer for a circular representation."""

    def __init__(self, tree, tree_style=None, draw_node_fns=None, labels=None,
                 viewport=None, zoom=(1, 1), collapsed_ids=None, searches=None):
        super().__init__(tree, tree_style, draw_node_fns, labels,
                         viewport, zoom, collapsed_ids, searches)

        assert self.zoom[0] == self.zoom[1], 'zoom must be equal in x and y'

        self.xmin = self.tree_style.get('radius', 0)

        amin = self.tree_style.get('angle-start')
        amax = self.tree_style.get('angle-end')
        self.ymin = amin * pi/180 if amin is not None else -pi
        self.ymax = amax * pi/180 if amax is not None else +pi

        da = self.tree_style.get('angle-span')
        if da is not None:
            if amin is not None and amax is not None:
                assert abs(amax - (amin + da)) < 1e-10, \
                    'incompatible values: angle-start, angle-end, angle-span'
            if amin is not None:
                self.ymax = self.ymin + da * pi/180
            else:
                self.ymin = self.ymax - da * pi/180

        self.dy2da = (self.ymax - self.ymin) / self.tree.size[1]

    def is_visible(self, box):
        """Return True if the node in box will produce something visible."""
        if not self.viewport:
             # Just make sure the box has a valid angle.
            return intersects_segment((-pi, +pi), get_ys(box))

        return intersects_angles(self.viewport, box)
        # NOTE: If we didn't care about aligned items, we could restrict more:
        #   return (intersects_box(self.viewport, circumrect(box)) and
        #           intersects_segment((-pi, +pi), get_ys(box)))

    def clip_outline(self):
        """Clip borders of outline to make sure that its box is reasonable."""
        r, a, dr, da = self.outline
        a1, a2 = clip_angles(a, a + da)
        self.outline = Box(r, a1, dr, a2 - a1)

    def draw_collapsed(self):
        """Yield collapsed nodes representation with all the skeleton points."""
        yield from super().draw_collapsed(self.dy2da)

    def node_size(self, node):
        """Return the size of a node (its content and its children)."""
        return Size(node.size[0], node.size[1] * self.dy2da)

    def content_size(self, node):
        """Return the size of the node's content."""
        return Size(dist(node), node.size[1] * self.dy2da)

    def is_small(self, box):
        z = self.zoom[0]  # zx == zy in this drawer
        r, a, dr, da = box
        return (r + dr) * da * z < self.node_height_min

    def draw_hz_line(self, p1, p2, parent_of, style):
        """Yield a "horizontal line" representing a length."""
        if -pi <= p1[1] < pi:  # NOTE: the angles p1[1] and p2[1] are equal
            yield gr.draw_hz_line(p1, p2, parent_of, style)

    def draw_vt_line(self, p1, p2, style):
        """Yield a "vertical line" (arc) spanning children, from p1 to p2."""
        (r1, a1), (r2, a2) = p1, p2
        a1, a2 = clip_angles(a1, a2)
        if a1 < a2:
            yield gr.draw_vt_line((r1, a1), (r2, a2), style)

    def draw_nodebox(self, node, node_id, box, result_of, style):
        r, a, dr, da = box
        a1, a2 = clip_angles(a, a + da)
        if a1 < a2:
            props = self.get_nodeprops(node)
            yield gr.draw_nodebox(Box(r, a1, dr, a2 - a1),
                                  node.name, props, node_id, result_of, style)

    def draw_nodes(self, nodes, box, bda):  # bda: branch da (height)
        """Return graphic commands for the contents of nodes, and xmax."""
        return super().draw_nodes(nodes, box, bda, circular=True)


def clip_angles(a1, a2):
    """Return the angles such that a1 to a2 extend at maximum from -pi to pi."""
    EPSILON = 1e-8  # without it, p1 can be == p2 and svg arcs are not drawn
    return max(-pi + EPSILON, a1), min(pi - EPSILON, a2)


def cartesian(point):
    r, a = point
    return r * cos(a), r * sin(a)


def is_valid_label(label, is_leaf):
    """Return True if the given label would be drawn if it is/isn't a leaf."""
    ntype = label.node_type

    return ((ntype == 'any') or
            (ntype == 'leaf' and is_leaf) or
            (ntype == 'internal' and not is_leaf))


def make_deco(label):
    """Return a Decoration object from its description as a Label one."""
    face = EvalTextFace(label.code, fs_max=label.fs_max, style=label.style)
    return Decoration(face, label.position, label.column, label.anchor)


def draw_decorations(decorations, nodes, xmin, content_box, bdy, zoom,
                     min_size, collapsed, circular=False):
    """Return the graphic commands from the decorations, and xmax."""
    positions = {a.position for a in decorations}

    xmax = content_box.x + content_box.dx
    commands = []

    for pos in positions:
        if pos == 'aligned':
            commands.append(gr.set_panel(1))  # command to change to panel 1

        pos_box = get_position_box(content_box, bdy, pos)
        bdy_dy = bdy / content_box.dy

        # FIXME: This is a hack to add a little padding!
        # We should get the padding from the style instead.
        if pos == 'right':
            pos_box = Box(pos_box.x + 10/zoom[0], pos_box.y,
                          pos_box.dx, pos_box.dy)

        decos_at_pos = [a for a in decorations if a.position == pos]

        columns = sorted(set(a.column for a in decos_at_pos))
        ncols = len(columns)  # number of columns

        x_col = max(pos_box.x, xmin)  # where we start
        for icol, col in enumerate(columns):
            rows = [a for a in decos_at_pos if a.column == col]
            dx_col = (pos_box.dx - (x_col - pos_box.x)) / (ncols - icol)

            if (pos in ['left', 'right', 'aligned'] or  # in these, dx == 0
                dx_col * zoom[0] > min_size):           # means no limits for dx
                elements, x_col = get_col_data(rows, x_col, dx_col, nodes,
                                               pos_box, pos, bdy_dy, zoom,
                                               min_size, collapsed, circular)
                if pos != 'aligned':
                    xmax = max(xmax, x_col)
                commands += elements

        if pos == 'aligned':
            commands.append(gr.set_panel(0))  # command to change to panel 0

    return commands, xmax


def get_col_data(rows, x_col, dx_col, nodes, pos_box, pos, bdy_dy, zoom,
                 min_size, collapsed, circular=False):
    """Return the graphic elements at the given rows, and the new x_col."""
    # rows contains all the decorations that go in this column.
    # x_col is the starting x for this column (after all boxes in previos cols).
    # dx_col is the "allocated dx for this column".

    x_pos, y_pos, dx_pos, dy_pos = pos_box
    dx_max = 0  # will have the max dx of all the drawn elements
    nrows = len(rows)  # number of rows in this column

    blocks = []  # will contain the column data to send afterwards

    # Iterate over the decorations and get their graphics (none if
    # there's not enough space). We iterate reversed ([::-1]) so the
    # first decorations are the ones with more space (dy) allocated.
    dy_sum = 0
    ax, ay = None, None  # so we set the anchor only once per column
    for irow, deco in enumerate(rows[::-1]):  # iterate over all decorations
        if ax is None:  # anchor already set? then no more for this column!
            ax, ay = get_anchor(deco.anchor, pos, bdy_dy)

        dy_row = (dy_pos - dy_sum) / (nrows - irow)  # allocated dy for this row

        is_small = (dy_row * zoom[1] < min_size if not circular else
                    (pos != 'aligned' and  # circular aligned items always drawn
                     circular_dy(x_col, dx_col, dy_row) * zoom[1] < min_size))
        if is_small:
            continue  # skip if the available size is too small

        # Finally draw the face.
        r = x_pos if circular and pos != 'aligned' else 1  # "radius"
        elements, size = deco.face.draw(nodes, Size(dx_col, dy_row),
                                        collapsed, zoom, (ax, ay), r)
        blocks.append( (elements, size) )
        dx_max = max(dx_max, size.dx)
        dy_sum += size.dy

    # Get all the graphic elements appropriately positioned.
    y = y_pos + ay * (dy_pos - dy_sum)  # starting y position for the blocks
    elements_all = []  # all the graphic elements to send
    if ay <= 0.5:
        blocks.reverse()  # we want the 1st block closer to its anchor point
    for elements, size in blocks:
        elements_all += gr.draw_group(elements, circular, shift=(x_col, y))
        y += size.dy

    return elements_all, x_col + dx_max


def get_position_box(content_box, bdy, position):
    """Return the box corresponding to the given box and position."""
    x, y, dx, dy = content_box
    p = position
    if   p == 'top':     return Box(x     , y      , dx, bdy     )
    elif p == 'bottom':  return Box(x     , y + bdy, dx, dy - bdy)
    elif p == 'left':    return Box(x - dx, y      , dx, dy      )
    elif p == 'right':   return Box(x + dx, y      , 0 , dy      )
    elif p == 'aligned': return Box(0     , y      , 0 , dy      )
    else: raise ValueError(f'unknown position: {p}')


def get_anchor(anchor, pos, bdy_dy):
    """Return the anchor inside [0, 1] from the one inside [-1, 1] at pos."""
    # From the gui we have an anchor inside [-1, 1], where 0 means "branch
    # position" for the y. This function returns the anchor inside [0, 1].
    ax, ay = anchor

    if ax is None or ay is None:  # not specified? use defaults for position
        default_ax, default_ay = default_anchor(pos)
        ax = ax if ax is not None else default_ax
        ay = ay if ay is not None else default_ay

    # Transform anchor from [-1, -1] to [0, 1] (with 0 -> bdy / content_box.dy).
    ax = (ax + 1) * 0.5
    if pos in ['left', 'right', 'aligned']:
        ax = 1 if pos == 'left' else 0  # x anchor does not make sense in these
        ay = (ay + 1) * bdy_dy if ay < 0 else bdy_dy + ay * (1 - bdy_dy)
    else:
        ay = (ay + 1) * 0.5  # for 'top' or 'bottom'

    return ax, ay


def default_anchor(position):
    """Return the default anchor point for the given position."""
    # The x, y go between -1 to +1, with 0 the center.
    p = position
    if   p == 'top':     return ( 0,  1)  # x centered, y bottom (touching the branch)
    elif p == 'bottom':  return ( 0, -1)  # x centered, y top (touching the branch)
    elif p == 'left':    return ( 1,  0)  # x right, y centered (at branch y)
    elif p == 'right':   return (-1,  0)  # x left, y centered (at branch y)
    elif p == 'aligned': return (-1,  0)  # x left, y centered (at branch y)
    else: raise ValueError(f'unknown position: {p}')


def circular_dy(r, dr, da):
    """Return the dy corresponding to the exterior part of an annular sector."""
    return (r + dr) * da if r > 0 else 0  # but dy=0 if r=0 (no interior part)


# Box-related functions.

def get_rect(element):
    """Return the rectangle that contains the given graphic element."""
    eid = element[0]
    if eid in ['nodebox', 'array', 'text']:
        return element[1]
    elif eid == 'collapsed':
        points = element[1]
        x, y = points[0]
        return Box(x, y, 0, 0)  # we don't care for the rect of this element
    elif eid in ['line', 'hz-line', 'vt-line']:
        (x1, y1), (x2, y2) = element[1], element[2]
        return Box(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    elif eid in ['arc']:  # not a great approximation for an arc...
        (x1, y1), (x2, y2) = cartesian(element[1]), cartesian(element[2])
        return Box(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    elif eid == 'circle':
        (x, y), r = element[1], element[2]
        return Box(x, y, 0, 0)
    else:
        raise ValueError(f'unrecognized element: {element!r}')


def intersects_box(b1, b2):
    """Return True if the boxes b1 and b2 (of the same kind) intersect."""
    return (intersects_segment(get_xs(b1), get_xs(b2)) and
            intersects_segment(get_ys(b1), get_ys(b2)))


def intersects_segment(s1, s2):
    """Return True if the segments s1 and s2 intersect."""
    s1min, s1max = s1
    s2min, s2max = s2
    return s1min <= s2max and s2min <= s1max


def intersects_angles(rect, asec):
    """Return True if any part of rect is contained within the asec angles."""
    return any(intersects_segment(get_ys(circumasec(r)), get_ys(asec))
                   for r in split_thru_negative_xaxis(rect))
    # We divide rect in two if it passes thru the -x axis, because then its
    # circumbscribing asec goes from -pi to +pi and (wrongly) always intersects.


def split_thru_negative_xaxis(rect):
    """Return a list of rectangles resulting from cutting the given one."""
    x, y, dx, dy = rect
    if x >= 0 or y > 0 or y + dy < 0:
        return [rect]
    else:
        EPSILON = 1e-8
        return [Box(x, y, dx, -y-EPSILON), Box(x, EPSILON, dx, dy + y)]


def stack(box1, box2):
    """Return the box resulting from stacking the given boxes."""
    if not box1:
        return box2
    else:
        x, y, dx1, dy1 = box1
        _, _, dx2, dy2 = box2
        return Box(x, y, max(dx1, dx2), dy1 + dy2)


def points_from_nodes(nodes, point, dy_min, dy2da=1, maxdepth=30):
    """Return the points sketching the given nodes, starting at point."""
    x, y = point  # top-left origin at point
    dx, dy = 0, 0  # defined here so they can be accessed inside add_points()
    points = []  # the actual points we are interested in
    abox = [x, y, 0, 0]  # box surrounding the accumulated node boxes
    def add_points(ps):
        if abox[-1] > dy_min:
            points.extend(corner_points(*abox))
        points.extend(ps)
        abox[:] = [x, y+dy, 0, 0]

    for node in nodes:
        dx, dy = node.size[0], node.size[1] * dy2da
        if maxdepth < 0:  # we went too far: add bounding box
            add_points(corner_points(x, y, dx, dy))
        elif dy < dy_min:  # too small to peek inside
            if dy < 0.2 * dy_min:  # and even to try to draw
                ax, ay, adx, ady = abox
                abox = [ax, ay, max(adx, dx), ady+dy]  # accumulate it!
            else:  # small, but no too small
                add_points(corner_points(x, y, dx, dy))  # just add bounding box
        else:
            add_points(points_from_node(node, (x, y), dy_min,
                                        dy2da, maxdepth-1))
        y += dy

    if abox[-1] > 0:  # do we still have any accumulated box of points?
        points.extend(corner_points(*abox))  # flush remaining points

    if len(nodes) < 2:
        return points
    else:
        by = (points[0][1] + points[-1][1]) / 2
        return [(x, by)] + points + [(x, by)]


def points_from_node(node, point, dy_min, dy2da=1, maxdepth=30):
    """Return the points sketching the given node, starting at point."""
    x, y = point
    dx, dy = dist(node), node.size[1] * dy2da

    points = points_from_nodes(node.children, (x + dx, y), dy_min,
                               dy2da, maxdepth-1)

    by = ((points[0][1] + points[-1][1]) / 2) if points else (y + dy/2)

    return ([(x, by), (x + dx, by)] +
            points +
            [(x + dx, by), (x, by)])


def corner_points(x, y, dx, dy):
    """Return the corner points of a box at (x, y) and dimensions (dx, dy)."""
    return [(x, y),                   # 1    1,5.-----.2
                       (x+dx, y),     # 2       |     |
                       (x+dx, y+dy),  # 3       |     |
            (x, y+dy),                # 4      4·-----·3
            (x, y)]                   # 5 (same as 1, closing the box)


def dist(node):
    """Return the distance of a node, with default values if not set."""
    default = 0 if node.up is None else 1
    return float(node.props.get('dist', default))


def circumasec(rect):
    """Return the annular sector that circumscribes the given rectangle."""
    if rect is None:
        return None

    x, y, dx, dy = rect

    points = [(x, y), (x, y+dy), (x+dx, y), (x+dx, y+dy)]
    radius2 = [x*x + y*y for x,y in points]

    if x <= 0 and x+dx >= 0 and y <= 0 and y+dy >= 0:
        return Box(0, -pi, sqrt(max(radius2)), 2*pi)
    else:
        angles = [atan2(y, x) for x,y in points]
        rmin, amin = sqrt(min(radius2)), min(angles)

        return Box(rmin, amin, sqrt(max(radius2)) - rmin, max(angles) - amin)
