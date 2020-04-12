from __future__ import absolute_import
from __future__ import print_function
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


from .. import numpy
from . import faces

def basic(node):
    if node.is_leaf():
        #node.img_style["size"]=1
        #node.img_style["shape"] = "circle"
        faces.add_face_to_node(faces.AttrFace("name", fstyle="Arial", fsize=10,
                                              fgcolor="#4f8f0f", penwidth=None), node, 0 )

def phylogeny(node):
    leaf_color = "#000000"
    node.img_style["shape"] = "circle"
    if hasattr(node,"evoltype"):
        if node.evoltype == 'D':
            node.img_style["fgcolor"] = "#FF0000"
            node.img_style["hz_line_color"] = "#FF0000"
            node.img_style["vt_line_color"] = "#FF0000"
        elif node.evoltype == 'S':
            node.img_style["fgcolor"] = "#1d176e"
            node.img_style["hz_line_color"] = "#1d176e"
            node.img_style["vt_line_color"] = "#1d176e"
        elif node.evoltype == 'L':
            node.img_style["fgcolor"] = "#777777"
            node.img_style["vt_line_color"] = "#777777"
            node.img_style["hz_line_color"] = "#777777"
            node.img_style["hz_line_type"] = 1
            node.img_style["vt_line_type"] = 1
            leaf_color = "#777777"

    if node.is_leaf():
        node.img_style["shape"] = "square"
        node.img_style["size"] = 4
        node.img_style["fgcolor"] = leaf_color
        faces.add_face_to_node( faces.AttrFace("name", ftype="Arial", fsize=11,
                                               fgcolor=leaf_color, penwidth=None), node, 0 )
        if hasattr(node,"sequence"):
            SequenceFace =  faces.SequenceFace(node.sequence,"aa",13)
            faces.add_face_to_node(SequenceFace, node, 1, aligned=True)
    else:
        node.img_style["size"] = 6

def heatmap(node):
    square_size = 10
    # Extras node info
    node.collapsed = False

    # Color and style
    node.img_style["fgcolor"] = "#3333FF"
    node.img_style["size"] =  0

    ncols = node.arraytable.matrix.shape[1]

    matrix_max = numpy.max(node.arraytable._matrix_max)
    matrix_min = numpy.min(node.arraytable._matrix_min)
    
    matrix_avg = matrix_min+((matrix_max-matrix_min)/2)

    ProfileFace = faces.ProfileFace(\
      matrix_max,\
        matrix_min,\
        matrix_avg,\
        square_size*ncols,\
        square_size,\
        "heatmap")
    ProfileFace.ymargin=0
    if node.is_leaf():
        # Set colors
        faces.add_face_to_node(ProfileFace, node, 0, aligned=True)

def cluster_cbars(node):
    # Extras node info
    node.collapsed = False
    # Color and style
    node.img_style["fgcolor"] = "#3333FF"
    node.img_style["size"] =  4
    matrix_max = numpy.max(node.arraytable._matrix_max)
    matrix_min = numpy.min(node.arraytable._matrix_min)
    matrix_avg = matrix_min+((matrix_max-matrix_min)/2)
    ProfileFace = faces.ProfileFace(\
                                        matrix_max,\
                                        matrix_min,\
                                        matrix_avg,\
                                        200,\
                                        60,\
                                        "cbars")

    if node.is_leaf():
        nameFace = faces.AttrFace("name",fsize=6 )
        faces.add_face_to_node(nameFace, node, 1, aligned=True )
        faces.add_face_to_node(ProfileFace, node, 0,  aligned=True )
    else:
        # Set custom faces
        faces.add_face_to_node(ProfileFace, node, 0, aligned=True )

def cluster_lines(node):
    # Extras node info
    node.collapsed = False
    # Color and style
    node.img_style["fgcolor"] = "#3333FF"
    node.img_style["size"] = 4
    matrix_max = numpy.max(node.arraytable._matrix_max)
    matrix_min = numpy.min(node.arraytable._matrix_min)
    matrix_avg = matrix_min+((matrix_max-matrix_min)/2)
    ProfileFace = faces.ProfileFace(\
      matrix_max,\
        matrix_min,\
        matrix_avg,\
        200,\
        50,\
        "lines")

    if node.is_leaf():
        nameFace = faces.AttrFace("name",fsize=6 )
        faces.add_face_to_node(nameFace, node, 1,  aligned=True )
        faces.add_face_to_node(ProfileFace, node, 0, aligned=True )
    else:
        # Set custom faces
        faces.add_face_to_node(ProfileFace, node, 0, aligned=True )

def cluster_bars(node):
    # Extras node info
    node.collapsed = False
    # Color and style
    node.img_style["fgcolor"] = "#3333FF"
    node.img_style["size"] = 4

    if node.is_leaf():
        matrix_max = numpy.max(node.arraytable._matrix_max)
        matrix_min = numpy.min(node.arraytable._matrix_min)
        matrix_avg = matrix_min+((matrix_max-matrix_min)/2)
        ProfileFace = faces.ProfileFace(\
          matrix_max,\
            matrix_min,\
            matrix_avg,\
            200,\
            40,\
            "bars")
        nameFace = faces.AttrFace("name",fsize=6 )
        faces.add_face_to_node(nameFace, node, 1, aligned=True )
        faces.add_face_to_node(ProfileFace, node, 0, aligned=True )

def large(node):
    # Color and style
    node.img_style["fgcolor"] = "#3333FF"
    node.img_style["size"] = 0


def evol_layout(node):
    '''
    layout for CodemlTree
    '''
    if hasattr(node, "collapsed"):
        if node.collapsed == 1:
            node.img_style["draw_descendants"]= False
    leaf_color = "#000000"
    if not node.is_root() and 'w' in node.features:
        node.img_style["shape"] = 'circle'
        if (node.w > 900):
            node._w = 3
        elif (node.w > 100):
            node._w = 2.5
        elif (node.w > 10) :
            node._w = 2
        elif (node.w > 1):
            node._w = 1.5
        else:
            node._w = node.w
        node.img_style["size"] = int ((float(node._w))*6+2)
        if node._w == 3   :
            node.img_style["fgcolor"] = "#c10000"
        if node._w == 2.5 :
            node.img_style["fgcolor"] = "#FF5A02"
        if node._w == 2   :
            node.img_style["fgcolor"] = "#FFA200"
        if node._w == 1.5 :
            node.img_style["fgcolor"] = "#E9BF00"
        if node._w  < 0.2 :
            node.img_style["fgcolor"] = "#000000"
    if hasattr(node,"extras"):
        faces.add_face_to_node( faces.AttrFace("extras", fstyle="Arial", fsize=7, \
                                               fgcolor="#000000", penwidth=None), node, 2 )
    #if node.is_leaf():
    if hasattr (node, "sequence"):
        seqface =  faces.SequenceFace(node.sequence, interactive=True,
                                      codon=node.nt_sequence)
        faces.add_face_to_node(seqface, node, 1, aligned=True)


def evol_clean_layout(node):
    '''
    layout for CodemlTree
    '''
    if hasattr(node, "collapsed"):
        if node.collapsed == 1:
            node.img_style["draw_descendants"]= False
    leaf_color = "#000000"
    node.img_style["size"] = 2
    if node.is_leaf():
        # if hasattr (node,"highlight"):
        #     faces.add_face_to_node(faces.AttrFace("name", "Arial", fsize=9,
        #                                           fgcolor=node.highlight, penwidth=None), \
        #                            node, 0 )
        #else:
        #    leaface = faces.AttrFace("name", fstyle="Arial", fsize=9,\
        #       fgcolor=leaf_color, penwidth=None)
        #    leaface.margin_right = 10
        #    faces.add_face_to_node (leaface, node, 0)
        if hasattr (node, "sequence"):
            seqface =  faces.SequenceFace(node.sequence, interactive=True,
                                          codon=node.nt_sequence)
            faces.add_face_to_node(seqface, node, 1, aligned=True)
    if hasattr(node, 'dN'):
        faces.add_face_to_node (faces.TextFace('%.4f'%(node.w), fsize=6,
                                               fgcolor="#7D2D2D"),
                                node, 0, position="branch-top")
        faces.add_face_to_node (faces.TextFace('%.2f/%.2f'% (100*node.dN,
                                                             100*node.dS),
                                              fsize=6, fgcolor="#787878"),
                                node, 0, position="branch-bottom")
    if hasattr(node,"extras"):
        faces.add_face_to_node( faces.AttrFace("extras", fstyle="Arial", fsize=7, \
                                               fgcolor="#000000", penwidth=None), node, 2 )
