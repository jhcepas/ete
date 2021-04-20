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
import re
import math

try:
    from numpy import isfinite as _isfinite, ceil
except ImportError:
    pass
else:
    isfinite = lambda n: n and _isfinite(n)

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import six
from six.moves import map
from six.moves import range
from six.moves import zip

from .qt import (QGraphicsRectItem, QGraphicsLineItem,
                 QGraphicsPolygonItem, QGraphicsEllipseItem,
                 QPen, QColor, QBrush, QPolygonF, QFont,
                 QPixmap, QFontMetrics, QPainter, QPainterPath,
                 QRadialGradient, QGraphicsSimpleTextItem, QGraphicsTextItem,
                 QGraphicsItem, Qt,  QPointF, QRect, QRectF, QGraphicsSvgItem)

from .main import add_face_to_node, _Background, _Border, COLOR_SCHEMES

_aafgcolors = {
    'A':"#000000" ,
    'R':"#000000" ,
    'N':"#000000" ,
    'D':"#000000" ,
    'C':"#000000" ,
    'Q':"#000000" ,
    'E':"#000000" ,
    'G':"#000000" ,
    'H':"#000000" ,
    'I':"#000000" ,
    'L':"#000000" ,
    'K':"#000000" ,
    'M':"#000000" ,
    'F':"#000000" ,
    'P':"#000000" ,
    'S':"#000000" ,
    'T':"#000000" ,
    'W':"#000000" ,
    'Y':"#000000" ,
    'V':"#000000" ,
    'B':"#000000" ,
    'Z':"#000000" ,
    'X':"#000000",
    '.':"#000000",
    '-':"#000000",
}

_aabgcolors = {
    'A':"#C8C8C8" ,
    'R':"#145AFF" ,
    'N':"#00DCDC" ,
    'D':"#E60A0A" ,
    'C':"#E6E600" ,
    'Q':"#00DCDC" ,
    'E':"#E60A0A" ,
    'G':"#EBEBEB" ,
    'H':"#8282D2" ,
    'I':"#0F820F" ,
    'L':"#0F820F" ,
    'K':"#145AFF" ,
    'M':"#E6E600" ,
    'F':"#3232AA" ,
    'P':"#DC9682" ,
    'S':"#FA9600" ,
    'T':"#FA9600" ,
    'W':"#B45AB4" ,
    'Y':"#3232AA" ,
    'V':"#0F820F" ,
    'B':"#FF69B4" ,
    'Z':"#FF69B4" ,
    'X':"#BEA06E",
    '.':"#FFFFFF",
    '-':"#FFFFFF",
    }

_ntfgcolors = {
    'A':'#000000',
    'G':'#000000',
    'I':'#000000',
    'C':'#000000',
    'T':'#000000',
    'U':'#000000',
    '.':"#000000",
    '-':"#000000",
    ' ':"#000000"
    }

_ntbgcolors = {
    'A':'#A0A0FF',
    'G':'#FF7070',
    'I':'#80FFFF',
    'C':'#FF8C4B',
    'T':'#A0FFA0',
    'U':'#FF8080',
    '.':"#FFFFFF",
    '-':"#FFFFFF",
    ' ':"#FFFFFF"
}

__all__ = ["Face", "TextFace", "AttrFace", "ImgFace",
           "ProfileFace", "SequenceFace", "TreeFace",
           "RandomFace", "DynamicItemFace", "StaticItemFace",
           "CircleFace", "PieChartFace", "BarChartFace", "SeqMotifFace",
           "RectFace", "StackedBarFace", "SVGFace", "DiamondFace"]

class Face(object):
    """Base Face object. All Face types (i.e. TextFace, SeqMotifFace,
    etc.) inherit the following options:

    :param 0 margin_left: in pixels
    :param 0 margin_right: in pixels
    :param 0 margin_top: in pixels
    :param 0 margin_bottom: in pixels
    :param 1.0 opacity: a float number in the (0,1) range
    :param True rotable: If True, face will be rotated when necessary
      (i.e. when circular mode is enabled and face occupies an inverted position.)
    :param 0 hz_align: 0 left, 1 center, 2 right
    :param 1 vt_align: 0 top, 1 center, 2 bottom
    :param background.color: background color of face plus all its margins.
    :param inner_background.color: background color of the face excluding margins
    :param border: Border around face margins.
    :param inner_border: Border around face excluding margins.

    **border and inner_border sub-parameters:**

    :param 0 (inner\_)border.type: 0=solid, 1=dashed, 2=dotted
    :param None (inner\_)border.width: a positive integer number. Zero
                             indicates a cosmetic pen. This means that
                             the pen width is always drawn one pixel
                             wide, independent of the transformation
                             set on the painter. A "None" value means
                             invisible border.
    :param black (inner\_)border.color: RGB or color name in :data:`SVG_COLORS`

    See also specific options for each face type.

    """
    __slots__ = ["margin_left", "margin_right", "margin_top", "margin_bottom",
                 "pixmap", "opacity", "rotable", "rotable", "hz_align",
                 "vt_align", "background", "border", "inner_border",
                 "inner_background", "rotation", "node", "type"]

    def __init__(self):
        self.node        = None
        self.type = "pixmap" # pixmap, text or item

        self.margin_left = 0
        self.margin_right = 0
        self.margin_top = 0
        self.margin_bottom = 0
        self.pixmap = None
        self.opacity = 1.0
        self.rotable = True
        self.hz_align = 0 # 0 left, 1 center, 2 right
        self.vt_align = 1
        self.background = _Background()
        self.border = _Border()
        self.inner_border = _Border()
        self.inner_background = _Background()
        self.rotation = 0

    def _size(self):
        if self.pixmap:
            return self._width(),self._height()
        else:
            return 0, 0

    def _width(self):
        if self.pixmap:
            return self.pixmap.width()
        else:
            return 0

    def _height(self):
        if self.pixmap:
            return self.pixmap.height()
        else:
            return 0

    def load_pixmap_from_file(self, filename):
        self.pixmap = QPixmap(filename)

    def update_pixmap(self):
        pass


class TextFace(Face):
    """Static text Face object

    .. currentmodule:: ete3

    :param text:     Text to be drawn
    :param ftype:    Font type, e.g. Arial, Verdana, Courier
    :param fsize:    Font size, e.g. 10,12,6, (default=10)
    :param fgcolor:  Foreground font color. RGB code or color name in :data:`SVG_COLORS`
    :param penwidth: Penwdith used to draw the text.
    :param fstyle: "normal" or "italic"

    :param False tight_text: When False, boundaries of the text are
        approximated according to general font metrics, producing slightly
        worse aligned text faces but improving the performance of tree
        visualization in scenes with a lot of text faces.
    """
    __slots__ = ["fgcolor", "fstyle", "fsize", "ftype", "penwidth",
                 "tight_text", "bold", "_text", "_bounding_rect", "_real_rect"]

    def __init__(self, text, ftype="Verdana", fsize=10,
                 fgcolor="black", penwidth=0, fstyle="normal",
                 tight_text=False, bold=False):
        self._text = str(text)
        self._bounding_rect = None
        self._real_rect = None

        Face.__init__(self)
        self.pixmap = None
        self.type = "text"
        self.fgcolor = fgcolor
        self.ftype = ftype
        self.fsize = fsize
        self.fstyle = fstyle
        self.penwidth = penwidth
        self.tight_text = tight_text
        self.bold = bold


    def __repr__(self):
        return "Text Face [%s] (%s)" %(self._text, hex(self.__hash__()))

    def _load_bounding_rect(self, txt=None):
        if txt is None:
            txt= self.get_text()
        fm = QFontMetrics(self._get_font())
        tx_w = fm.width(txt)
        if self.tight_text:
            textr = fm.tightBoundingRect(self.get_text())
            down = textr.height() + textr.y()
            up = textr.height() - down
            asc = fm.ascent()
            des = fm.descent()
            center = (asc + des) / 2.0
            xcenter = ((up+down)/2.0) + asc - up
            self._bounding_rect = QRectF(0, asc - up, tx_w, textr.height())
            self._real_rect = QRectF(0, 0, tx_w, textr.height())
        else:
            textr = fm.boundingRect(QRect(0, 0, 0, 0), 0, txt) # see issue 241
            self._bounding_rect = QRectF(0, 0, textr.width(), textr.height())
            self._real_rect = QRectF(0, 0, textr.width(), textr.height())

    def _get_text(self):
        return self._text

    def _set_text(self, txt):
        self._text = str(txt)

    def get_bounding_rect(self):
        if not self._bounding_rect:
            self._load_bounding_rect()
        return self._bounding_rect

    def get_real_rect(self):
        if not self._real_rect:
            self._load_bounding_rect()
        return self._bounding_rect

    text = property(_get_text, _set_text)

    def _get_font(self):
        font = QFont(self.ftype, self.fsize)
        font.setBold(self.bold)
        if self.fstyle == "italic":
            font.setStyle(QFont.StyleItalic)
        elif self.fstyle == "oblique":
            font.setStyle(QFont.StyleOblique)
        return font

    def _height(self):
        return self.get_bounding_rect().height()

    def _width(self):
        return self.get_bounding_rect().width()

    def get_text(self):
        return self._text

class AttrFace(TextFace):
    """

    Dynamic text Face. Text rendered is taken from the value of a
    given node attribute.

    :param attr:     Node's attribute that will be drawn as text
    :param ftype:    Font type, e.g. Arial, Verdana, Courier, (default="Verdana")
    :param fsize:    Font size, e.g. 10,12,6, (default=10)
    :param fgcolor:  Foreground font color. RGB code or name in :data:`SVG_COLORS`
    :param penwidth: Penwdith used to draw the text. (default is 0)
    :param text_prefix: text_rendered before attribute value
    :param text_suffix: text_rendered after attribute value
    :param formatter: a text string defining a python formater to
      process the attribute value before renderer. e.g. "%0.2f"
    :param fstyle: "normal" or "italic"
    """

    __slots__ = ["attr", "text_suffix", "text_prefix", "attr_formatter", "_bounding_rect_text"]

    def __repr__(self):
        return "Attribute Face [%s] (%s)" %(self.attr, hex(self.__hash__()))

    def get_text(self):
        if self.attr_formatter:
            text = self.attr_formatter % getattr(self.node, self.attr)
        else:
            text = str(getattr(self.node, self.attr))
        text = ''.join(map(str, [self.text_prefix, \
                                     text, \
                                     self.text_suffix]))
        return text

    def get_bounding_rect(self):
        current_text = self.get_text()
        if current_text != self._bounding_rect_text:
            self._load_bounding_rect(current_text)
            self._bounding_rect_text = current_text
        return self._bounding_rect

    def get_real_rect(self):
        current_text = self.get_text()
        if current_text != self._bounding_rect_text:
            self._load_bounding_rect(current_text)
            self._bounding_rect_text = current_text
        return self._real_rect

    def __init__(self, attr, ftype="Verdana", fsize=10,
                 fgcolor="black", penwidth=0, text_prefix="",
                 text_suffix="", formatter=None, fstyle="normal",
                 tight_text=False):

        Face.__init__(self)
        TextFace.__init__(self, None, ftype, fsize, fgcolor, penwidth,
                          fstyle, tight_text)
        self.attr = attr
        self.type  = "text"
        self.text_prefix = text_prefix
        self.text_suffix = text_suffix
        self.attr_formatter = formatter
        self._bounding_rect_text = ""

class ImgFace(Face):
    """Creates a node Face using an external image file.

    :param img_file: path to the image file.
    :param None width: if provided, image will be scaled to this width (in pixels)
    :param None height: if provided, image will be scaled to this height (in pixels)
    :param False is_url: if True, img_file is considered a URL and the image is automatically downloaded

    If only one dimension value (width or height) is provided, the other
    will be calculated to keep aspect ratio.

    """

    def __init__(self, img_file, width=None, height=None, is_url=False):
        Face.__init__(self)
        self.img_file = img_file
        self.width = width
        self.height = height
        self.is_url = is_url

    def update_pixmap(self):
        if self.is_url:
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(urlopen(self.img_file).read())
        else:
            self.pixmap = QPixmap(self.img_file)

        if self.width or self.height:
            w, h = self.width, self.height
            ratio = self.pixmap.width() / float(self.pixmap.height())
            if not w:
                w = ratio * h
            if not h:
                h = w  / ratio
            self.pixmap = self.pixmap.scaled(w, h)

class ProfileFace(Face):
    """
    A profile Face for ClusterNodes

    :param max_v: maximum value used to build the build the plot scale.
    :param max_v: minimum value used to build the build the plot scale.
    :param center_v: Center value used to scale plot and heatmap.
    :param 200 width:  Plot width in pixels.
    :param 40 height: Plot width in pixels.
    :param lines style: Plot style: "lines", "bars", "cbars" or "heatmap".

    :param 2 colorscheme: colors used to create the gradient from
      min values to max values. 0=green & blue; 1=green & red; 2=red &
      blue. In all three cases, missing values are rendered in black
      and transition color (values=center) is white.
    """

    def __init__(self,max_v,min_v,center_v,width=200,height=40,style="lines", colorscheme=2, values_vector=None, deviations_vector=None):
        Face.__init__(self)
        self.profile = values_vector
        self.deviations = deviations_vector

        self.width  = width
        self.height = height
        self.max_value = max_v
        self.min_value = min_v
        self.center_v  = center_v
        self.style = style
        self.colorscheme = colorscheme

    def update_pixmap(self):
        if self.style=="lines":
            self.draw_line_profile()
        elif self.style=="heatmap":
            self.draw_heatmap_profile()
        elif self.style=="bars":
            self.draw_bar_profile()
        elif self.style=="cbars":
            self.draw_centered_bar_profile()

    def get_color_gradient(self):
        colors = []
        if self.colorscheme == 0:
            # Blue and Green
            for a in range(100,0,-1):
                color=QColor()
                color.setRgb( 200-2*a,255,200-2*a )
                colors.append(color)

            colors.append(QColor("white"))

            for a in range(0,100):
                color=QColor()
                color.setRgb( 200-2*a,200-2*a,255 )
                colors.append(color)
#            color=QColor()
#            color.setRgb( 0,255,255 )
#            colors.append(color)

        elif self.colorscheme == 1:
            for a in range(100,0,-1):
                color=QColor()
                color.setRgb( 200-2*a,255,200-2*a )
                colors.append(color)

            colors.append(QColor("white"))

            for a in range(0,100):
                color=QColor()
                color.setRgb( 255,200-2*a,200-2*a )
                colors.append(color)
#            color=QColor()
#            color.setRgb(255,255,0 )
#            colors.append(color)

        else:
            # Blue and Red
            for a in range(100,0,-1):
                color=QColor()
                color.setRgb( 200-2*a,200-2*a,255 )
                colors.append(color)

            colors.append(QColor("white"))

            for a in range(0,100):
                color=QColor()
                color.setRgb( 255,200-2*a,200-2*a )
                colors.append(color)

#            color=QColor()
#            color.setRgb( 255,0,255 )
#            colors.append(color)

        return colors

    def draw_bar_profile(self):
        # Calculate vector
        mean_vector = self.node.profile
        deviation_vector = self.node.deviation
        # If no vector, skip
        if mean_vector is None:
            return

        colors = self.get_color_gradient()

        vlength = len(mean_vector)
        # pixels per array position
        profile_width = self.width  - 40
        profile_height= self.height

        x_alpha = float( profile_width / (len(mean_vector)) )
        y_alpha = float ( (profile_height-1) / (self.max_value-self.min_value) )

        # Creates a pixmap
        self.pixmap = QPixmap(self.width,self.height)
        self.pixmap.fill(QColor("white"))
        p = QPainter(self.pixmap)

        x2 = 0
        y  = 0

        # Mean and quartiles y positions
        mean_line_y = y + profile_height/2
        line2_y     = mean_line_y + profile_height/4
        line3_y     = mean_line_y - profile_height/4

        # Draw axis and scale
        p.setPen(QColor("black"))
        p.drawRect(x2,y,profile_width, profile_height-1)
        p.setFont(QFont("Verdana",8))
        p.drawText(profile_width,y+10,"%0.3f" %self.max_value)
        p.drawText(profile_width,y+profile_height,"%0.3f" %self.min_value)

        dashedPen = QPen(QBrush(QColor("#ddd")), 0)
        dashedPen.setStyle(Qt.DashLine)

        # Draw hz grid
        p.setPen(dashedPen)
        p.drawLine(x2+1, mean_line_y, profile_width-2, mean_line_y )
        p.drawLine(x2+1, line2_y, profile_width-2, line2_y )
        p.drawLine(x2+1, line3_y, profile_width-2, line3_y )


        # Draw bars
        for pos in range(vlength):
            # first and second X pixel positions
            x1 = x2
            x2 = x1 + x_alpha

            dev1 =  self.fit_to_scale(deviation_vector[pos])
            mean1 = self.fit_to_scale(mean_vector[pos])

            # If nan value, skip
            if not isfinite(mean1):
                continue

            # Set heatmap color
            if mean1 > self.center_v:
                color_index = abs(int(ceil(((self.center_v - mean1) * 100) / (self.max_value - self.center_v))))
                customColor = colors[100 + color_index]
            elif mean1 < self.center_v:
                color_index = abs(int(ceil(((self.center_v - mean1) * 100) / (self.min_value - self.center_v))))
                customColor = colors[100 - color_index]
            else:
                customColor = colors[100]

            # mean bar high
            mean_y1     = int ( (mean1 - self.min_value) * y_alpha)

            # Draw bar border
            p.setPen(QColor("black"))
            #p.drawRect(x1+2,mean_y1, x_alpha-3, profile_height-mean_y1+1)
            # Fill bar with custom color
            p.fillRect(x1+3,profile_height-mean_y1, x_alpha-4, mean_y1-1, QBrush(customColor))

            # Draw error bars
            if dev1 != 0:
                dev_up_y1   = int((mean1+dev1 - self.min_value) * y_alpha)
                dev_down_y1 = int((mean1-dev1 - self.min_value) * y_alpha)
                p.drawLine(x1+x_alpha/2, profile_height-dev_up_y1 ,x1+x_alpha/2, profile_height-dev_down_y1 )
                p.drawLine(x1-1+x_alpha/2,  profile_height-dev_up_y1, x1+1+x_alpha/2, profile_height-dev_up_y1 )
                p.drawLine(x1-1+x_alpha/2,  profile_height-dev_down_y1, x1+1+x_alpha/2, profile_height-dev_down_y1 )

    def draw_centered_bar_profile(self):
        # Calculate vector
        mean_vector  = self.node.profile
        deviation_vector = self.node.deviation
        # If no vector, skip
        if mean_vector is None:
            return

        colors = self.get_color_gradient()

        vlength = len(mean_vector)
        # pixels per array position
        profile_width = self.width - 40
        profile_height= self.height

        x_alpha = float( profile_width / (len(mean_vector)) )
        y_alpha_up = float ( ((profile_height-1)/2) / (self.max_value-self.center_v) )
        y_alpha_down = float ( ((profile_height-1)/2) / (self.min_value-self.center_v) )

        # Creates a pixmap
        self.pixmap = QPixmap(self.width,self.height)
        self.pixmap.fill(QColor("white"))
        p = QPainter(self.pixmap)

        x2 = 0
        y  = 0

        # Mean and quartiles y positions
        mean_line_y = y + profile_height/2
        line2_y     = mean_line_y + profile_height/4
        line3_y     = mean_line_y - profile_height/4

        # Draw axis and scale
        p.setPen(QColor("black"))
        p.drawRect(x2,y,profile_width, profile_height-1)
        p.setFont(QFont("Verdana",8))
        p.drawText(profile_width,y+10,"%0.3f" %self.max_value)
        p.drawText(profile_width,y+profile_height,"%0.3f" %self.min_value)
        p.drawText(profile_width,mean_line_y,"%0.3f" %self.center_v)

        dashedPen = QPen(QBrush(QColor("#ddd")), 0)
        dashedPen.setStyle(Qt.DashLine)

        # Draw hz grid
        p.setPen(dashedPen)
        p.drawLine(x2+1, mean_line_y, profile_width-2, mean_line_y )
        p.drawLine(x2+1, line2_y, profile_width-2, line2_y )
        p.drawLine(x2+1, line3_y, profile_width-2, line3_y )


        # Draw bars
        for pos in range(vlength):
            # first and second X pixel positions
            x1 = x2
            x2 = x1 + x_alpha

            dev1 =  self.fit_to_scale( deviation_vector[pos]   )
            mean1 = self.fit_to_scale( mean_vector[pos]        )

            # If nan value, skip
            if not isfinite(mean1):
                continue

            # Set heatmap color
            if mean1>self.center_v:
                color_index = abs(int(ceil(((self.center_v-mean1)*100)/(self.max_value-self.center_v))))
                customColor = colors[100 + color_index]

                #print mean1, color_index, len(colors), "%x" %colors[100 + color_index].rgb()
                #print abs(((self.center_v-mean1)*100)/(self.max_value-self.center_v))
                #print round(((self.center_v-mean1)*100)/(self.max_value-self.center_v))

            elif mean1<self.center_v:
                color_index = abs(int(ceil(((self.center_v-mean1)*100)/(self.min_value-self.center_v))))
                customColor = colors[100 - color_index]
            else:
                customColor = colors[100]

            # mean bar high
            if mean1 < self.center_v:
                mean_y1 = int(abs((mean1 - self.center_v) * y_alpha_down))
            else:
                mean_y1 = int(abs((mean1 - self.center_v) * y_alpha_up))

            # Draw bar border
            p.setPen(QColor("black"))
            #p.drawRect(x1+2,mean_y1, x_alpha-3, profile_height-mean_y1+1)
            # Fill bar with custom color
            if mean1<self.center_v:
                p.fillRect(x1+3, mean_line_y, x_alpha-4, mean_y1, QBrush(customColor))
            else:
                p.fillRect(x1+3, mean_line_y-mean_y1, x_alpha-4, mean_y1+1, QBrush(customColor))

            # Draw error bars
            if dev1 != 0:
                if mean1<self.center_v:
                    dev_up_y1   = int((mean1+dev1 - self.center_v) * y_alpha_down)
                    dev_down_y1 = int((mean1-dev1 - self.center_v) * y_alpha_down)
                    p.drawLine(x1+x_alpha/2, mean_line_y+dev_up_y1 ,x1+x_alpha/2, mean_line_y+dev_down_y1 )
                    p.drawLine(x1-1+x_alpha/2, mean_line_y+dev_up_y1 ,x1+1+x_alpha/2, mean_line_y+dev_up_y1 )
                    p.drawLine(x1-1+x_alpha/2, mean_line_y+dev_down_y1 ,x1+1+x_alpha/2, mean_line_y+dev_down_y1 )
                else:
                    dev_up_y1   = int((mean1+dev1 - self.center_v) * y_alpha_up)
                    dev_down_y1 = int((mean1-dev1 - self.center_v) * y_alpha_up)
                    p.drawLine(x1+x_alpha/2, mean_line_y-dev_up_y1 ,x1+x_alpha/2, mean_line_y-dev_down_y1 )
                    p.drawLine(x1-1+x_alpha/2, mean_line_y-dev_up_y1 ,x1+1+x_alpha/2, mean_line_y-dev_up_y1 )
                    p.drawLine(x1-1+x_alpha/2, mean_line_y-dev_down_y1 ,x1+1+x_alpha/2, mean_line_y-dev_down_y1 )

    def draw_line_profile(self):
        # Calculate vector
        mean_vector = self.node.profile
        deviation_vector = self.node.deviation
        if mean_vector is None:
            return

        vlength = len(mean_vector)
        # pixels per array position
        profile_width = self.width - 40
        profile_height= self.height


        x_alpha = float( profile_width / (len(mean_vector)-1) )
        y_alpha = float ( (profile_height-1) / (self.max_value-self.min_value) )

        # Creates a pixmap
        self.pixmap = QPixmap(self.width,self.height)
        self.pixmap.fill(QColor("white"))
        p = QPainter(self.pixmap)

        x2 = 0
        y  = 0

        # Mean and quartiles y positions
        mean_line_y = y + profile_height/2
        line2_y     = mean_line_y + profile_height/4
        line3_y     = mean_line_y - profile_height/4

        # Draw axis and scale
        p.setPen(QColor("black"))
        p.drawRect(x2,y,profile_width, profile_height-1)
        p.setFont(QFont("Verdana",8))
        p.drawText(profile_width,y+10,"%0.3f" %self.max_value)
        p.drawText(profile_width,y+profile_height,"%0.3f" %self.min_value)
        p.drawText(profile_width,mean_line_y+5,"%0.3f" %self.center_v)

        dashedPen = QPen(QBrush(QColor("#ddd")), 0)
        dashedPen.setStyle(Qt.DashLine)

        # Draw hz grid
        p.setPen(dashedPen)
        p.drawLine(x2+1, mean_line_y, profile_width-2, mean_line_y )
        p.drawLine(x2+1, line2_y, profile_width-2, line2_y )
        p.drawLine(x2+1, line3_y, profile_width-2, line3_y )

        # Draw lines
        for pos in range(0,vlength-1):
            dev1 =  self.fit_to_scale(mean_vector[pos] + deviation_vector[pos])
            dev2 =  self.fit_to_scale(mean_vector[pos+1] + deviation_vector[pos+1])
            mean1 = self.fit_to_scale(mean_vector[pos])
            mean2 = self.fit_to_scale(mean_vector[pos+1])
            # first and second X pixel positions
            x1 = x2
            x2 = x1 + x_alpha

            # Draw vt grid
            if x2 < profile_width:
                p.setPen(dashedPen)
                p.drawLine(x2, y+1, x2, profile_height-2)

            # If nan values, continue
            if not isfinite(mean1) or not isfinite(mean2):
                continue

            # First Y postions for mean
            mean_y1 = (mean1 - self.min_value) * y_alpha
            # Second Y postions for mean
            mean_y2 = (mean2 - self.min_value) * y_alpha
            if dev1!= 0 and dev2!=0:
                # First Y postions for deviations
                dev_y1   = (dev1 - self.min_value) * y_alpha
                # Second Y postions for deviations
                dev_y2   = (dev2 - self.min_value) * y_alpha
                # Draw red deviation lines
                p.setPen(QColor("red"))
                p.drawLine(x1, profile_height-dev_y1, x2, profile_height-dev_y2)
                p.drawLine(x1, profile_height+dev_y1, x2, profile_height+dev_y2)
            # Draw blue mean line
            p.setPen(QColor("blue"))
            p.drawLine(x1, profile_height-mean_y1, x2, profile_height-mean_y2)


    def draw_heatmap_profile(self):
        # Calculate vector
        vector = self.node.profile
        deviation = self.node.deviation
        # If no vector, skip
        if vector is None:
            return

        colors = self.get_color_gradient()

        leaves = self.node.get_leaves()

        vlength = len(vector)
        # pixels per array position
        img_height = self.height * len(leaves)
        profile_width = self.width
        profile_height= img_height

        x_alpha = float( profile_width / (len(vector)) )

        # Creates a pixmap
        self.pixmap = QPixmap(self.width, img_height)
        self.pixmap.fill(QColor("white"))
        p = QPainter(self.pixmap)

        x2 = 0
        y  = 0
        y_step = self.height
        for leaf in leaves:
            mean_vector = leaf.profile
            deviation_vector = leaf.deviation
            # Draw heatmap
            for pos in range(vlength):
                # first and second X pixel positions
                x1 = x2
                x2 = x1 + x_alpha
                dev1 = self.fit_to_scale(deviation_vector[pos])
                mean1 = self.fit_to_scale(mean_vector[pos])
                # Set heatmap color
                if not isfinite(mean1):
                    customColor = QColor("black")
                elif mean1>self.center_v:
                    color_index = abs(int(ceil(((self.center_v-mean1)*100)/(self.max_value-self.center_v))))
                    customColor = colors[100 + color_index]
                elif mean1<self.center_v:
                    color_index = abs(int(ceil(((self.center_v-mean1)*100)/(self.min_value-self.center_v))))
                    customColor = colors[100 - color_index]
                else:
                    customColor = colors[100]

                # Fill bar with custom color
                p.fillRect(x1, y, x_alpha, y_step, QBrush(customColor))
            y+= y_step
            x2 = 0
        p.end()

    def fit_to_scale(self,v):
        if v<self.min_value:
            return float(self.min_value)
        elif v>self.max_value:
            return float(self.max_value)
        else:
            return float(v)


class OLD_SequenceFace(Face):
    """ Creates a new molecular sequence face object.


    :param seq:  Sequence string to be drawn
    :param seqtype: Type of sequence: "nt" or "aa"
    :param fsize:   Font size,  (default=10)

    You can set custom colors for aminoacids or nucleotides:

    :param aafg: a dictionary in which keys are aa codes and values
      are foreground RGB colors

    :param aabg: a dictionary in which keys are aa codes and values
      are background RGB colors

    :param ntfg: a dictionary in which keys are nucleotides codes
      and values are foreground RGB colors

    :param ntbg: a dictionary in which keys are nucleotides codes and values
      are background RGB colors

    """

    def __init__(self, seq, seqtype, fsize=10, aafg=None,  \
                     aabg=None, ntfg=None, ntbg=None):

        Face.__init__(self)
        self.seq  = seq
        self.fsize= fsize
        self.fsize = fsize
        self.style = seqtype

        if not aafg:
            aafg = _aafgcolors
        if not aabg:
            aabg = _aabgcolors
        if not ntfg:
            ntfg = _ntfgcolors
        if not ntbg:
            ntbg = _ntbgcolors

        self.aafg = aafg
        self.aabg = aabg
        self.ntfg = ntfg
        self.ntbg = ntbg

    def update_pixmap(self):
        font = QFont("Courier", self.fsize)
        fm = QFontMetrics(font)
        height = fm.leading() + fm.overlinePos() + fm.underlinePos()
        #width  = fm.size(Qt.AlignTop, self.seq).width()
        width = self.fsize * len(self.seq)

        self.pixmap = QPixmap(width,height)
        self.pixmap.fill()
        p = QPainter(self.pixmap)
        x = 0
        y = height - fm.underlinePos()*2

        p.setFont(font)

        for letter in self.seq:
            letter = letter.upper()

            if self.style=="nt":
                letter_brush = QBrush(QColor(self.ntbg.get(letter,"white" )))
                letter_pen = QPen(QColor(self.ntfg.get(letter, "black")))
            else:
                letter_brush = QBrush(QColor(self.aabg.get(letter,"white" )))
                letter_pen = QPen(QColor(self.aafg.get(letter,"black" )))

            p.setPen(letter_pen)
            p.fillRect(x,0,width, height,letter_brush)
            p.drawText(x, y, letter)
            x += float(width)/len(self.seq)
        p.end()

class TreeFace(Face):
    """
    .. versionadded:: 2.1

    Creates a Face containing a Tree object. Yes, a tree within a tree :)

    :param tree: An ETE Tree instance (Tree, PhyloTree, etc...)
    :param tree_style: A TreeStyle instance defining how tree show be drawn

    """
    def __init__(self, tree, tree_style):
        Face.__init__(self)
        self.type = "item"
        self.root_node = tree
        self.img = tree_style
        self.item = None

    def update_items(self):
        from .qt4_render import render, init_tree_style
        ts = init_tree_style(self.root_node, self.img)
        hide_root = False
        if self.root_node is self.node:
            hide_root = True
        self.item, self.n2i, self.n2f = render(self.root_node, ts, hide_root)

    def _width(self):
        return self.item.rect().width()

    def _height(self):
        return self.item.rect().height()


def _label_painter(obj, p, option, widget):
    """
    Delegate for graphics objects (RectItem, SphereItem) to
    add an approximately-centered (gnashing of teeth) label

    :param obj: the object (standard parameter to paint() method)
    :param p: a QPainter (see paint() method)
    :param option: (see paint() method)
    :param widget: (see paint() method)

    """
    if not obj.label:
        return
    try:
        lcolor = obj.label['color']
        llabel = obj.label['text'] if 'text' in obj.label else 'No label text!'
        lfont = obj.label['font'] if 'font' in obj.label else "Verdana"
        lsize = 12 if 'fontsize' not in obj.label else int(obj.label['fontsize'])
        p.setFont(QFont(lfont, lsize))
        p.setPen(QPen(QColor(lcolor)))
        fm = QFontMetrics(p.font())
        metrics = fm.boundingRect(QRect(), Qt.AlignCenter, llabel)
        rect = obj.boundingRect()
        p.drawText(int(rect.width()/2-(metrics.width()/2)),
                   int(rect.height()/2+(metrics.height()/2)),
                   llabel)
    except Exception as e:
        print('Labelling problem: %s' % (e))


class _SphereItem(QGraphicsEllipseItem):
    def __init__(self, radius, color, solid=False, label=None):
        self.label = label
        r = radius
        d = r*2
        QGraphicsEllipseItem.__init__(self, 0, 0, d, d)
        if solid:
            self.setBrush(QBrush(QColor(color)))
        else:
            self.gradient = QRadialGradient(r, r, r,(d)/3,(d)/3)
            self.gradient.setColorAt(0.05, Qt.white)
            self.gradient.setColorAt(1, QColor(color))
            self.setBrush(QBrush(self.gradient))
        self.setPen(QPen(QColor(color)))

    def paint(self, p, option, widget):
        super(_SphereItem, self).paint(p, option, widget)
        _label_painter(self, p, option, widget)


class _RectItem(QGraphicsRectItem):
    def __init__(self, w, h, bgcolor, fgcolor, label=None):
        QGraphicsRectItem.__init__(self)
        self.label = label
        self.setRect(0, 0, w, h)
        if bgcolor:
            self.setBrush(QBrush(QColor(bgcolor)))
        else:
            self.setBrush(QBrush(Qt.NoBrush))
        if fgcolor:
            self.setPen(QPen(QColor(fgcolor)))
        else:
            self.setPen(QPen(Qt.NoPen))

    def paint(self, p, option, widget):
        super(_RectItem, self).paint(p, option, widget)
        _label_painter(self, p, option, widget)


class RectFace(Face):
    """
    .. versionadded:: 2.3

    Creates a Rectangular solid face.

    :param label: optional text string to annotate the face: Default
        value is None; label can also be a dict with attributes text,
        font, color, and fontsize color defaults to background color,
        font to Verdana, fontsize to 12
    """
    def __init__(self, width, height, fgcolor, bgcolor, label=None):
        Face.__init__(self)
        self.width = width
        self.height = height
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.type = "item"
        self.rotable = True
        self.label = label
        if label:
            if not isinstance(label, dict):
                self.label = {'text' : label}
            if 'color' not in self.label:
                self.label['color'] = bgcolor

    def update_items(self):
        self.item = _RectItem(self.width, self.height, self.bgcolor, self.fgcolor, label=self.label)

    def _width(self):
        return self.width

    def _height(self):
        return self.height


class CircleFace(Face):
    """
    .. versionadded:: 2.1

    Creates a Circle or Sphere Face.

    :param radius: integer number defining the radius of the face
    :param color: Color used to fill the circle. RGB code or name in :data:`SVG_COLORS`
    :param "circle" style: Valid values are "circle" or "sphere"
    :param label: optional text string to annotate the face: Default
        value is None; label can also be a dict with attributes text,
        font, color, and fontsize color defaults to circle color
        (because it looks nice with "sphere"), font to Verdana,
        fontsize to 12
    """

    def __init__(self, radius, color, style="circle", label=None):
        Face.__init__(self)
        self.radius = radius
        self.style = style
        self.color = color
        self.type = "item"
        self.rotable = False
        self.label = label
        if label:
            if not isinstance(label, dict):
                self.label = {'text' : label}
            if 'color' not in self.label:
                self.label['color'] = color

    def update_items(self):
        if self.style == "circle":
            self.item = _SphereItem(self.radius, self.color, solid=True, label=self.label)
        elif self.style == "sphere":
            self.item = _SphereItem(self.radius, self.color, label=self.label)

    def _width(self):
        return self.item.rect().width()

    def _height(self):
        return self.item.rect().height()


class StaticItemFace(Face):
    """
    .. versionadded:: 2.1

    Creates a face based on an external QtGraphicsItem object.
    QGraphicsItem object is expected to be independent from tree node
    properties, so its content is assumed to be static (drawn only
    once, no updates when tree changes).

    :param item: an object based on QGraphicsItem
    """
    def __init__(self, item):
        Face.__init__(self)
        self.type = "item"
        self.item = item

    def update_items(self):
        return

    def _width(self):
        return self.item.rect().width()

    def _height(self):
        return self.item.rect().height()


class DynamicItemFace(Face):
    """
    .. versionadded:: 2.1

    Creates a face based on an external QGraphicsItem object whose
    content depends on the node that is linked to.

    :param constructor: A pointer to a method (function or class
      constructor) returning a QGraphicsItem based
      object. "constructor" method is expected to receive a node
      instance as the first argument. The rest of arguments passed to
      ItemFace are optional and will passed also to the constructor
      function.
    """

    def __init__(self, constructor, *args, **kargs):
        Face.__init__(self)
        self.type = "item"
        self.item = None
        self.constructor = constructor
        self.args = args
        self.kargs = kargs

    def update_items(self):
        self.item = self.constructor(self.node, *self.args, **self.kargs)

    def _width(self):
        return self.item.rect().width()

    def _height(self):
        return self.item.rect().height()

class RandomFace(Face):
    def __init__(self):
        Face.__init__(self)
        self.type = "item"

    def update_items(self):
        import random
        w = random.randint(4, 100)
        h = random.randint(4, 100)
        self.tree_partition = QGraphicsRectItem(0,0,w, h)
        self.tree_partition.setBrush(QBrush(QColor("green")))

    def _width(self):
        return self.tree_partition.rect().width()

    def _height(self):
        return self.tree_partition.rect().height()

class _PieChartItem(QGraphicsRectItem):
    def __init__(self, percents, width, height, colors, line_color=None):
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        self.percents = percents
        self.colors = colors
        self.line_color = line_color

    def paint(self, painter, option, widget):
        a = 5760
        angle_start = 0

        if not self.line_color:
            painter.setPen(Qt.NoPen)
        else:
            painter.setPen(QColor(self.line_color))

        for i, p in enumerate(self.percents):
            col = self.colors[i]
            painter.setBrush(QBrush(QColor(col)))
            angle_span = (p/100.) * a
            painter.drawPie(self.rect(), angle_start, angle_span )
            angle_start += angle_span


class PieChartFace(StaticItemFace):
    """
    .. versionadded:: 2.2

    :param percents: a list of values summing up 100.
    :param width: width of the piechart
    :param height: height of the piechart
    :param colors: a list of colors (same length as percents)
    :param line_color: color used to render the border of the piechart (None=transparent)

    """
    def __init__(self, percents, width, height, colors=None, line_color=None):
        Face.__init__(self)

        if round(sum(percents)) > 100:
            raise ValueError("PieChartItem: percentage values > 100")

        self.type = "item"
        self.item = None
        self.percents = percents
        if not colors:
            colors = COLOR_SCHEMES["paired"]
        self.colors =  colors
        self.width = width
        self.height = height
        self.line_color = line_color

    def update_items(self):
        self.item = _PieChartItem(self.percents, self.width,
                                  self.height, self.colors, self.line_color)

    def _width(self):
        return self.item.rect().width()

    def _height(self):
        return self.item.rect().height()


class _StackedBarItem(QGraphicsRectItem):
    def __init__(self, percents, width, height, colors, line_color=None):
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        self.percents = percents
        self.colors = colors
        self.line_color = line_color

    def paint(self, painter, option, widget):
        total_w = self.rect().width()
        total_h = self.rect().height()
        painter.setBrush(Qt.NoBrush)

        if not self.line_color:
            painter.setPen(Qt.NoPen)
        else:
            painter.setPen(QColor(self.line_color))

        x = 0
        for i, p in enumerate(self.percents):
            col = self.colors[i]
            w = (p * total_w) / 100. # assuming p is between 0 and 100
            painter.fillRect(QRectF(x, 0, w, total_h), QColor(col))
            x += w

class StackedBarFace(StaticItemFace):
    def __init__(self, percents, width, height, colors=None, line_color=None):
        """
        .. versionadded:: 2.3

        :param percents: a list of values summing up 100.
        :param width: width of the bar
        :param height: height of the bar
        :param colors: a list of colors (same length as percents)
        :param line_color: color used to render the border of the bar (None=transparent)
        """
        Face.__init__(self)

        if round(sum(percents)) > 100:
            raise ValueError("percentage values > 100")

        self.type = "item"
        self.item = None
        self.percents = percents
        if not colors:
            colors = COLOR_SCHEMES["paired"]
        self.colors =  colors
        self.width = width
        self.height = height
        self.line_color = line_color

    def update_items(self):
        self.item = _StackedBarItem(self.percents, self.width,
                                 self.height, self.colors, self.line_color)

    def _width(self):
        return self.item.rect().width()

    def _height(self):
        return self.item.rect().height()



class BarChartFace(Face):
    """
    .. versionadded:: 2.2

    :param values: a list of values each representing a vertical bar.
    :param 200 width: width of the bar chart.
    :param 100 height: height of the bar chart
    :param None colors: a list of colors, one per bar value
    :param None labels: a list of labels, one per bar
    :param 0 min_value: min value to set the scale of the chart.
    :param None max_value: max value to set the scale of the chart.

    """
    def __init__(self, values, deviations=None, width=200, height=100,
                 colors=None, labels=None, min_value=0, max_value=None,
                 label_fsize=6, scale_fsize=6):
        Face.__init__(self)
        self.type = "item"
        self.item = None
        self.values = values
        if not deviations:
            self.deviations = [0] * len(values)
        else:
            self.deviations = deviations

        if not colors:
            colors = COLOR_SCHEMES["paired"]
        self.colors =  colors

        self.width = width
        self.height = height
        self.labels = labels
        self.max_value = max_value
        self.min_value = min_value
        self.margin_left = 1
        self.margin_right = 1
        self.margin_top = 2
        self.margin_bottom = 2
        self.label_fsize = label_fsize
        self.scale_fsize = scale_fsize

    def update_items(self):
        self.item = _BarChartItem(self.values, self.deviations, self.width,
                                  self.height, self.colors, self.labels,
                                  self.min_value, self.max_value,
                                  self.label_fsize, self.scale_fsize)
    def _width(self):
        return self.item.rect().width()

    def _height(self):
        return self.item.rect().height()


class _BarChartItem(QGraphicsRectItem):
    def __init__(self, values, deviations, width, height, colors, labels,
                 min_value, max_value, label_fsize, scale_fsize):
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        self.values = values
        self.colors = colors
        self.width = float(width)
        self.height = float(height)
        self.draw_border = True
        self.draw_grid = False
        self.draw_scale = True
        self.labels = labels
        self.max_value = max_value
        self.min_value = min_value
        self.deviations = deviations
        self.label_fsize = label_fsize
        self.scale_fsize = scale_fsize

        self.set_real_size()

    def set_real_size(self):
        label_height = 0
        scale_width = 0
        margin = 2

        if self.max_value is None:
            max_value = max([v+d for v,d in zip(self.values, self.deviations) if isfinite(v)])
        else:
            max_value = self.max_value

        if self.min_value is None:
            min_value = min([v+d for v,d in zip(self.values, self.deviations) if isfinite(v)])
        else:
            min_value = self.min_value

        if self.draw_scale:
            max_string = "% 7.2f" %max_value
            min_string = "% 7.2f" %min_value
            fm = QFontMetrics(QFont("Verdana", self.scale_fsize))
            max_string_metrics = fm.boundingRect(QRect(), \
                                                 Qt.AlignLeft, \
                                                 max_string)
            min_string_metrics = fm.boundingRect(QRect(), \
                                                 Qt.AlignLeft, \
                                                 min_string)
            scale_width = margin + max(max_string_metrics.width(),
                                             min_string_metrics.width())

        if self.labels:
            fm = QFontMetrics(QFont("Verdana", self.label_fsize))
            longest_label = sorted(self.labels, key=lambda x: len(x))[-1]
            label_height = fm.boundingRect(QRect(), Qt.AlignLeft, longest_label).width() + margin
            label_width = fm.height() * len(self.labels)
            self.width = max(label_width, self.width)

        self.setRect(0, 0, self.width + scale_width, self.height + label_height)


    def paint(self, p, option, widget):
        colors = self.colors
        values = self.values
        deviations = self.deviations
        p.setBrush(Qt.NoBrush)
        margin = 2
        spacer = 3
        spacing_length = (spacer*(len(values)-1))
        height = self.height

        if self.max_value is None:
            max_value = max([v+d for v,d in zip(values, deviations) if isfinite(v)])
        else:
            max_value = self.max_value

        if self.min_value is None:
            min_value = min([v+d for v,d in zip(values, deviations) if isfinite(v)])
        else:
            min_value = self.min_value

        plot_width = self.width
        plot_height = self.height

        x_alpha = float((plot_width - spacing_length) / (len(values)))
        if x_alpha < 1:
            raise ValueError("BarChartFace is too small")

        y_alpha = float ( (plot_height-3) / float(max_value - min_value) )
        x = 0
        y = 0

        # Mean and quartiles y positions
        mean_line_y = y + (plot_height / 2.0)
        line2_y = mean_line_y + (plot_height/4.0)
        line3_y = mean_line_y - (plot_height/4.0)

        if self.draw_border:
            p.setPen(QColor("black"))
            p.drawRect(x, y + 1, plot_width, plot_height)

        if self.draw_scale:
            p.setFont(QFont("Verdana", self.scale_fsize))
            font_height = QFontMetrics(p.font()).height()
            max_string = "% 7.2f" %max_value
            min_string = "% 7.2f" %min_value
            p.drawText(plot_width + margin, font_height-2, max_string)
            p.drawText(plot_width + margin, plot_height - 2, min_string)
            p.drawLine(plot_width + margin - 1, 1, plot_width + margin - 1, plot_height+1)
            p.drawLine(plot_width + margin - 1, 1, plot_width + margin + 2, 1)
            p.drawLine(plot_width + margin - 1, plot_height+1, plot_width + margin + 2, plot_height+1)

        if self.draw_grid:
            dashedPen = QPen(QBrush(QColor("#ddd")), 0)
            dashedPen.setStyle(Qt.DashLine)
            p.setPen(dashedPen)
            p.drawLine(x+1, mean_line_y, plot_width - 2, mean_line_y)
            p.drawLine(x+1, line2_y, plot_width - 2, line2_y )
            p.drawLine(x+1, line3_y, plot_width - 2, line3_y )

        # Draw bars
        p.setFont(QFont("Verdana", self.label_fsize))
        label_height = self.rect().height() - self.height
        label_width = QFontMetrics(p.font()).height()
        for pos in range(len(values)):
            # first and second X pixel positions
            x1 = x
            x = x1 + x_alpha + spacer

            std =  deviations[pos]
            val = values[pos]

            if self.labels:
                p.save()
                p.translate(x1, plot_height+2)
                p.rotate(90)
                p.drawText(0, -x_alpha, label_height, x_alpha, Qt.AlignVCenter, str(self.labels[pos]))
                #p.drawRect(0, -x_alpha, label_height, x_alpha)
                p.restore()

            # If nan value, skip
            if not isfinite(val):
                continue

            color = QColor(colors[pos])
            # mean bar high
            mean_y1     = int((val - min_value) * y_alpha)
            # Draw bar border
            p.setPen(QColor("black"))

            # Fill bar with custom color
            p.fillRect(x1, height - mean_y1, x_alpha, mean_y1, QBrush(color))

            # Draw error bars
            if std != 0:
                dev_up_y1   = int((val + std - min_value) * y_alpha)
                dev_down_y1 = int((val - std - min_value) * y_alpha)
                center_x = x1 + (x_alpha / 2)
                p.drawLine(center_x, plot_height - dev_up_y1, center_x, plot_height - dev_down_y1)
                p.drawLine(center_x + 1, plot_height - dev_up_y1, center_x -1, plot_height - dev_up_y1)
                p.drawLine(center_x + 1, plot_height - dev_down_y1, center_x -1, plot_height - dev_down_y1)



class QGraphicsTriangleItem(QGraphicsPolygonItem):
    def __init__(self, width, height, orientation=1):
        self.tri = QPolygonF()
        if orientation == 1:
            self.tri.append(QPointF(0, 0))
            self.tri.append(QPointF(0, height))
            self.tri.append(QPointF(width, height / 2.0))
            self.tri.append(QPointF(0, 0))
        elif orientation == 2:
            self.tri.append(QPointF(0, 0))
            self.tri.append(QPointF(width, 0))
            self.tri.append(QPointF(width / 2.0, height))
            self.tri.append(QPointF(0, 0))
        elif orientation == 3:
            self.tri.append(QPointF(0, height / 2.0))
            self.tri.append(QPointF(width, 0))
            self.tri.append(QPointF(width, height))
            self.tri.append(QPointF(0, height / 2.0))
        elif orientation == 4:
            self.tri.append(QPointF(0, height))
            self.tri.append(QPointF(width, height))
            self.tri.append(QPointF(width / 2.0, 0))
            self.tri.append(QPointF(0, height))

        QGraphicsPolygonItem.__init__(self, self.tri)

class QGraphicsDiamondItem(QGraphicsPolygonItem):
    def __init__(self, width, height):
        self.pol = QPolygonF()
        self.pol.append(QPointF(width / 2.0, 0))
        self.pol.append(QPointF(width, height / 2.0))
        self.pol.append(QPointF(width / 2.0, height))
        self.pol.append(QPointF(0, height / 2.0))
        self.pol.append(QPointF(width / 2.0, 0))
        QGraphicsPolygonItem.__init__(self, self.pol)

class QGraphicsRoundRectItem(QGraphicsRectItem):
    def __init__(self, *args, **kargs):
        QGraphicsRectItem.__init__(self, *args, **kargs)
    def paint(self, p, option, widget):
        p.setPen(self.pen())
        p.setBrush(self.brush())
        p.drawRoundedRect(self.rect(), 3, 3)

class SequenceItem(QGraphicsRectItem):
    def __init__(self, seq, seqtype="aa", poswidth=1, posheight=10,
                 draw_text=False):
        QGraphicsRectItem.__init__(self)
        self.seq = seq
        self.seqtype = seqtype
        self.poswidth = poswidth
        self.posheight = posheight
        if draw_text:
            self.poswidth = poswidth
        self.draw_text = draw_text
        if seqtype == "aa":
            self.fg = _aafgcolors
            self.bg = _aabgcolors
        elif seqtype == "nt":
            self.fg = _ntfgcolors
            self.bg = _ntbgcolors
        self.setRect(0, 0, len(seq) * poswidth, posheight)

    def paint(self, p, option, widget):
        x, y = 0, 0
        qfont = QFont("Courier")
        current_pixel = 0
        blackPen = QPen(QColor("black"))
        for letter in self.seq:
            letter = letter.upper()
            if x >= current_pixel:
                if self.draw_text and self.poswidth >= 8:
                    br = QBrush(QColor(self.bg.get(letter, "white")))
                    p.setPen(blackPen)
                    p.fillRect(x, 0, self.poswidth, self.posheight, br)
                    qfont.setPixelSize(min(self.posheight, self.poswidth))
                    p.setFont(qfont)
                    p.setBrush(QBrush(QColor("black")))
                    p.drawText(x, 0, self.poswidth, self.posheight,
                               Qt.AlignCenter |  Qt.AlignVCenter,
                               letter)
                elif letter == "-" or letter == ".":
                    p.setPen(blackPen)
                    p.drawLine(x, self.posheight/2, x+self.poswidth, self.posheight/2)

                else:
                    br = QBrush(QColor(self.bg.get(letter, "white")))
                    p.fillRect(x, 0, max(1, self.poswidth), self.posheight, br)
                    #p.setPen(QPen(QColor(self.bg.get(letter, "black"))))
                    #p.drawLine(x, 0, x, self.posheight)
                current_pixel = int(x)
            x += self.poswidth


class TextLabelItem(QGraphicsRectItem):
    def __init__(self, text, w, h, fcolor="black", ffam="Arial", fsize=10):
        QGraphicsRectItem.__init__(self)
        self.setRect(0, 0, w, h)
        self.text = text
        self.fsize = int(fsize)
        self.ffam = ffam
        self.fcolor = fcolor


    def paint(self, p, option, widget):
        color = QColor(self.fcolor)
        p.setPen(color)
        p.setBrush(QBrush(color))

        qfont = QFont()
        qfont.setFamily(self.ffam)
        qfont.setPointSize(self.fsize)
        p.setFont(qfont)
        p.save()
        p.setBrush(Qt.NoBrush)
        p.setClipRect(self.rect())
        p.drawText(self.rect(), Qt.AlignCenter |  Qt.AlignVCenter, self.text)
        p.restore()



        #p.drawRect(self.rect())

class SeqMotifRectItem(QGraphicsRectItem):
    pass

class SeqMotifFace(StaticItemFace):
    """.. versionadded:: 2.2

    Creates a face based on an amino acid or nucleotide sequence and a
    list of motif regions.

    :param None seq: a text string containing an aa or nt sequence. If
        not provided, ``seq`` and ``compactseq`` motif modes will not be
        available.

    :param None motifs: a list of motif regions referred to original
        sequence. Each motif is defined as a list containing the
        following information:

        ::

          motifs = [[seq.start, seq.end, shape, width, height, fgcolor, bgcolor, text_label],
                   [seq.start, seq.end, shape, width, height, fgcolor, bgcolor, text_label],
                   ...
                  ]

        Where:

         * **seq.start:** Motif start position referred to the full sequence (1-based)
         * **seq.end:** Motif end position referred to the full sequence (1-based)
         * **shape:** Shape used to draw the motif. Available values are:

            * ``o`` = circle or ellipse
            * ``>``  = triangle (base to the left)
            * ``<``  = triangle (base to the left)
            * ``^``  = triangle (base at bottom)
            * ``v``  = triangle (base on top )
            * ``<>`` = diamond
            * ``[]`` = rectangle
            * ``()`` = round corner rectangle
            * ``line`` = horizontal line
            * ``blank`` = blank space

            * ``seq`` = Show a color and the corresponding letter of each sequence position
            * ``compactseq`` = Show a thinh vertical color line for each sequence position

         * **width:** total width of the motif (or sequence position width if seq motif type)
         * **height:** total height of the motif (or sequence position height if seq motif type)
         * **fgcolor:** color for the motif shape border
         * **bgcolor:** motif background color. Color code or name can be preceded with the "rgradient:" tag to create a radial gradient effect.
         * **text_label:** a text label in the format 'FontType|FontSize|FontColor|Text', for instance, arial|8|white|MotifName""

    :param line gap_format: default shape for the gaps between motifs
    :param blockseq seq_format: default shape for the seq regions not covered in motifs
    """

    def __init__(self, seq=None, motifs=None, seqtype="aa",
                 gap_format="line", seq_format="()",
                 scale_factor=1, height=10, width=10,
                 fgcolor='slategrey', bgcolor='slategrey', gapcolor='black'):

        if not motifs and not seq:
            raise ValueError("At least one argument (seq or motifs) should be provided. ")

        StaticItemFace.__init__(self, None)
        self.seq = seq
        self.motifs = motifs

        self.scale_factor = scale_factor
        self.overlaping_motif_opacity = 0.5
        self.adjust_to_text = False

        self.gap_format = gap_format
        self.seq_format = seq_format

        if seqtype == "aa":
            self.fg = _aafgcolors
            self.bg = _aabgcolors
        elif seqtype == "nt":
            self.fg = _ntfgcolors
            self.bg = _ntbgcolors

        self.h = height
        self.w = width
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.gapcolor = gapcolor
        self.regions = []

        self.build_regions()

    def build_regions(self):
        # Build and sort regions
        motifs = self.motifs
        if self.seq:
            seq = self.seq
        else:
            seq = "-" * max([m[1] for m in motifs])

        # if only sequence is provided, build regions out of gap spaces
        if not motifs:
            if self.seq_format == "seq":
                motifs = [[0, len(seq), "seq", 10, self.h, None, None, None]]
            else:
                motifs = []
                pos = 0
                for reg in re.split('([^-]+)', seq):
                    if reg:
                        if not reg.startswith("-"):
                            if self.seq_format == "compactseq":
                                motifs.append([pos, pos+len(reg)-1, "compactseq", 1, self.h, None, None, None])
                            elif self.seq_format == "line":
                                motifs.append([pos, pos+len(reg)-1, "-", 1, 1, self.fgcolor, None, None])
                            else:
                                motifs.append([pos, pos+len(reg)-1, self.seq_format, None, self.h, self.fgcolor, self.bgcolor, None])
                        pos += len(reg)

        motifs.sort()

        # complete missing regions
        current_seq_pos = 0
        for index, mf in enumerate(motifs):
            start, end, typ, w, h, fg, bg, name = mf
            if start > current_seq_pos:
                pos = current_seq_pos
                for reg in re.split('([^-]+)', seq[current_seq_pos:start]):
                    if reg:
                        if reg.startswith("-") and self.seq_format != "seq":
                            self.regions.append([pos, pos+len(reg)-1, self.gap_format, 1, 1, self.gapcolor, None, None])
                        else:
                            self.regions.append([pos, pos+len(reg)-1, self.seq_format,
                                                 self.w, self.h,
                                                 self.fgcolor, self.bgcolor, None])
                    pos += len(reg)
                current_seq_pos = start

            self.regions.append(mf)
            current_seq_pos = end + 1

        if len(seq) > current_seq_pos:
            pos = current_seq_pos
            for reg in re.split('([^-]+)', seq[current_seq_pos:]):
                if reg:
                    if reg.startswith("-") and self.seq_format != "seq":
                        self.regions.append([pos, pos+len(reg)-1, self.gap_format, 1, 1, self.gapcolor, None, None])
                    else:
                        self.regions.append([pos, pos+len(reg)-1, self.seq_format,
                                             self.w, self.h,
                                             self.fgcolor, self.bgcolor, None])
                    pos += len(reg)

        #print ('\n'.join(map(str, self.regions)))

    def update_items(self):
        # master item, all object should have this as parent
        self.item = SeqMotifRectItem()

        # Calculate max height of all elements in this motif object
        max_h = max([reg[4] for index, reg
                     in enumerate(self.regions)])
        y_center = max_h / 2

        max_x_pos = 0
        current_seq_end = 0


        seq_x_correction = {}
        for seq_start, seq_end, typ, wf, h, fg, bg, name in self.regions:
            if typ == "seq":
                seq_x_correction[(seq_start, seq_end)] = wf * self.scale_factor

        for index, (seq_start, seq_end, typ, wf, h, fg, bg, name) in enumerate(self.regions):
            # this are the actual coordinates mapping to the sequence
            opacity = 1
            w = (seq_end - seq_start) + 1
            xstart = seq_start

            if self.scale_factor:
                w *= self.scale_factor
                if wf:
                    wf *= self.scale_factor
                xstart *= self.scale_factor


            # this loop corrects x-positions for overlaping motifs and takes
            # into account the different scales used for different motif types,
            # i.e. seq
            for (old_start, old_end), correction in six.iteritems(seq_x_correction):
                seq_range = None
                if seq_start > old_start:
                    seq_range = min(old_end, seq_start) - old_start
                    xstart -= seq_range
                    xstart += (seq_range * correction)
                elif seq_end > old_start:
                    seq_range = min(old_end, seq_end) - old_start
                # corrects also the width for the overlaping part
                if seq_range:
                    if seq_start < old_end or seq_end < seq_start:
                        w -= seq_range
                        w += (seq_range * correction)

            if seq_start < current_seq_end:
                opacity = self.overlaping_motif_opacity

            # expected width of the object to be drawn
            ystart = y_center - (h/2)

            if typ == "-" or typ == "line":
                i = QGraphicsLineItem(0, h/2, w, h/2)
            elif typ == " " or typ == "blank":
                i = None
            elif typ == "o":
                i = QGraphicsEllipseItem(0, 0, w, h)
            elif typ == ">":
                i = QGraphicsTriangleItem(w, h, orientation=1)
            elif typ == "v":
                i = QGraphicsTriangleItem(w, h, orientation=2)
            elif typ == "<":
                i = QGraphicsTriangleItem(w, h, orientation=3)
            elif typ == "^":
                i = QGraphicsTriangleItem(w, h, orientation=4)
            elif typ == "<>":
                i = QGraphicsDiamondItem(w, h)
            elif typ == "[]":
                i = QGraphicsRectItem(0, 0, w, h)
            elif typ == "()":
                i = QGraphicsRoundRectItem(0, 0, w, h)

            elif typ == "seq" and self.seq:
                i = SequenceItem(self.seq[seq_start:seq_end+1],
                                 poswidth=wf,
                                 posheight=h, draw_text=True)
                w = i.rect().width()
                h = i.rect().height()
            elif typ == "compactseq" and self.seq:
                i = SequenceItem(self.seq[seq_start:seq_end+1], poswidth=1*self.scale_factor,
                                 posheight=h, draw_text=False)
                w = i.rect().width()
                h = i.rect().height()
            else:
                i = QGraphicsSimpleTextItem("?")

            if name and i:
                family, fsize, fcolor, text = name.split("|")
                #qfmetrics = QFontMetrics(qfont)
                #txth = qfmetrics.height()
                #txtw = qfmetrics.width(text)
                txt_item = TextLabelItem(text, w, h,
                                         fsize=fsize, ffam=family, fcolor=fcolor)
                # enlarges circle domains to fit text
                #if typ == "o":
                #    min_r = math.hypot(txtw/2.0, txth/2.0)
                #    txtw = max(txtw, min_r*2)

                #y_txt_start = (max_h/2.0) - (h/2.0)
                txt_item.setParentItem(i)
                #txt_item.setPos(0, ystart)


            if i:
                i.setParentItem(self.item)
                i.setPos(xstart, ystart)

                if bg:
                    if bg.startswith("rgradient:"):
                        bg = bg.replace("rgradient:", "")
                        try:
                            c1, c2 = bg.split("|")
                        except ValueError:
                            c1, c2 = bg, "white"
                        rect = i.boundingRect()
                        gr = QRadialGradient(rect.center(), rect.width()/2)
                        gr.setColorAt(0, QColor(c2))
                        gr.setColorAt(1, QColor(c1))
                        color = gr
                    else:
                        color = QColor(bg)
                    try:
                        i.setBrush(color)
                    except:
                        pass

                if fg:
                    i.setPen(QColor(fg))

                if opacity < 1:
                    i.setOpacity(opacity)

            max_x_pos = max(max_x_pos, xstart + w)
            current_seq_end = max(seq_end, current_seq_end)

        self.item.setRect(0, 0, max_x_pos, max_h)

        self.item.setPen(QPen(Qt.NoPen))



class SequencePlotFace(StaticItemFace):
    """
    To draw plots, usually correlated to columns in alignment

    :argument values : a list of values
    :argument None errors : a list of errors associated to each value. elements of the list can contain a list with lower and upper error, if they are different.
    :argument None colors : a list of colors associated to each value
    :argument None header : a title for the plot
    :argument bar kind : kind of plot, one of bar, curve or sticks.
    :argument None fsize : font size for header and labels
    :argument 100 height : height of the plot (excluding labels)
    :argument None hlines : list of y values of horizontal dashed lines to be drawn across plot
    :argument None hlines_col: list of colors associated to each horizontal line
    :argument None col_width : width of a column in the alignment
    :argument red error_col : color of error bars
    """
    def __init__(self, values, errors=None, colors=None, header='',
                 fsize=9, height = 100, hlines=None, kind='bar',
                 hlines_col = None, extras=None, col_width=11,
                 ylim=None, xlabel='', ylabel=''):

        self.col_w = float(col_width)
        self.height = height
        self.values = [float(v) for v in values]
        self.width = self.col_w * len (self.values)
        self.errors = errors if errors else []
        self.colors = colors if colors else ['gray'] * len(self.values)
        self.header = header
        self.fsize = fsize
        if ylim:
            self.ylim = tuple((float(y) for y in ylim))
        else:
            self.ylim = (int(min(self.values)-0.5), int(max(self.values)+0.5))
        self.xlabel = xlabel
        self.ylabel = ylabel

        if self.errors:
            if type(self.errors[0]) is list or type(self.errors[0]) is tuple:
                self._up_err = [float(e[1]) for e in self.errors]
                self._dw_err = [float(-e[0]) for e in self.errors]
            else:
                self._up_err = [float(e) for e in self.errors]
                self._dw_err = [float(-e) for e in self.errors]
        if kind == 'bar':
            self.draw_fun = self.draw_bar
        elif kind == 'stick':
            self.draw_fun = self.draw_stick
        elif kind == 'curve':
            self.draw_fun = self.draw_curve
        else:
            raise 'kind %s not yet implemented... ;)' % (kind)

        self.hlines = [float(h) for h in hlines] if hlines else [1.0]
        self.hlines_col = hlines_col if hlines_col else ['black']*len(self.hlines)

        self.extras = extras if extras else ['']
        if len (self.extras) != len (self.values):
            self.extras = ['']

        super(SequencePlotFace, self).__init__(None)

    def update_items(self):
        self.item =  QGraphicsRectItem(-40, 0, self.width+40, self.height+50)
        self.item.setPen(QPen(QColor('white')))
        # draw lines
        for line, col in zip(self.hlines, self.hlines_col):
            self.draw_hlines(line, col)
        # draw plot
        width = self.col_w
        for i, val in enumerate(self.values):
            self.draw_fun(width * i + self.col_w / 2 , val, i)
        # draw error bars
        if self.errors:
            for i in range(len(self.errors)):
                self.draw_errors(width * i + self.col_w / 2 , i)
        # draw x axis
        self.draw_x_axis()
        # draw y axis
        self.draw_y_axis()
        # put header
        self.write_header()

    def write_header(self):
        text = QGraphicsSimpleTextItem(self.header)
        text.setFont(QFont("Arial", self.fsize))
        text.setParentItem(self.item)
        text.setPos(0, 5)

    def draw_y_axis(self):
        lineItem = QGraphicsLineItem(0, self.coordY(self.ylim[0]),
                                     0, self.coordY(self.ylim[1]),
                                     parent=self.item)
        lineItem.setPen(QPen(QColor('black')))
        lineItem.setZValue(10)
        max_w = 0
        for y in set(self.hlines + list(self.ylim)):
            lineItem = QGraphicsLineItem(0, self.coordY(y),
                                               -5, self.coordY(y),
                                               parent=self.item)
            lineItem.setPen(QPen(QColor('black')))
            lineItem.setZValue(10)
            text = QGraphicsSimpleTextItem(str(y))
            text.setFont(QFont("Arial", self.fsize-2))
            text.setParentItem(self.item)
            tw = text.boundingRect().width()
            max_w = tw if tw > max_w else max_w
            th = text.boundingRect().height()
            # Center text according to masterItem size
            text.setPos(-tw - 5, self.coordY(y)-th/2)
        if self.ylabel:
            text = QGraphicsSimpleTextItem(self.ylabel)
            text.setFont(QFont("Arial", self.fsize-1))
            text.setParentItem(self.item)
            text.setRotation(-90)
            tw = text.boundingRect().width()
            th = text.boundingRect().height()
            # Center text according to masterItem size
            text.setPos(-th -5-max_w, tw/2+self.coordY(sum(self.ylim)/2))

    def draw_x_axis(self):
        lineItem = QGraphicsLineItem(self.col_w/2,
                                           self.coordY(self.ylim[0])+2,
                                           self.width-self.col_w/2,
                                           self.coordY(self.ylim[0])+2,
                                           parent=self.item)
        lineItem.setPen(QPen(QColor('black')))
        lineItem.setZValue(10)
        all_vals = list(range(0, len(self.values), 5))
        if (len(self.values)-1)%5:
            all_vals += [len(self.values)-1]
        for x in all_vals:
            lineItem = QGraphicsLineItem(0, self.coordY(self.ylim[0])+2,
                                               0, self.coordY(self.ylim[0])+6,
                                               parent=self.item)
            lineItem.setX(x*self.col_w + self.col_w/2)
            lineItem.setPen(QPen(QColor('black')))
            lineItem.setZValue(10)
            text = QGraphicsSimpleTextItem(str(x))
            text.setFont(QFont("Arial", self.fsize-2))
            text.setParentItem(self.item)
            tw = text.boundingRect().width()
            # Center text according to masterItem size
            text.setPos(x*self.col_w-tw/2 + self.col_w/2,
                        self.coordY(self.ylim[0])+6)

    def coordY(self, y):
        """
        return the transformation of Y according to mean value
        (that is last element of lines)
        """
        y_offset = 30
        if self.ylim[1] <= y: return y_offset
        if self.ylim[1] == 0: return self.height + y_offset
        if self.ylim[0] >= y: return self.height + y_offset
        #return self.height - y * self.height / self.ylim[1]
        return self.height + y_offset - (y-self.ylim[0]) / (self.ylim[1]-self.ylim[0]) * self.height

    def draw_hlines (self, line, col):
        lineItem = QGraphicsLineItem(0, self.coordY(line),
                                           self.width, self.coordY(line),
                                           parent=self.item)
        lineItem.setPen(QPen(QColor(col), 1, Qt.DashLine))
        lineItem.setZValue(10)

    def draw_bar(self, x, y, i):
        h = self.coordY(self.ylim[0])#self.height
        coordY = self.coordY
        item = self.item
        # if value stands out of bound
        if y < self.ylim[0]: return
        if y < self.ylim[1]:
            # left line
            lineItem = QGraphicsLineItem(0, h, 0, coordY(y), parent=item)
            lineItem.setX(x-3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))
            # right line
            lineItem = QGraphicsLineItem(0, h, 0, coordY(y), parent=item)
            lineItem.setX(x+3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))
            # top line
            lineItem = QGraphicsLineItem(0, coordY(y), 6, coordY(y), parent=item)
            lineItem.setX(x-3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))
        else:
            # lower left line
            lineItem = QGraphicsLineItem(0, h, 0, coordY(y), parent=item)
            lineItem.setX(x-3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))
            # lower right line
            lineItem = QGraphicsLineItem(0, h, 0, coordY(y), parent=item)
            lineItem.setX(x+3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))
            # upper left line
            lineItem = QGraphicsLineItem(0, coordY(y)-4, 0, coordY(y)-7, parent=item)
            lineItem.setX(x-3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))
            # upper right line
            lineItem = QGraphicsLineItem(0, coordY(y)-4, 0, coordY(y)-7, parent=item)
            lineItem.setX(x+3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))
            # top line
            lineItem = QGraphicsLineItem(0, coordY(y)-7, 6, coordY(y)-7, parent=item)
            lineItem.setX(x-3)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))

    def draw_stick(self, x, y, i):
        lineItem = QGraphicsLineItem(0, self.coordY(self.ylim[0]),
                                           0, self.coordY(y),
                                           parent=self.item)
        lineItem.setX(x)
        lineItem.setPen(QPen(QColor(self.colors[i]),2))

    def draw_errors(self, x, i):
        lower = self.values[i]+self._dw_err[i]
        upper = self.values[i]+self._up_err[i]
        lineItem = QGraphicsLineItem(0, self.coordY(lower), 0,
                                           self.coordY(upper), parent=self.item)
        lineItem.setX(x)
        lineItem.setPen(QPen(QColor('black'),1))

    def draw_curve(self, x, y, i):
        # top line
        lineItem = QGraphicsLineItem(0, self.coordY(y), 4,
                                           self.coordY(y), parent=self.item)
        lineItem.setX(x-2)
        lineItem.setPen(QPen(QColor(self.colors[i]),2))
        if i > 0:
            prev = self.values[i-1] if i>0 else self.values[i]
            lineItem = QGraphicsLineItem(0, self.coordY(prev), self.col_w-4,
                                               self.coordY(y), parent=self.item)
            lineItem.setX(x - self.col_w+2)
            lineItem.setPen(QPen(QColor(self.colors[i]),2))

class SVGFace(Face):
    """Creates a node Face using an external SVG file.

    :param img_file: path to the image file.
    :param None width: if provided, image will be scaled to this width (in pixels)
    :param None height: if provided, image will be scaled to this height (in pixels)

    If only one dimension value (width or height) is provided, the other
    will be calculated to keep original aspect ratio.

    (Known limitations: The same SVGFace cannot be used in several nodes)

    .. versionadded:: 3.1
    """

    def __init__(self, img_file, width=None, height=None):
        Face.__init__(self)
        self.img_file = img_file
        self.width = float(width) if width else None
        self.height = float(height) if height else None
        self.xscale = 1.0
        self.yscale = 1.0
        self.type = "item"
        self.item = None

    def update_items(self):
        if not self.item:
            self.item = QGraphicsSvgItem(self.img_file)

            if self.width:
                self.xscale = self.width / self._width()
                if not self.height:
                    self.yscale = self.xscale
            if self.height:
                self.yscale = self.height / self._height()
                if not self.width:
                    self.xscale = self.yscale
            self.item.scale(self.xscale, self.yscale)

    def _width(self):
        return self.item.boundingRect().width() * self.xscale

    def _height(self):
        return self.item.boundingRect().height() * self.yscale

class SequenceFace(StaticItemFace, Face):
    """
    Creates a new molecular sequence face object.
    :param seq: Sequence string to be drawn
    :param seqtype: Type of sequence: "nt" or "aa"
    :param fsize: Font size, (default=10)

    You can set custom colors for amino-acids or nucleotides:

    :param None codon: a string that corresponds to the reverse
      translation of the amino-acid sequence
    :param None col_w: width of the column (if col_w is lower than
      font size, letter wont be displayed)
    :param None fg_colors: dictionary of colors for foreground, with
      as keys each possible character in sequences, and as value the
      colors
    :param None bg_colors: dictionary of colors for background, with
      as keys each possible character in sequences, and as value the
      colors
    :param 3 alt_col_w: works together with special_col option,
      defines the width of given columns
    :param None special_col: list of lists containing the bounds
      of columns to be displayed with alt_col_w as width
    :param False interactive: more info can be displayed when
      mouse over sequence

        """
    def __init__(self, seq, seqtype="aa", fsize=10,
                 fg_colors=None, bg_colors=None,
                 codon=None, col_w=None, alt_col_w=3,
                 special_col=None, interactive=False):
        self.seq = seq
        self.codon = codon
        self.fsize = fsize
        self.style = seqtype
        self.col_w = float(self.fsize + 1) if col_w is None else float(col_w)
        self.alt_col_w = float(alt_col_w)
        self.special_col = special_col if special_col else []
        self.width = 0 # will store the width of the whole sequence
        self.interact = interactive

        if self.style == "aa":
            if not fg_colors:
                fg_colors = _aafgcolors
            if not bg_colors:
                bg_colors = _aabgcolors
        else:
            if not fg_colors:
                fg_colors = _ntfgcolors
            if not bg_colors:
                bg_colors = _ntbgcolors

        def __init_col(color_dic):
            """to speed up the drawing of colored rectangles and characters"""
            new_color_dic = {}
            for car in color_dic:
                new_color_dic[car] = QBrush(QColor(color_dic[car]))
            return new_color_dic

        self.fg_col = __init_col(fg_colors)
        self.bg_col = __init_col(bg_colors)

        # for future?
        self.row_h = 13.0
        super(SequenceFace, self).__init__(None)


    def update_items(self):
        self.item = QGraphicsRectItem(0, 0, self.width, self.row_h)
        seq_width = 0
        nopen = QPen(Qt.NoPen)
        font = QFont("Courier", self.fsize)
        rect_cls = self.InteractiveLetterItem if self.interact \
                   else QGraphicsRectItem
        for i, letter in enumerate(self.seq):
            letter = letter.upper()
            width = self.col_w
            for reg in self.special_col:
                if reg[0] < i <= reg[1]:
                    width = self.alt_col_w
                    break
            #load interactive item if called correspondingly
            rectitem = rect_cls(0, 0, width, self.row_h, parent=self.item)
            rectitem.setX(seq_width) # to give correct X to children item
            rectitem.setBrush(self.bg_col[letter])
            rectitem.setPen(nopen)
            if self.interact:
                if self.codon:
                    rectitem.codon = '%s, %d: %s' % (self.seq[i], i,
                                                     self.codon[i*3:i*3+3])
                else:
                    rectitem.codon = '%s, %d' % (self.seq[i], i)
            # write letter if enough space
            if width >= self.fsize:
                text = QGraphicsSimpleTextItem(letter, parent=rectitem)
                text.setFont(font)
                text.setBrush(self.fg_col[letter])
                # Center text according to rectitem size
                txtw = text.boundingRect().width()
                txth = text.boundingRect().height()
                text.setPos((width - txtw)/2, (self.row_h - txth)/2)
            seq_width += width
        self.width = seq_width

    class InteractiveLetterItem(QGraphicsRectItem):
        """This is a class"""
        def __init__(self, *arg, **karg):
            QGraphicsRectItem.__init__(self, *arg, **karg)
            self.codon = None
            self.label = None
            self.setAcceptHoverEvents(True)

        def hoverEnterEvent (self, e):
            if not self.label:
                self.label = QGraphicsRectItem(parent=self)
                #self.label.setY(-18)
                self.label.setX(11)
                self.label.setBrush(QBrush(QColor("white")))
                self.label.text = QGraphicsSimpleTextItem(parent=self.label)

            self.setZValue(1)
            self.label.text.setText(self.codon)
            self.label.setRect(self.label.text.boundingRect())
            self.label.setVisible(True)

        def hoverLeaveEvent(self, e):
            """when mouse leaves area"""
            if self.label:
                self.label.setVisible(False)
                self.setZValue(0)

class _DiamondItem(QGraphicsPolygonItem):
    def __init__(self, width, height, label, color='#0000FF'):

        self.pol = QPolygonF()

        self.pol = QPolygonF()
        self.pol.append(QPointF(width / 2.0, 0))
        self.pol.append(QPointF(width, height / 2.0))
        self.pol.append(QPointF(width / 2.0, height))
        self.pol.append(QPointF(0, height / 2.0))
        self.pol.append(QPointF(width / 2.0, 0))

        self.label = label
        QGraphicsPolygonItem.__init__(self, self.pol)

        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor(color)))

    def paint(self, p, option, widget):
        super(_DiamondItem, self).paint(p, option, widget)
        _label_painter(self, p, option, widget)


class DiamondFace(StaticItemFace, Face):
    """
    Creates a collapsed node face object.
    """
    def __init__(self, width, height, label='', color='#0000FF'):
        # TODO: It would be great if this object could be automatically
        # resized to approximate the dimensions of the subtree.
        # One way around this is to scale the height by the number of tips
        # in the subtree (i.e. `len(node)`) and the width by the
        # maximum height of the subtree (i.e. node.get_farthest_node()).
        Face.__init__(self)
        self.height = height
        self.width = width
        self.type = 'item'
        self.label = label
        self.color = color

    def update_items(self):
        self.item = _DiamondItem(width=self.width, height=self.height,
                                 label=self.label, color=self.color)

    def _width(self):
        return self.width

    def _height(self):
        return self.height


class ArrowFace(Face):

    """

    Creates a color-stripped arrow representation for synteny visualization

    :param width: width of the arrow (min of 10)
    :param height: height of arrow (min of 10)
    :param strand: defines gene orientation. "-" entails left-oriented arrows
                   while "+" strand right-oriented arrows.
    :param colors: array containing values to color stripes

    """

    def __init__(self, width, height, strand, colors):
        Face.__init__(self)
        self.width = width
        self.height = height
        self.strand = strand
        self.colors = colors

    def _width(self):
        return self.width

    def _height(self):
        return self.height

    def update_items(self):
        return

    def update_pixmap(self):
        # Create pixmap
        self.pixmap = QPixmap(self.width, self.height)
        self.pixmap.fill(QColor("white"))
        p = QPainter(self.pixmap)

        # Create pen
        solidPen = QPen(QBrush(QColor("black")), 0)
        solidPen.setStyle(Qt.SolidLine)
        p.setPen(solidPen)

        # Define bands width and arrow height taking padding into account
        rect_w = (self.width - 10) / len(self.colors)
        rect_h = self.height - 10

        # Draw each of the color bands and the arrow pointer depending on the
        # strand (+,right/-,left)
        for i, color in enumerate(self.colors):
            if self.strand == "+":
                p.fillRect(3 + i*rect_w, 5, math.ceil(rect_w), rect_h, QColor(color))
                if i == (len(self.colors) - 1):
                    path = QPainterPath()
                    path.moveTo(3+(i+1)*rect_w, 5)
                    path.lineTo(7+(i+1)*rect_w, 5+rect_h / 2)
                    path.lineTo(3+(i+1)*rect_w, 5+rect_h)
                    p.fillPath(path, QColor(color))
            elif self.strand == "-":
                p.fillRect(7 + i*rect_w, 5, math.ceil(rect_w), rect_h, QColor(color))
                if i == 0:
                    path = QPainterPath()
                    path.moveTo(7, 5)
                    path.lineTo(3, 5+rect_h / 2)
                    path.lineTo(7, 5+rect_h)
                    p.fillPath(path, QColor(color))
