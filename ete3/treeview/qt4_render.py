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
import math
import re
import six

from .qt import *
from . import qt4_circular_render as crender
from . import qt4_rect_render as rrender
from .main import _leaf, NodeStyle, _FaceAreas, tracktime, TreeStyle
from .node_gui_actions import _NodeActions as _ActionDelegator
from .qt4_face_render import update_node_faces, _FaceGroupItem, _TextFaceItem
from .templates import _DEFAULT_STYLE, apply_template
from . import faces


## | General scheme of node content
## |==========================================================================================================================|
## |                                                fullRegion                                                                |
## |             nodeRegion                  |================================================================================|
## |                                         |                                fullRegion                                     ||
## |                                         |        nodeRegion                     |=======================================||
## |                                         |                                       |         fullRegion                   |||
## |                                         |                                       |         nodeRegion                   |||
## |                                         |                         |             |branch_length | nodeSize | facesRegion|||
## |                                         | branch_length | nodesize|faces-right  |=======================================||
## |                                         |                         |(facesRegion)|=======================================||
## |                                         |                                       |             fullRegion                ||
## |                                         |                                       |             nodeRegion                ||
## |  faces-top     |          |             |                                       | branch_length | nodeSize | facesRegion||
## | branch_length  | NodeSize |faces-right  |                                       |=======================================||
## |  faces-bottom  |          |(facesRegion)|================================================================================|
## |                                         |=======================================|                                        |
## |                                         |             fullRegion                |                                        |
## |                                         |        nodeRegion                     |                                        |
## |                                         | branch_length | nodeSize | facesRegion|                                        |
## |                                         |=======================================|                                        |
## |==========================================================================================================================|

class _CircleItem(QGraphicsEllipseItem, _ActionDelegator):
    def __init__(self, node):
        self.node = node
        d = node.img_style["size"]
        QGraphicsEllipseItem.__init__(self, 0, 0, d, d)
        _ActionDelegator.__init__(self)

        self.setBrush(QBrush(QColor(self.node.img_style["fgcolor"])))
        self.setPen(QPen(QColor(self.node.img_style["fgcolor"])))

class _RectItem(QGraphicsRectItem, _ActionDelegator):
    def __init__(self, node):
        self.node = node
        d = node.img_style["size"]
        QGraphicsRectItem.__init__(self, 0, 0, d, d)
        _ActionDelegator.__init__(self)
        self.setBrush(QBrush(QColor(self.node.img_style["fgcolor"])))
        self.setPen(QPen(QColor(self.node.img_style["fgcolor"])))

class _SphereItem(QGraphicsEllipseItem, _ActionDelegator):
    def __init__(self, node):
        self.node = node
        d = node.img_style["size"]
        r = d/2.0
        QGraphicsEllipseItem.__init__(self, 0, 0, d, d)
        _ActionDelegator.__init__(self)
        #self.setBrush(QBrush(QColor(self.node.img_style["fgcolor"])))
        self.setPen(QPen(QColor(self.node.img_style["fgcolor"])))
        gradient = QRadialGradient(r, r, r,(d)/3,(d)/3)
        gradient.setColorAt(0.05, Qt.white);
        gradient.setColorAt(1, QColor(self.node.img_style["fgcolor"]));
        self.setBrush(QBrush(gradient))
        # self.setPen(Qt.NoPen)

class _EmptyItem(QGraphicsItem):
    def __init__(self, parent=None):
        QGraphicsItem.__init__(self)
        self.setParentItem(parent)

        # qt4.6+ Only
        try:
            self.setFlags(QGraphicsItem.ItemHasNoContents)
        except:
            pass

    def boundingRect(self):
        return QRectF(0,0,0,0)

    def paint(self, *args, **kargs):
        return

class _TreeItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        QGraphicsRectItem.__init__(self)
        self.setParentItem(parent)
        self.n2i = {}
        self.n2f = {}

class _NodeItem(_EmptyItem):
    def __init__(self, node, parent):
        _EmptyItem.__init__(self, parent)
        self.node = node
        self.nodeRegion = QRectF()
        self.facesRegion = QRectF()
        self.fullRegion = QRectF()
        self.highlighted = False

class _NodeLineItem(QGraphicsLineItem, _ActionDelegator):
    def __init__(self, node, *args, **kargs):
        self.node = node
        QGraphicsLineItem.__init__(self, *args, **kargs)
        _ActionDelegator.__init__(self)
    def paint(self, painter, option, widget):
        QGraphicsLineItem.paint(self, painter, option, widget)

class _LineItem(QGraphicsLineItem):
    def paint(self, painter, option, widget):
        QGraphicsLineItem.paint(self, painter, option, widget)

class _PointerItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        QGraphicsRectItem.__init__(self,0,0,0,0, parent)
        self.color = QColor("blue")
        self._active = False
        self.setBrush(QBrush(Qt.NoBrush))

    def paint(self, p, option, widget):
        p.setPen(self.color)
        p.drawRect(self.rect())
        return
        # Draw info text
        font = QFont("Arial",13)
        text = "%d selected."  % len(self.get_selected_nodes())
        textR = QFontMetrics(font).boundingRect(text)
        if  self.rect().width() > textR.width() and \
                self.rect().height() > textR.height()/2.0 and 0: # OJO !!!!
            p.setPen(QPen(self.color))
            p.setFont(QFont("Arial",13))
            p.drawText(self.rect().bottomLeft().x(),self.rect().bottomLeft().y(),text)

    def get_selected_nodes(self):
        selPath = QPainterPath()
        selPath.addRect(self.rect())
        self.scene().setSelectionArea(selPath)
        return [i.node for i in self.scene().selectedItems()]

    def setActive(self,bool):
        self._active = bool

    def isActive(self):
        return self._active

class _TreeScene(QGraphicsScene):
    def __init__(self):
        QGraphicsScene.__init__(self)
        self.view = None

    def init_values(self, tree, img, n2i, n2f):
        self.master_item = _EmptyItem()
        self.tree = tree
        self.n2i = n2i
        self.n2f = n2f
        self.img = img

    def draw(self):
        self.img._scale = None
        tree_item, self.n2i, self.n2f = render(self.tree, self.img)
        if self.master_item:
            self.removeItem(self.master_item)
        tree_item, n2i, n2f = render(self.tree, self.img)
        self.init_values(self.tree, self.img, n2i, n2f)
        self.addItem(self.master_item)
        tree_item.setParentItem(self.master_item)
        self.setSceneRect(tree_item.rect())

#@tracktime
def render(root_node, img, hide_root=False):
    '''main render function. hide_root option is used when render
    trees as Faces

    '''
    mode = img.mode
    orientation = img.orientation

    arc_span = img.arc_span

    layout_fn = img._layout_handler

    parent = _TreeItem()
    n2i = parent.n2i # node to items
    n2f = parent.n2f # node to faces

    parent.bg_layer =  _EmptyItem(parent)
    parent.tree_layer = _EmptyItem(parent)
    parent.float_layer = _EmptyItem(parent)
    parent.float_behind_layer = _EmptyItem(parent)

    TREE_LAYERS = [parent.bg_layer, parent.tree_layer,
                   parent.float_layer, parent.float_behind_layer]

    parent.bg_layer.setZValue(0)
    parent.tree_layer.setZValue(2)

    parent.float_behind_layer.setZValue(1)
    parent.float_layer.setZValue(3)

    # This could be used to handle aligned faces in internal
    # nodes.
    virtual_leaves = 0

    if img.show_branch_length:
        bl_face = faces.AttrFace("dist", fsize=8, ftype="Arial", fgcolor="black", formatter = "%0.3g")
    if img.show_branch_support:
        su_face = faces.AttrFace("support", fsize=8, ftype="Arial", fgcolor="darkred", formatter = "%0.3g")
    if img.show_leaf_name:
        na_face = faces.AttrFace("name", fsize=10, ftype="Arial", fgcolor="black")

    for n in root_node.traverse(is_leaf_fn=_leaf):
        set_style(n, layout_fn)

        if img.show_branch_length:
            faces.add_face_to_node(bl_face, n, 0, position="branch-top")

        if not _leaf(n) and img.show_branch_support:
            faces.add_face_to_node(su_face, n, 0, position="branch-bottom")

        if _leaf(n) and n.name and img.show_leaf_name:
            faces.add_face_to_node(na_face, n, 0, position="branch-right")

        if _leaf(n):# or len(n.img_style["_faces"]["aligned"]):
            virtual_leaves += 1

        update_node_faces(n, n2f, img)

    rot_step = float(arc_span) / virtual_leaves
    #rot_step = float(arc_span) / len([n for n in root_node.traverse() if _leaf(n)])

    # Calculate optimal branch length
    if img._scale is not None:
        init_items(root_node, parent, n2i, n2f, img, rot_step, hide_root)
    elif img.scale is None:
        # create items and calculate node dimensions skipping branch lengths
        init_items(root_node, parent, n2i, n2f, img, rot_step, hide_root)
        if mode == 'r':
            if img.optimal_scale_level == "full":
                scales = [(i.widths[1]/n.dist) for n,i in six.iteritems(n2i) if n.dist]
                img._scale = max(scales) if scales else 0.0
            else:
                farthest, dist = root_node.get_farthest_leaf(topology_only=img.force_topology)
                img._scale = img.tree_width / dist if dist else 0.0
            update_branch_lengths(root_node, n2i, n2f, img)
        else:
            img._scale = crender.calculate_optimal_scale(root_node, n2i, rot_step, img)
            #print "OPTIMAL circular scale", img._scale
            update_branch_lengths(root_node, n2i, n2f, img)
            init_items(root_node, parent, n2i, n2f, img, rot_step, hide_root)
    else:
        # create items and calculate node dimensions CONSIDERING branch lengths
        img._scale = img.scale
        init_items(root_node, parent, n2i, n2f, img, rot_step, hide_root)

    #print "USING scale", img._scale
    # Draw node content
    for node in root_node.traverse(is_leaf_fn=_leaf):
        if node is not root_node or not hide_root:
            render_node_content(node, n2i, n2f, img)

    # Adjust content to rect or circular layout
    mainRect = parent.rect()

    if mode == "c":
        tree_radius = crender.render_circular(root_node, n2i, rot_step)
        mainRect.adjust(-tree_radius, -tree_radius, tree_radius, tree_radius)
    else:
        iwidth = n2i[root_node].fullRegion.width()
        iheight = n2i[root_node].fullRegion.height()
        mainRect.adjust(0, 0, iwidth, iheight)
        tree_radius = iwidth

    # Add extra layers: aligned faces, floating faces, node
    # backgrounds, etc. The order by which the following methods are
    # called IS IMPORTANT
    render_floatings(n2i, n2f, img, parent.float_layer, parent.float_behind_layer)

    aligned_region_width = render_aligned_faces(img, mainRect, parent.tree_layer, n2i, n2f)

    render_backgrounds(img, mainRect, parent.bg_layer, n2i, n2f)

    # rotate if necessary in circular images. flip and adjust if mirror orientation.
    adjust_faces_to_tranformations(img, mainRect, n2i, n2f, TREE_LAYERS)

    # Rotate main image if necessary
    parent.setRect(mainRect)
    parent.setPen(QPen(Qt.NoPen))

    if img.rotation:
        rect = parent.boundingRect()
        x =  rect.x() + (rect.width()/2.0)
        y =  rect.y() +  (rect.height()/2.0)
        parent.setTransform(QTransform().translate(x, y).rotate(img.rotation).translate(-x, -y))

    # Creates the main tree item that will act as frame for the whole image
    frame = QGraphicsRectItem()
    parent.setParentItem(frame)
    mainRect = parent.mapToScene(mainRect).boundingRect()

    mainRect.adjust(-img.margin_left, -img.margin_top, \
                         img.margin_right, img.margin_bottom)

    # Fix negative coordinates, so main item always starts at 0,0
    topleft  = mainRect.topLeft()
    _x = abs(topleft.x()) if topleft.x() < 0 else 0
    _y = abs(topleft.y()) if topleft.y() < 0 else 0
    if _x or _y:
        parent.moveBy(_x, _y)
        mainRect.adjust(_x, _y, _x, _y)

    # Add extra components and adjust mainRect to them

    add_legend(img, mainRect, frame)
    add_title(img, mainRect, frame)
    add_scale(img, mainRect, frame)
    tree_face_n2i, treeface_n2f = add_treeface(img, mainRect, frame)
    n2i.update(tree_face_n2i)
    n2f.update(treeface_n2f)
    frame.setRect(mainRect)

    # Draws a border around the tree
    if not img.show_border:
        frame.setPen(QPen(Qt.NoPen))
    else:
        frame.setPen(QPen(QColor("black")))

    return frame, n2i, n2f

def adjust_faces_to_tranformations(img, mainRect, n2i, n2f, tree_layers):
    if img.mode == "c":
        rotate_inverted_faces(n2i, n2f, img)
    elif img.mode == "r" and img.orientation == 1:
        for layer in tree_layers:
            layer.setTransform(QTransform().translate(0, 0).scale(-1,1).translate(0, 0))
            layer.moveBy(mainRect.width(),0)
        for faceblock in six.itervalues(n2f):
            for pos, fb in six.iteritems(faceblock):
                fb.flip_hz()

def add_legend(img, mainRect, parent):
    if img.legend:
        legend = _FaceGroupItem(img.legend, None)
        legend.setup_grid()
        legend.render()
        lg_w, lg_h = legend.get_size()
        dw = max(0, lg_w-mainRect.width())
        legend.setParentItem(parent)
        if img.legend_position == 1:
            mainRect.adjust(0, -lg_h, dw, 0)
            legend.setPos(mainRect.topLeft())
        elif img.legend_position == 2:
            mainRect.adjust(0, -lg_h, dw, 0)
            pos = mainRect.topRight()
            legend.setPos(pos.x()-lg_w, pos.y())
        elif img.legend_position == 3:
            legend.setPos(mainRect.bottomLeft())
            mainRect.adjust(0, 0, dw, lg_h)
        elif img.legend_position == 4:
            pos = mainRect.bottomRight()
            legend.setPos(pos.x()-lg_w, pos.y())
            mainRect.adjust(0, 0, dw, lg_h)

def add_title(img, mainRect, parent):
    if img.title:
        title = _FaceGroupItem(img.title, None)
        title.setup_grid()
        title.render()
        lg_w, lg_h = title.get_size()
        dw = max(0, lg_w-mainRect.width())
        title.setParentItem(parent)
        mainRect.adjust(0, -lg_h, dw, 0)
        title.setPos(mainRect.topLeft())

def add_treeface(img, mainRect, parent):
    n2i, n2f = {}, {}
    if img.aligned_treeface_vt:
        treeface = _FaceGroupItem(img.aligned_treeface_vt, None)
        treeface.setup_grid()
        treeface.render()
        lg_w, lg_h = treeface.get_size()
        dw = max(0, lg_w-mainRect.width())
        dh = max(0, lg_h-mainRect.height())
        treeface.setParentItem(parent)
        if img.treeface_position_vt == -1:
            mainRect.adjust(0, -lg_h, dw, 0)
            treeface.setPos(mainRect.topLeft())
        else:
            treeface.setPos(mainRect.bottomLeft())
            mainRect.adjust(0, 0, dw, lg_h)

        # return n2i and n2f for the added trees
        # Those will be used to update parent dict
        for (k, facelist) in treeface.column2faces.items():
            for f in facelist:
                if isinstance(f, faces.TreeFace):
                    n2i.update(f.n2i)
                    n2f.update(f.n2f)

    if img.aligned_treeface_hz:
        treeface = _FaceGroupItem(img.aligned_treeface_hz, None)
        treeface.setup_grid()
        treeface.render()
        lg_w, lg_h = treeface.get_size()
        dw = max(0, lg_w-mainRect.width())
        dh = max(0, lg_h-mainRect.height())
        treeface.setParentItem(parent)
        if img.treeface_position_hz == -1:
            mainRect.adjust(-lg_w, 0, 0, dh)
            treeface.setPos(mainRect.topLeft())
        else:
            mainRect.adjust(0, 0, lg_w, dh)
            pos = mainRect.topRight()
            treeface.setPos(pos.x()-lg_w, 0)

        # return n2i and n2f for the added trees
        # Those will be used to update parent dict
        for (k, facelist) in treeface.column2faces.items():
            for f in facelist:
                if isinstance(f, faces.TreeFace):
                    n2i.update(f.n2i)
                    n2f.update(f.n2f)


    return n2i, n2f


def add_scale(img, mainRect, parent):
    if img.show_scale:
        if img.scale_length is None:
            length = 50.0
        else:
            length = img.scale_length * img._scale
            if length > mainRect.width():
                max_value = mainRect.width() / img._scale
                raise ValueError('Custom scale bar length (TreeStyle.scale_length) is larger than the tree image'
                                 'Use values between 0 and %g' %max_value)

        scaleItem = _EmptyItem()
        customPen = QPen(QColor("black"), 1)

        if img.force_topology:
            wtext = "Force topology is enabled!\nBranch lengths do not represent real values."
            warning_text = QGraphicsSimpleTextItem(wtext)
            warning_text.setFont(QFont("Arial", 8))
            warning_text.setBrush( QBrush(QColor("darkred")))
            warning_text.setPos(0, 32)
            warning_text.setParentItem(scaleItem)
        else:
            line = QGraphicsLineItem(scaleItem)
            line2 = QGraphicsLineItem(scaleItem)
            line3 = QGraphicsLineItem(scaleItem)
            line.setPen(customPen)
            line2.setPen(customPen)
            line3.setPen(customPen)

            line.setLine(0, 5, length, 5)
            line2.setLine(0, 0, 0, 10)
            line3.setLine(length, 0, length, 10)
            length_text = float(length) / img._scale if img._scale else 0.0
            scale_text = "%g" %(length_text)
            scale = QGraphicsSimpleTextItem(scale_text)
            scale.setParentItem(scaleItem)
            scale.setPos(0, 10)

        scaleItem.setParentItem(parent)
        dw = max(0, length - mainRect.width())
        scaleItem.setPos(mainRect.bottomLeft())
        scaleItem.moveBy(img.margin_left, 0)
        mainRect.adjust(0, 0, 0, length)

def rotate_inverted_faces(n2i, n2f, img):
    for node, faceblock in six.iteritems(n2f):
        item = n2i[node]
        if item.rotation > 90 and item.rotation < 270:
            for pos, fb in six.iteritems(faceblock):
                fb.rotate(181)

def render_backgrounds(img, mainRect, bg_layer, n2i, n2f):

    if img.mode == "c":
        max_r = mainRect.width()/2.0
    else:
        max_r = mainRect.width()

    for node, item in six.iteritems(n2i):
        if _leaf(node):
            first_c = n2i[node]
            last_c = n2i[node]
        else:
            first_c = n2i[node.children[0]]
            last_c = n2i[node.children[-1]]

        if img.mode == "c":
            h = item.effective_height
            angle_start = first_c.full_start
            angle_end = last_c.full_end
            parent_radius = getattr(n2i.get(node.up, None), "radius", 0)
            base = parent_radius + item.nodeRegion.width()

            # if node.img_style["node_bgcolor"].upper() != "#FFFFFF":
            #     bg1 = crender._ArcItem()
            #     r = math.sqrt(base**2 + h**2)
            #     bg1.set_arc(0, 0, parent_radius, r, angle_start, angle_end)
            #     bg1.setParentItem(item.content.bg)
            #     bg1.setPen(QPen(QColor(node.img_style["node_bgcolor"])))
            #     bg1.setBrush(QBrush(QColor(node.img_style["node_bgcolor"])))

            # if node.img_style["faces_bgcolor"].upper() != "#FFFFFF":
            #     bg2 = crender._ArcItem()
            #     r = math.sqrt(base**2 + h**2)
            #     bg2.set_arc(0, 0, parent_radius, item.radius, angle_start, angle_end)
            #     bg2.setParentItem(item.content)
            #     bg2.setPen(QPen(QColor(node.img_style["faces_bgcolor"])))
            #     bg2.setBrush(QBrush(QColor(node.img_style["faces_bgcolor"])))

            if node.img_style["bgcolor"].upper() != "#FFFFFF":
                bg = crender._ArcItem()
                bg.set_arc(0, 0, parent_radius, max_r, angle_start, angle_end)
                bg.setPen(QPen(QColor(node.img_style["bgcolor"])))
                bg.setBrush(QBrush(QColor(node.img_style["bgcolor"])))
                bg.setParentItem(bg_layer)
                bg.setZValue(item.zValue())

        if img.mode == "r":
            if node.img_style["bgcolor"].upper() != "#FFFFFF":
                bg = QGraphicsRectItem()
                pos = item.content.mapToScene(0, 0)
                bg.setPos(pos.x(), pos.y())
                bg.setRect(0, 0, max_r-pos.x(),  item.fullRegion.height())
                bg.setPen(QPen(QColor(node.img_style["bgcolor"])))
                bg.setBrush(QBrush(QColor(node.img_style["bgcolor"])))
                bg.setParentItem(bg_layer)
                bg.setZValue(item.zValue())

def set_node_size(node, n2i, n2f, img):
    scale = img._scale
    min_separation = img.min_leaf_separation

    item = n2i[node]
    if img.force_topology:
        branch_length = item.branch_length = 25
    else:
        branch_length = item.branch_length = float(node.dist * scale)

    # Organize faces by groups
    #faceblock = update_node_faces(node, n2f, img)
    faceblock = n2f[node]
    aligned_height = 0
    if _leaf(node):
        if img.mode == "r":
            aligned_height = faceblock["aligned"].h
        elif img.mode == "c":
            # aligned faces in circular mode are adjusted afterwords. The
            # min radius of the largest aligned faces will be calculated.
            pass

    # Total height required by the node. I cannot sum up the height of
    # all elements, since the position of some of them are forced to
    # be on top or at the bottom of branches. This fact can produce
    # and unbalanced nodeRegion center. Here, I only need to know
    # about the imbalance size to correct node height. The center will
    # be calculated later according to the parent position.
    top_half_h = ( (node.img_style["size"]/2.0) +
                       node.img_style["hz_line_width"]/2.0 +
                       faceblock["branch-top"].h )

    bottom_half_h =( (node.img_style["size"]/2.0) +
                       node.img_style["hz_line_width"]/2.0 +
                       faceblock["branch-bottom"].h )

    h1 = top_half_h + bottom_half_h
    h2 = max(faceblock["branch-right"].h, \
                 aligned_height, \
                min_separation )
    h = max(h1, h2)
    imbalance = abs(top_half_h - bottom_half_h)
    if imbalance > h2/2.0:
        h += imbalance - (h2/2.0)

    # This adds a vertical margin around the node elements
    h += img.branch_vertical_margin

    # Total width required by the node
    w = sum([max(branch_length + node.img_style["size"],
                 faceblock["branch-top"].w + node.img_style["size"],
                 faceblock["branch-bottom"].w + node.img_style["size"],
                 ),
             faceblock["branch-right"].w]
            )

    # This breaks ultrametric tree visualization
    #w += node.img_style["vt_line_width"]

    # rightside faces region
    item.facesRegion.setRect(0, 0, faceblock["branch-right"].w, h)

    # Node region
    item.nodeRegion.setRect(0, 0, w, h)

    # This is the node total region covered by the node
    item.fullRegion.setRect(0, 0, w, h)

def render_node_content(node, n2i, n2f, img):
    style = node.img_style
    item = n2i[node]
    item.content = _EmptyItem(item)

    nodeR = item.nodeRegion
    facesR = item.facesRegion
    center = item.center
    branch_length = item.branch_length

    # Node points
    ball_size = style["size"]


    vlw = style["vt_line_width"] if not _leaf(node) and len(node.children) > 1 else 0.0

    # face_start_x = nodeR.width() - facesR.width() - vlw
    face_start_x = max(0, nodeR.width() - facesR.width() - vlw)
    ball_start_x = face_start_x - ball_size

    if ball_size:
        if node.img_style["shape"] == "sphere":
            node_ball = _SphereItem(node)
        elif node.img_style["shape"] == "circle":
            node_ball = _CircleItem(node)
        elif node.img_style["shape"] == "square":
            node_ball = _RectItem(node)

        node_ball.setPos(ball_start_x, center-(ball_size/2.0))

        #from qt4_gui import _BasicNodeActions
        #node_ball.delegate = _BasicNodeActions()
        #node_ball.setAcceptHoverEvents(True)
        #node_ball.setCursor(Qt.PointingHandCursor)

    else:
        node_ball = None

    # Branch line to parent
    pen = QPen()
    set_pen_style(pen, style["hz_line_type"])
    pen.setColor(QColor(style["hz_line_color"]))
    pen.setWidth(style["hz_line_width"])
    pen.setCapStyle(Qt.FlatCap)
    #pen.setCapStyle(Qt.RoundCap)
    #pen.setCapStyle(Qt.SquareCap)
    #pen.setJoinStyle(Qt.RoundJoin)
    hz_line = _LineItem()
    hz_line = _NodeLineItem(node)
    hz_line.setPen(pen)

    join_fix = 0
    if img.mode == "c" and node.up and node.up.img_style["vt_line_width"]:
        join_fix = node.up.img_style["vt_line_width"]
        # fix_join_line = _LineItem()
        # fix_join_line = _NodeLineItem(node)
        # parent_style = node.up.img_style
        # pen = QPen()
        # pen.setColor(QColor(parent_style["vt_line_color"]))
        # pen.setWidth(parent_style["hz_line_width"])
        # pen.setCapStyle(Qt.FlatCap)
        # fix_join_line.setPen(pen)
        # fix_join_line.setLine(-join_fix, center, join_fix, center)
        # fix_join_line.setParentItem(item.content)

    hz_line.setLine(-join_fix, center, branch_length, center)

    if img.complete_branch_lines_when_necessary:
        extra_line = _LineItem(branch_length, center, ball_start_x, center)
        pen = QPen()
        item.extra_branch_line = extra_line
        set_pen_style(pen, img.extra_branch_line_type)
        pen.setColor(QColor(img.extra_branch_line_color))
        pen.setCapStyle(Qt.FlatCap)
        pen.setWidth(style["hz_line_width"])
        extra_line.setPen(pen)
    else:
        extra_line = None

    # Attach branch-right faces to child
    fblock_r = n2f[node]["branch-right"]
    fblock_r.render()
    fblock_r.setPos(face_start_x, center-fblock_r.h/2.0)

    # Attach branch-bottom faces to child
    fblock_b = n2f[node]["branch-bottom"]
    fblock_b.render()
    fblock_b.setPos(item.widths[0], center + style["hz_line_width"]/2.0)

    # Attach branch-top faces to child
    fblock_t = n2f[node]["branch-top"]
    fblock_t.render()
    fblock_t.setPos(item.widths[0], center - fblock_t.h - style["hz_line_width"]/2.0)

    # Vertical line
    if not _leaf(node):
        if img.mode == "c":
            vt_line = QGraphicsPathItem()

        elif img.mode == "r":
            vt_line = _LineItem(item)
            first_child = node.children[0]
            last_child = node.children[-1]
            first_child_part = n2i[node.children[0]]
            last_child_part = n2i[node.children[-1]]
            c1 = first_child_part.start_y + first_child_part.center
            c2 = last_child_part.start_y + last_child_part.center
            fx = nodeR.width() - (vlw/2.0)
            if first_child.img_style["hz_line_width"] > 0:
                c1 -= (first_child.img_style["hz_line_width"] / 2.0)
            if last_child.img_style["hz_line_width"] > 0:
                c2 += (last_child.img_style["hz_line_width"] / 2.0)
            vt_line.setLine(fx, c1, fx, c2)

        pen = QPen()
        set_pen_style(pen, style["vt_line_type"])
        pen.setColor(QColor(style["vt_line_color"]))
        pen.setWidth(style["vt_line_width"])
        pen.setCapStyle(Qt.FlatCap)
        #pen.setCapStyle(Qt.RoundCap)
        #pen.setCapStyle(Qt.SquareCap)
        vt_line.setPen(pen)
        item.vt_line = vt_line
    else:
        vt_line = None

    item.bg = QGraphicsItemGroup()
    item.movable_items = [] #QGraphicsItemGroup()
    item.static_items = [] #QGraphicsItemGroup()

    # Items fow which coordinates are exported in the image map
    item.mapped_items = [node_ball, fblock_r, fblock_b, fblock_t]


    for i in [vt_line, extra_line, hz_line]:
        if i:
            #item.static_items.addToGroup(i)
            item.static_items.append(i)
            i.setParentItem(item.content)
    for i in [node_ball, fblock_r, fblock_b, fblock_t]:
        if i:
            #item.movable_items.addToGroup(i)
            item.movable_items.append(i)
            i.setParentItem(item.content)


    #item.movable_items.setParentItem(item.content)
    #item.static_items.setParentItem(item.content)

def set_pen_style(pen, line_style):
    if line_style == 0:
        pen.setStyle(Qt.SolidLine)
    elif line_style == 1:
        pen.setStyle(Qt.DashLine)
    elif line_style == 2:
        pen.setStyle(Qt.DotLine)

def set_style(n, layout_func):
    #if not isinstance(getattr(n, "img_style", None), NodeStyle):
    #    print "Style of", n.name ,"is None"
    #    n.set_style()
    #    n.img_style = NodeStyle()

    n._temp_faces = _FaceAreas()

    for func in layout_func:
        func(n)

def render_floatings(n2i, n2f, img, float_layer, float_behind_layer):
    #floating_faces = [ [node, fb["float"]] for node, fb in n2f.iteritems() if "float" in fb]

    for node, faces in six.iteritems(n2f):
        face_set = [ [float_layer, faces.get("float", None)],
                     [float_behind_layer, faces.get("float-behind",None)]]

        for parent_layer,fb in face_set:
            if not fb:
                continue

            item = n2i[node]
            fb.setParentItem(parent_layer)

            try:
                xtra =  item.extra_branch_line.line().dx()
            except AttributeError:
                xtra = 0

            if img.mode == "c":
                # Floatings are positioned over branches
                crender.rotate_and_displace(fb, item.rotation, fb.h, item.radius - item.nodeRegion.width() + xtra)
                # Floatings are positioned starting from the node circle
                #crender.rotate_and_displace(fb, item.rotation, fb.h, item.radius - item.nodeRegion.width())

            elif img.mode == "r":
                start = item.branch_length + xtra - fb.w #if fb.w < item.branch_length else 0.0
                fb.setPos(item.content.mapToScene(start, item.center - (fb.h/2.0)))

            z = item.zValue()
            if not img.children_faces_on_top:
                z = -z

            fb.setZValue(z)
            fb.update_columns_size()
            fb.render()

def render_aligned_faces(img, mainRect, parent, n2i, n2f):
    # Prepares and renders aligned face headers. Used to later
    # place aligned faces
    aligned_faces = [ [node, fb["aligned"]] for node, fb in six.iteritems(n2f)\
                          if fb["aligned"].column2faces and _leaf(node)]

    # If no aligned faces, just return an offset of 0 pixels
    if not aligned_faces:
        return 0

    # Load header and footer
    if img.mode == "r":
        tree_end_x = mainRect.width()

        fb_head = _FaceGroupItem(img.aligned_header, None)
        fb_head.setParentItem(parent)
        fb_foot = _FaceGroupItem(img.aligned_foot, None)
        fb_foot.setParentItem(parent)
        surroundings = [[None,fb_foot], [None, fb_head]]
        mainRect.adjust(0, -fb_head.h, 0, fb_foot.h)
    else:
        tree_end_x = mainRect.width()/2.0
        surroundings = []

    # Place aligned faces and calculates the max size of each
    # column (needed to place column headers)
    c2max_w = {}
    maxh = 0
    maxh_node = None
    for node, fb in aligned_faces + surroundings:
        if fb.h > maxh:
            maxh = fb.h
            maxh_node = node
        for c, w in six.iteritems(fb.c2max_w):
            c2max_w[c] = max(w, c2max_w.get(c,0))
    extra_width = sum(c2max_w.values())

    # If rect mode, render header and footer
    if img.mode == "r":
        if img.draw_aligned_faces_as_table:
            fb_head.setup_grid(c2max_w)
            fb_foot.setup_grid(c2max_w)

        fb_head.render()
        fb_head.setPos(tree_end_x, mainRect.top())
        fb_foot.render()
        fb_foot.setPos(tree_end_x, mainRect.bottom()-fb_foot.h)
        if img.orientation == 1:
            fb_head.flip_hz()
            fb_foot.flip_hz()

    # if no scale provided in circular mode, optimal scale is expected
    # to provide the correct ending point to start drawing aligned
    # faces.
    elif img.mode == "c" and (img.scale or img._scale == 0) and not img.allow_face_overlap:
        angle = n2i[maxh_node].angle_span
        rad, off = crender.get_min_radius(1, maxh, angle, tree_end_x)
        extra_width += rad - tree_end_x
        tree_end_x = rad

    # Place aligned faces
    for node, fb in aligned_faces:
        item = n2i[node]
        item.mapped_items.append(fb)
        if img.draw_aligned_faces_as_table:
            if img.aligned_table_style == 0:
                fb.setup_grid(c2max_w, as_grid=True)
            elif img.aligned_table_style == 1:
                fb.setup_grid(c2max_w, as_grid=False)

        fb.render()
        fb.setParentItem(item.content)
        if img.mode == "c":
            if node.up in n2i:
                x = tree_end_x - n2i[node.up].radius
            else:
                x = tree_end_x
            #fb.moveBy(tree_end_x, 0)
        elif img.mode == "r":
            x = item.mapFromScene(tree_end_x, 0).x()

        fb.setPos(x, item.center-(fb.h/2.0))

        if img.draw_guiding_lines and _leaf(node):
            # -1 is to connect the two lines, otherwise there is a pixel in between
            guide_line = _LineItem(item.nodeRegion.width()-1, item.center, x, item.center)
            pen = QPen()
            set_pen_style(pen, img.guiding_lines_type)
            pen.setColor(QColor(img.guiding_lines_color))
            pen.setCapStyle(Qt.FlatCap)
            pen.setWidth(node.img_style["hz_line_width"])
            guide_line.setPen(pen)
            guide_line.setParentItem(item.content)

    if img.mode == "c":
        mainRect.adjust(-extra_width, -extra_width, extra_width, extra_width)
    else:
        mainRect.adjust(0, 0, extra_width, 0)
    return extra_width

def get_tree_img_map(n2i, x_scale=1, y_scale=1):
    MOTIF_ITEMS = set([faces.QGraphicsTriangleItem,
                       faces.QGraphicsEllipseItem,
                       faces.QGraphicsDiamondItem,
                       faces.QGraphicsRectItem,
                       faces.QGraphicsRoundRectItem])
    node_list = []
    face_list = []
    node_areas = {}
    #nid = 0
    for n, main_item in six.iteritems(n2i):
        #n.add_feature("_nid", str(nid))
        nid = n._nid

        rect = main_item.mapToScene(main_item.fullRegion).boundingRect()
        x1 = x_scale * rect.x()
        y1 = y_scale * rect.y()
        x2 = x_scale * (rect.x() + rect.width())
        y2 = y_scale * (rect.y() + rect.height())
        node_areas[nid] = [x1, y1, x2, y2]

        for item in main_item.mapped_items:
            if isinstance(item, _CircleItem) \
                    or isinstance(item, _SphereItem) \
                    or isinstance(item, _RectItem):
                r = item.boundingRect()
                rect = item.mapToScene(r).boundingRect()
                x1 = x_scale * rect.x()
                y1 = y_scale * rect.y()
                x2 = x_scale * (rect.x() + rect.width())
                y2 = y_scale * (rect.y() + rect.height())
                node_list.append([x1, y1, x2, y2, nid, None])
            elif isinstance(item, _FaceGroupItem):
                if item.column2faces:
                    for f in item.childItems():
                        r = f.boundingRect()
                        rect = f.mapToScene(r).boundingRect()
                        x1 = x_scale * rect.x()
                        y1 = y_scale * rect.y()
                        x2 = x_scale * (rect.x() + rect.width())
                        y2 = y_scale * (rect.y() + rect.height())
                        if isinstance(f, _TextFaceItem):
                            face_list.append([x1, y1, x2, y2, nid, str(getattr(f, "face_label", f.text()))])
                        elif isinstance(f, faces.SeqMotifRectItem):
                            #face_list.append([x1, y1, x2, y2, nid, str(getattr(f, "face_label", None))])
                            for mf in f.childItems():
                                r = mf.boundingRect()
                                rect = mf.mapToScene(r).boundingRect()
                                x1 = x_scale * rect.x()
                                y1 = y_scale * rect.y()
                                x2 = x_scale * (rect.x() + rect.width())
                                y2 = y_scale * (rect.y() + rect.height())
                                try:
                                    label = "Motif:%s" %mf.childItems()[0].text
                                except Exception:
                                    label = ""
                                face_list.append([x1, y1, x2, y2, nid, label])
                        else:
                            face_list.append([x1, y1, x2, y2, nid, getattr(f, "face_label", None)])
        #nid += 1

    return {"nodes": node_list, "faces": face_list, "node_areas": node_areas}

#@tracktime
def init_items(root_node, parent, n2i, n2f, img, rot_step, hide_root):
    # ::: Precalculate values :::
    visited = set()
    to_visit = []
    to_visit.append(root_node)
    last_rotation = img.arc_start
    depth = 1
    while to_visit:
        node = to_visit[-1]
        finished = True
        if node not in n2i:
            # Set style according to layout function
            item = n2i[node] = _NodeItem(node, parent.tree_layer)
            depth += 1

            item.setZValue(depth)
            if node is root_node and hide_root:
                pass
            else:
                init_node_dimensions(node, item, n2f[node], img)
                #set_node_size(node, n2i, n2f, img)

        if not _leaf(node):
            # visit children starting from left to right. Very
            #  important!! check all children[-1] and children[0]
            for c in reversed(node.children):
                if c not in visited:
                    to_visit.append(c)
                    finished = False
            # :: pre-order code here ::
        if not finished:
            continue
        else:
            to_visit.pop(-1)
            visited.add(node)

        # :: Post-order visits. Leaves are already visited here ::
        if img.mode == "c":
            if _leaf(node):
                crender.init_circular_leaf_item(node, n2i, n2f, last_rotation, rot_step)
                last_rotation += rot_step
            else:
                crender.init_circular_node_item(node, n2i, n2f)

        elif img.mode == "r":
            if _leaf(node):
                rrender.init_rect_leaf_item(node, n2i, n2f)
            else:
                rrender.init_rect_node_item(node, n2i, n2f)


def init_node_dimensions(node, item, faceblock, img):
    """Calculates width and height of all different subparts and faces
    of a given node. Branch lengths are not taken into account, so some
    dimensions must be adjusted after setting a valid scale.
    """

    min_separation = img.min_leaf_separation

    if _leaf(node):
        aligned_height = faceblock["aligned"].h
        aligned_width = faceblock["aligned"].w
    else:
        aligned_height = 0
        aligned_width = 0

    ndist =  1.0 if img.force_topology else node.dist
    item.branch_length = (ndist * img._scale) if img._scale else 0
    ## Calculate dimensions of the different node regions
    ##
    ##
    ##                                |
    ##                                |        ------
    ##          b-top       --------- |        |    |
    ## xoff-------------- O |b-right| |        |alg |
    ##          b-bottom    --------- |        |    |
    ##                                |        ------
    ##                                |
    ##
    ##      0     1       2     3     4           5
    ##

    item.xoff = 0.0
    # widths
    w1 = max(faceblock["branch-bottom"].w, faceblock["branch-top"].w)
    w0 = item.branch_length - w1 if item.branch_length > w1 else 0
    w2 = node.img_style["size"]
    w3 = faceblock["branch-right"].w
    w4 = node.img_style["vt_line_width"] if not _leaf(node) and len(node.children) > 1 else 0.0
    w5 = 0
    # heights
    h0 = node.img_style["hz_line_width"]
    h1 = node.img_style["hz_line_width"] + faceblock["branch-top"].h + faceblock["branch-bottom"].h
    h2 = node.img_style["size"]
    h3 = faceblock["branch-right"].h
    h4 = 0
    h5 = aligned_height

    # This fixes the problem of miss-aligned branches in ultrametric trees. If
    # there is nothing between the hz line and the vt line, then I prevent
    # vt_line_width to add extra width to the node, so node distances are
    # preserved in the img.
    if w2 == 0 and w3 == 0:
        w4 = 0

    # ignore face heights if requested
    if img.mode == "c" and img.allow_face_overlap:
        h1, h3, h5 = 0, 0, 0

    item.heights = [h0, h1, h2, h3, h4, h5]
    item.widths = [w0, w1, w2, w3, w4, w5]

    # Calculate total node size
    total_w = sum([w0, w1, w2, w3, w4, item.xoff]) # do not count aligned faces
    
    if img.mode == "c":
        max_h = max(item.heights[:4] + [min_separation])
    elif img.mode == "r":
        max_h = max(item.heights + [min_separation])

    max_h += img.branch_vertical_margin

    # correct possible unbalanced block in branch faces
    h_imbalance = abs(faceblock["branch-top"].h - faceblock["branch-bottom"].h)
    if h_imbalance + h1 > max_h:
        max_h += h_imbalance

    item.facesRegion.setRect(0, 0, w3, max_h)
    item.nodeRegion.setRect(0, 0, total_w, max_h)
    item.fullRegion.setRect(0, 0, total_w, max_h)

def update_branch_lengths(tree, n2i, n2f, img):
    for node in tree.traverse("postorder", is_leaf_fn=_leaf):
        item = n2i[node]
        ndist = 1.0 if img.force_topology else node.dist
        item.branch_length = ndist * img._scale
        w0 = 0

        if item.branch_length > item.widths[1]:
            w0 = item.widths[0] = item.branch_length - item.widths[1]
            item.nodeRegion.adjust(0, 0, w0, 0)

        child_width = 0
        if not _leaf(node):
            for ch in node.children:
                child_width = max(child_width, n2i[ch].fullRegion.width())
                if w0 and img.mode == "r":
                    #n2i[ch].translate(w0, 0) # deprecated in qt4.8
                    n2i[ch].moveBy(w0, 0)
        item.fullRegion.setWidth(item.nodeRegion.width() + child_width)

def init_tree_style(t, ts):
    custom_ts = True
    if not ts:
        custom_ts = False
        ts = TreeStyle()

    if not ts.layout_fn:
        cl = t.__class__
        try:
            ts_template = _DEFAULT_STYLE[cl]
        except KeyError as e:
            pass
        else:
            if not custom_ts:
                apply_template(ts, ts_template)
            else:
                ts.layout_fn = ts_template.get("layout_fn", None)

    return ts

