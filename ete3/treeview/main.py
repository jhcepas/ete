# #START_LICENSE###########################################################
#
#
# This file is part of the Environment for Tree Exploration program
# (ETE).  http://etetoolkit.org
#
# ETE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ETE is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ETE.  If not, see <http://www.gnu.org/licenses/>.
#
#
#                     ABOUT THE ETE PACKAGE
#                     =====================
#
# ETE is distributed under the GPL copyleft license (2008-2015).
#
# If you make use of ETE in published work, please cite:
#
# Jaime Huerta-Cepas, Joaquin Dopazo and Toni Gabaldon.
# ETE: a python Environment for Tree Exploration. Jaime BMC
# Bioinformatics 2010,:24doi:10.1186/1471-2105-11-24
#
# Note that extra references to the specific methods implemented in
# the toolkit may be available in the documentation.
#
# More info at http://etetoolkit.org. Contact: huerta@embl.de
#
#
# #END_LICENSE#############################################################
from __future__ import absolute_import
from __future__ import print_function

import colorsys
import random
import re
import types
from sys import stderr

from .qt import *

from .svg_colors import SVG_COLORS, COLOR_SCHEMES

import time
def tracktime(f):
    def a_wrapper_accepting_arguments(*args, **kargs):
        t1 = time.time()
        r = f(*args, **kargs)
        print("                         -> TIME:", f.__name__, time.time() - t1)
        return r
    return a_wrapper_accepting_arguments


_LINE_TYPE_CHECKER = lambda x: x in (0,1,2)
_SIZE_CHECKER = lambda x: isinstance(x, int)
_COLOR_MATCH = re.compile("^#[A-Fa-f\d]{6}$")
_COLOR_CHECKER = lambda x: x.lower() in SVG_COLORS or re.match(_COLOR_MATCH, x)
_NODE_TYPE_CHECKER = lambda x: x in ["sphere", "circle", "square"]
_BOOL_CHECKER =  lambda x: isinstance(x, bool) or x in (0,1)

FACE_POSITIONS = set(["branch-right", "branch-top", "branch-bottom", "float", "float-behind", "aligned"])

__all__  = ["NodeStyle", "TreeStyle", "FaceContainer", "_leaf", "add_face_to_node", "COLOR_SCHEMES"]

NODE_STYLE_DEFAULT = [
    ["fgcolor",          "#0030c1",    _COLOR_CHECKER                           ],
    ["bgcolor",          "#FFFFFF",    _COLOR_CHECKER                           ],
    #["node_bgcolor",     "#FFFFFF",    _COLOR_CHECKER                           ],
    #["partition_bgcolor","#FFFFFF",    _COLOR_CHECKER                           ],
    #["faces_bgcolor",    "#FFFFFF",    _COLOR_CHECKER                           ],
    ["vt_line_color",    "#000000",    _COLOR_CHECKER                           ],
    ["hz_line_color",    "#000000",    _COLOR_CHECKER                           ],
    ["hz_line_type",     0,            _LINE_TYPE_CHECKER                       ], # 0 solid, 1 dashed, 2 dotted
    ["vt_line_type",     0,            _LINE_TYPE_CHECKER                       ], # 0 solid, 1 dashed, 2 dotted
    ["size",             3,            _SIZE_CHECKER                            ], # node circle size
    ["shape",            "circle",     _NODE_TYPE_CHECKER                       ],
    ["draw_descendants", True,         _BOOL_CHECKER                            ],
    ["hz_line_width",          0,      _SIZE_CHECKER                            ],
    ["vt_line_width",          0,      _SIZE_CHECKER                            ]
    ]

TREE_STYLE_CHECKER = {
    "mode": lambda x: x.lower() in set(["c", "r"]),
    }

# _faces and faces are registered to allow deepcopy to work on nodes
VALID_NODE_STYLE_KEYS = set([i[0] for i in NODE_STYLE_DEFAULT]) | set(["_faces"])

class _Border(object):
    def __init__(self):
        self.width = None
        self.type = 0
        self.color = None

    def apply(self, item):
        if self.width is not None:
            r = item.boundingRect()
            border = QGraphicsRectItem(r)
            border.setParentItem(item)
            if self.color:
                pen = QPen(QColor(self.color))
            else:
                pen = QPen(Qt.NoPen)
            set_pen_style(pen, self.type)
            pen.setWidth(self.width)
            pen.setCapStyle(Qt.FlatCap)
            border.setPen(pen)
            return border
        else:
            return None

class _Background(object):
    """
    Set the background of the object

    :param color: RGB color code or :data:`SVG_COLORS`

    """
    def __init__(self):
        self.color = None

    def apply(self, item):
        if self.color:
            r = item.boundingRect()
            bg = QGraphicsRectItem(r)
            bg.setParentItem(item)
            pen = QPen(QColor(self.color))
            brush = QBrush(QColor(self.color))
            bg.setPen(pen)
            bg.setBrush(brush)
            bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
            return bg
        else:
            return None


class _ActionDelegator(object):
    """ Used to associate GUI Functions to nodes and faces """

    def get_delegate(self):
        return self._delegate

    def set_delegate(self, delegate):
        if hasattr(delegate, "init"):
            delegate.init(self)

        for attr in dir(delegate):
            if not attr.startswith("_") and attr != "init" :
                fn = getattr(delegate, attr)
                setattr(self, attr, types.MethodType(fn, self))
        self._delegate = delegate

    delegate = property(get_delegate, set_delegate)

    def __init__(self):
        self._delegate = None

class NodeStyle(dict):
    """
    .. versionadded:: 2.1

    .. currentmodule:: ete3

    A dictionary with all valid node graphical attributes.

    :argument #0030c1 fgcolor: RGB code or name in :data:`SVG_COLORS`
    :argument #FFFFFF bgcolor: RGB code or name in :data:`SVG_COLORS`
    :argument #FFFFFF node_bgcolor: RGB code or name in :data:`SVG_COLORS`
    :argument #FFFFFF partition_bgcolor: RGB code or name in :data:`SVG_COLORS`
    :argument #FFFFFF faces_bgcolor: RGB code or name in :data:`SVG_COLORS`
    :argument #000000 vt_line_color: RGB code or name in :data:`SVG_COLORS`
    :argument #000000 hz_line_color: RGB code or name in :data:`SVG_COLORS`
    :argument 0 hz_line_type: integer number
    :argument 0 vt_line_type: integer number
    :argument 3 size: integer number
    :argument "circle" shape: "circle", "square" or "sphere"
    :argument True draw_descendants: Mark an internal node as a leaf.

    :argument 0 hz_line_width: integer number representing the width
                               of the line in pixels.  A line width of
                               zero indicates a cosmetic pen. This
                               means that the pen width is always
                               drawn one pixel wide, independent of
                               the transformation set on the painter.

    :argument 0 vt_line_width: integer number representing the width
                               of the line in pixels.  A line width of
                               zero indicates a cosmetic pen. This
                               means that the pen width is always
                               drawn one pixel wide, independent of
                               the transformation set on the painter.

    """

    def __init__(self, *args, **kargs):
        super(NodeStyle, self).__init__(*args, **kargs)
        self.init()
        #self._block_adding_faces = False

    def init(self):
        for key, dvalue, checker in NODE_STYLE_DEFAULT:
            if key not in self:
                self[key] = dvalue
            elif not checker(self[key]):
                raise ValueError("'%s' attribute in node style has not a valid value: %s" %\
                                     (key, self[key]))
    #
    #    #super(NodeStyle, self).__setitem__("_faces", {})
    #    # copy fixed faces to the faces dict that will be drawn
    #    #for pos, values in self["faces"].iteritems():
    #    #    for col, faces in values.iteritems():
    #    #        self["_faces"].setdefault(pos, {})
    #    #        self["_faces"][pos][col] = list(faces)

    def __setitem__(self, i, v):
        # keeps compatible with ETE 2.0 version
        if i == "line_type":
            print("WARNING: [%s] keyword is deprecated and it has been replaced by %s." %\
                (i, "[hz_line_type, vt_line_type]"), file=stderr)
            print("WARNING: Support for this keyword will be removed in next ETE versions.", file=stderr)
            super(NodeStyle, self).__setitem__("hz_line_type", v)
            i = "vt_line_type"

        if i == "vlwidth":
            i = "vt_line_width"
            print("WARNING: [%s] keyword is deprecated and it has been replaced by %s." %\
                (i, "[vt_line_width]"), file=stderr)
            print("WARNING: Support for this keyword will be removed in next ETE versions.", file=stderr)
        if i == "hlwidth":
            i = "hz_line_width"
            print("WARNING: [%s] keyword is deprecated and it has been replaced by %s." %\
                (i, "[hz_line_width]"), file=stderr)
            print("WARNING: Support for this keyword will be removed in next ETE versions.", file=stderr)

        if i not in VALID_NODE_STYLE_KEYS:
            raise ValueError("'%s' is not a valid keyword for a NodeStyle instance" %i)

        super(NodeStyle, self).__setitem__(i, v)

    #def clear(self):
    #    super(NodeStyle, self).__setitem__("_faces", {})

class TreeStyle(object):
    """.. versionadded:: 2.1

    .. currentmodule:: ete3

    Contains all the general image properties used to render a tree

    **-- About tree design --**

    :param None layout_fn: Layout function used to dynamically control
      the aspect of nodes. Valid values are: None or a pointer to a method,
      function, etc.

    **-- About tree shape --**

    :param "r" mode: Valid modes are 'c'(ircular)  or 'r'(ectangular).

    :param 0 orientation: If 0, tree is drawn from left-to-right. If
       1, tree is drawn from right-to-left. This property only makes
       sense when "r" mode is used.

    :param 0 rotation: Tree figure will be rotate X degrees (clock-wise
       rotation).

    :param 1 min_leaf_separation: Min separation, in pixels, between
      two adjacent branches

    :param 0 branch_vertical_margin: Leaf branch separation margin, in
      pixels. This will add a separation of X pixels between adjacent
      leaf branches. In practice, increasing this value work as
      increasing Y axis scale.

    :param 0 arc_start: When circular trees are drawn, this defines the
      starting angle (in degrees) from which leaves are distributed
      (clock-wise) around the total arc span (0 = 3 o'clock).

    :param 359 arc_span: Total arc used to draw circular trees (in
      degrees).

    :param 0 margin_left: Left tree image margin, in pixels.
    :param 0 margin_right: Right tree image margin, in pixels.
    :param 0 margin_top: Top tree image margin, in pixels.
    :param 0 margin_bottom: Bottom tree image margin, in pixels.

    **-- About Tree branches --**

    :param None scale: Scale used to draw branch lengths. If None, it will
      be automatically calculated.

    :param "mid" optimal_scale_level: Two levels of automatic branch
      scale detection are available: :attr:`"mid"` and
      :attr:`"full"`. In :attr:`full` mode, branch scale will me
      adjusted to fully avoid dotted lines in the tree image. In other
      words, scale will be increased until the extra space necessary
      to allocated all branch-top/bottom faces and branch-right faces
      (in circular mode) is covered by real branches. Note, however,
      that the optimal scale in trees with very unbalanced branch
      lengths might be huge. If :attr:`"mid"` mode is selected (as it is by default),
      optimal scale will only satisfy the space necessary to allocate
      branch-right faces in circular trees. Some dotted lines
      (artificial branch offsets) will still appear when
      branch-top/bottom faces are larger than branch length. Note that
      both options apply only when :attr:`scale` is set to None
      (automatic).

    :param 0.25 root_opening_factor: (from 0 to 1). It defines how much the center of
      a circular tree could be opened when adjusting optimal scale, referred
      to the total tree length. By default (0.25), a blank space up to 4
      times smaller than the tree width could be used to calculate the
      optimal tree scale. A 0 value would mean that root node should
      always be tightly adjusted to the center of the tree.

    :param True complete_branch_lines_when_necessary: True or False.
      Draws an extra line (dotted by default) to complete branch lengths when the space to cover is larger than the branch itself.

    :param 2 extra_branch_line_type:  0=solid, 1=dashed, 2=dotted

    :param "gray" extra_branch_line_color: RGB code or name in
      :data:`SVG_COLORS`

    :param False force_topology: Convert tree branches to a fixed length, thus allowing to
      observe the topology of tight nodes

    :param False draw_guiding_lines: Draw guidelines from leaf nodes
      to aligned faces

    :param 2 guiding_lines_type: 0=solid, 1=dashed, 2=dotted.

    :param "gray" guiding_lines_color: RGB code or name in :data:`SVG_COLORS`

    **-- About node faces --**

    :param False allow_face_overlap: If True, node faces are not taken
      into account to scale circular tree images, just like many other
      visualization programs. Overlapping among branch elements (such
      as node labels) will be therefore ignored, and tree size
      will be a lot smaller. Note that in most cases, manual setting
      of tree scale will be also necessary.

    :param True draw_aligned_faces_as_table: Aligned faces will be
      drawn as a table, considering all columns in all node faces.

    :param True children_faces_on_top: When floating faces from
      different nodes overlap, children faces are drawn on top of
      parent faces. This can be reversed by setting this attribute
      to false.

    **-- Addons --**

    :param False show_border: Draw a border around the whole tree

    :param True show_scale: Include the scale legend in the tree
      image

    :param None scale_length: Scale length to be used as reference scale bar
    when visualizing tree. None = automatically adjusted.

    :param False show_leaf_name: Automatically adds a text Face to
      leaf nodes showing their names

    :param False show_branch_length: Automatically adds branch
      length information on top of branches

    :param False show_branch_support: Automatically adds branch
      support text in the bottom of tree branches

    **-- Tree surroundings --**

    The following options are actually Face containers, so graphical
    elements can be added just as it is done with nodes. In example,
    to add tree legend:

       ::

          TreeStyle.legend.add_face(CircleFace(10, "red"), column=0)
          TreeStyle.legend.add_face(TextFace("0.5 support"), column=1)

    :param aligned_header: a :class:`FaceContainer` aligned to the end
      of the tree and placed at the top part.

    :param aligned_foot: a :class:`FaceContainer` aligned to the end
      of the tree and placed at the bottom part.

    :param legend: a :class:`FaceContainer` with an arbitrary number of faces
      representing the legend of the figure.
    :param 4 legend_position=4: TopLeft corner if 1, TopRight
      if 2, BottomLeft if 3, BottomRight if 4

    :param title: A Face container that can be used as tree title

    """

    def set_layout_fn(self, layout):
        self._layout_handler = []
        if type(layout) not in set([list, set, tuple, frozenset]):
            layout = [layout]

        for ly in layout:
            # Validates layout function
            if (type(ly) == types.FunctionType or type(ly) == types.MethodType or ly is None):
                self._layout_handler.append(ly)
            else:
                from . import layouts
                try:
                    self._layout_handler.append(getattr(layouts, ly))
                except Exception as e:
                    print(e)
                    raise ValueError ("Required layout is not a function pointer nor a valid layout name.")

    def get_layout_fn(self):
        return self._layout_handler

    layout_fn = property(get_layout_fn, set_layout_fn)

    def __init__(self):
        # :::::::::::::::::::::::::
        # TREE SHAPE AND SIZE
        # :::::::::::::::::::::::::

        # Valid modes are : "c" or "r"
        self.mode = "r"

        # Applies only for circular mode. It prevents aligned faces to
        # overlap each other by increasing the radius.
        self.allow_face_overlap = False

        # Layout function used to dynamically control the aspect of
        # nodes
        self._layout_handler = []

        # 0= tree is drawn from left-to-right 1= tree is drawn from
        # right-to-left. This property only has sense when "r" mode
        # is used.
        self.orientation = 0

        # Tree rotation in degrees (clock-wise rotation)
        self.rotation = 0

        # Scale used to convert branch lengths to pixels. If 'None',
        # the scale will be automatically calculated.
        self.scale = None

        # How much the center of a circular tree can be opened,
        # referred to the total tree length.
        self.root_opening_factor = 0.25

        # mid, or full
        self.optimal_scale_level = "mid"

        # Min separation, in pixels, between to adjacent branches
        self.min_leaf_separation = 1

        # Leaf branch separation margin, in pixels. This will add a
        # separation of X pixels between adjacent leaf branches. In
        # practice this produces a Y-zoom in.
        self.branch_vertical_margin = 0

        # When circular trees are drawn, this defines the starting
        # angle (in degrees) from which leaves are distributed
        # (clock-wise) around the total arc. 0 = 3 o'clock
        self.arc_start = 0

        # Total arc used to draw circular trees (in degrees)
        self.arc_span = 359

        # Margins around tree picture
        self.margin_left = 1
        self.margin_right = 1
        self.margin_top = 1
        self.margin_bottom = 1

        # :::::::::::::::::::::::::
        # TREE BRANCHES
        # :::::::::::::::::::::::::

        # When top-branch and bottom-branch faces are larger than
        # branch length, branch line can be completed. Also, when
        # circular trees are drawn,
        self.complete_branch_lines_when_necessary = True
        self.extra_branch_line_type = 2 # 0 solid, 1 dashed, 2 dotted
        self.extra_branch_line_color = "gray"

        # Convert tree branches to a fixed length, thus allowing to
        # observe the topology of tight nodes
        self.force_topology = False

        # Draw guidelines from leaf nodes to aligned faces
        self.draw_guiding_lines = False

        # Format and color for the guiding lines
        self.guiding_lines_type = 2 # 0 solid, 1 dashed, 2 dotted
        self.guiding_lines_color = "gray"

        # :::::::::::::::::::::::::
        # FACES
        # :::::::::::::::::::::::::

        # Aligned faces will be drawn as a table, considering all
        # columns in all node faces.
        self.draw_aligned_faces_as_table = True
        self.aligned_table_style = 0 # 0 = full grid (rows and
                                     # columns), 1 = semigrid ( rows
                                     # are merged )

        # When floating faces from different nodes overlap, children
        # faces are drawn on top of parent faces. This can be reversed
        # by setting this attribute to false.
        self.children_faces_on_top = True

        # :::::::::::::::::::::::::
        # Addons
        # :::::::::::::::::::::::::

        # Draw a border around the whole tree
        self.show_border = False

        # Draw the scale
        self.show_scale = True
        self.scale_length = None

        # Initialize aligned face headers
        self.aligned_header = FaceContainer()
        self.aligned_foot = FaceContainer()

        self.show_leaf_name = True
        self.show_branch_length = False
        self.show_branch_support = False

        self.legend = FaceContainer()
        self.legend_position = 2


        self.title = FaceContainer()
        self.tree_width = 180
        # PRIVATE values
        self._scale = None

        self.__closed__ = 1


    def __setattr__(self, attr, val):
        if hasattr(self, attr) or not getattr(self, "__closed__", 0):
            if TREE_STYLE_CHECKER.get(attr, lambda x: True)(val):
                object.__setattr__(self, attr, val)
            else:
                raise ValueError("[%s] wrong type" %attr)
        else:
            raise ValueError("[%s] option is not supported" %attr)

class _FaceAreas(object):
    def __init__(self):
        for a in FACE_POSITIONS:
            setattr(self, a, FaceContainer())

    def __setattr__(self, attr, val):
        if attr not in FACE_POSITIONS:
            raise AttributeError("Face area [%s] not in %s" %(attr, FACE_POSITIONS) )
        return super(_FaceAreas, self).__setattr__(attr, val)

    def __getattr__(self, attr):
        if attr not in FACE_POSITIONS:
            raise AttributeError("Face area [%s] not in %s" %(attr, FACE_POSITIONS) )
        return super(_FaceAreas, self).__getattr__(attr)

class FaceContainer(dict):
    """
    .. versionadded:: 2.1

    Use this object to create a grid of faces. You can add faces to different columns.
    """
    def add_face(self, face, column):
        """
        add the face **face** to the specified **column**
        """
        self.setdefault(int(column), []).append(face)

def _leaf(node):
    collapsed = hasattr(node, "_img_style") and not node.img_style["draw_descendants"]
    return collapsed or node.is_leaf()

def add_face_to_node(face, node, column, aligned=False, position="branch-right"):
    """
    .. currentmodule:: ete3.treeview.faces

    Adds a Face to a given node.

    :argument face: A :class:`Face` instance

    .. currentmodule:: ete3

    :argument node: a tree node instance (:class:`Tree`, :class:`PhyloTree`, etc.)
    :argument column: An integer number starting from 0
    :argument "branch-right" position: Possible values are
      "branch-right", "branch-top", "branch-bottom", "float", "float-behind" and "aligned".
    """

    ## ADD HERE SOME TYPE CHECK FOR node and face

    # to stay 2.0 compatible
    if aligned == True:
        position = "aligned"

    if getattr(node, "_temp_faces", None):
        getattr(node._temp_faces, position).add_face(face, column)
    else:
         raise Exception("This function can only be called within a layout function. Use node.add_face() instead")


def set_pen_style(pen, line_style):
    if line_style == 0:
        pen.setStyle(Qt.SolidLine)
    elif line_style == 1:
        pen.setStyle(Qt.DashLine)
    elif line_style == 2:
        pen.setStyle(Qt.DotLine)


def save(scene, imgName, w=None, h=None, dpi=90,\
             take_region=False, units="px"):
    ipython_inline = False
    if imgName == "%%inline":
        ipython_inline = True
        ext = "PNG"
    elif imgName == "%%inlineSVG":
        ipython_inline = True
        ext = "SVG"        
    elif imgName.startswith("%%return"):
        try:
            ext = imgName.split(".")[1].upper()
        except IndexError:
            ext = 'SVG'
        imgName = '%%return'
    else:
        ext = imgName.split(".")[-1].upper()

    main_rect = scene.sceneRect()
    aspect_ratio = main_rect.height() / main_rect.width()

    # auto adjust size
    if not w and not h:
        units = "px"
        w = main_rect.width()
        h = main_rect.height()
        ratio_mode = Qt.KeepAspectRatio
    elif w and h:
        ratio_mode = Qt.IgnoreAspectRatio
    elif h is None :
        h = w * aspect_ratio
        ratio_mode = Qt.KeepAspectRatio
    elif w is None:
        w = h / aspect_ratio
        ratio_mode = Qt.KeepAspectRatio

    # Adjust to resolution
    if units == "mm":
        if w:
            w = w * 0.0393700787 * dpi
        if h:
            h = h * 0.0393700787 * dpi
    elif units == "in":
        if w:
            w = w * dpi
        if h:
            h = h * dpi
    elif units == "px":
        pass
    else:
        raise Exception("wrong unit format")

    x_scale, y_scale = w/main_rect.width(), h/main_rect.height()

    if ext == "SVG":
        svg = QSvgGenerator()
        targetRect = QRectF(0, 0, w, h)
        svg.setSize(QSize(w, h))
        svg.setViewBox(targetRect)
        svg.setTitle("Generated with ETE http://etetoolkit.org")
        svg.setDescription("Generated with ETE http://etetoolkit.org")

        if imgName == '%%return':
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            svg.setOutputDevice(buf)
        else:
            svg.setFileName(imgName)

        pp = QPainter()
        pp.begin(svg)
        scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
        pp.end()
        if imgName == '%%return':
            compatible_code = str(ba)
            print('from memory')
        else:
            with open(imgName) as f_in:
                compatible_code = f_in.read()
        # Fix a very annoying problem with Radial gradients in
        # inkscape and browsers...
        compatible_code = compatible_code.replace("xml:id=", "id=")
        compatible_code = re.sub('font-size="(\d+)"', 'font-size="\\1pt"', compatible_code)
        compatible_code = compatible_code.replace('\n', ' ')
        compatible_code = re.sub('<g [^>]+>\s*</g>', '', compatible_code)
        # End of fix
        if ipython_inline:
            from IPython.core.display import SVG
            return SVG(compatible_code)

        elif imgName == '%%return':
            return x_scale, y_scale, compatible_code
        else:
            with open(imgName, "w") as f_out:
                f_out.write(compatible_code)


    elif ext == "PDF" or ext == "PS":
        if ext == "PS":
            format = QPrinter.PostScriptFormat
        else:
            format = QPrinter.PdfFormat

        printer = QPrinter(QPrinter.HighResolution)
        printer.setResolution(dpi)
        printer.setOutputFormat(format)
        printer.setPageSize(QPrinter.A4)
        printer.setPaperSize(QSizeF(w, h), QPrinter.DevicePixel)
        printer.setPageMargins(0, 0, 0, 0, QPrinter.DevicePixel)

        #pageTopLeft = printer.pageRect().topLeft()
        #paperTopLeft = printer.paperRect().topLeft()
        # For PS -> problems with margins
        #print paperTopLeft.x(), paperTopLeft.y()
        #print pageTopLeft.x(), pageTopLeft.y()
        # print  printer.paperRect().height(),  printer.pageRect().height()
        #topleft =  pageTopLeft - paperTopLeft

        printer.setFullPage(True);
        printer.setOutputFileName(imgName);
        pp = QPainter(printer)
        targetRect =  QRectF(0, 0 , w, h)
        scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
    else:
        targetRect = QRectF(0, 0, w, h)
        ii= QImage(w, h, QImage.Format_ARGB32)
        ii.fill(QColor(Qt.white).rgb())
        ii.setDotsPerMeterX(dpi / 0.0254) # Convert inches to meters
        ii.setDotsPerMeterY(dpi / 0.0254)
        pp = QPainter(ii)
        pp.setRenderHint(QPainter.Antialiasing)
        pp.setRenderHint(QPainter.TextAntialiasing)
        pp.setRenderHint(QPainter.SmoothPixmapTransform)

        scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
        pp.end()
        if ipython_inline:
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            ii.save(buf, "PNG")
            from IPython.core.display import Image
            return Image(ba.data())
        elif imgName == '%%return':
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            ii.save(buf, "PNG")
            return x_scale, y_scale, ba.toBase64()
        else:
            ii.save(imgName)

    return w/main_rect.width(), h/main_rect.height()
