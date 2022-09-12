import json
from pathlib import Path

from ..treelayout import TreeLayout
from ..faces import SeqMotifFace
from ..draw_helpers import Padding


with open(Path(__file__).parent / "pfam2color.json") as handle:
    _pfam2color = json.load(handle)

with open(Path(__file__).parent / "smart2color.json") as handle:
    _smart2color = json.load(handle)


class LayoutPfamDomains(TreeLayout):
    def __init__(self, prop="pfam",
            column=10, colormap=colormap,
            min_fsize=4, max_fsize=15,
            padding_x=5, padding_y=0):
        super().__init__("Pfam domains")
        self.prop = prop
        self.column = column
        self.aligned_faces = True
        self.colormap = colormap
        self.min_fsize = min_fsize
        self.max_fsize = max_fsize
        self.padding = Padding(padding_x, padding_y)


    def get_doms(self, node):
        if node.is_leaf():
            dom_arq = node.props.get(self.prop)
            return dom_arq
        else:
            first_node = next(node.iter_leaves())
            return first_node.props.get(self.prop)

    def parse_doms(self, dom_list):
        doms = []
        for name, start, end in dom_list:
            color = self.colormap.get(name, "lightgray")
            dom = [int(start), int(end), "()", 
                   None, None, color, color,
                   "arial|20|black|%s" %(name)]
            doms.append(dom)
        return doms

    def set_node_style(self, node):
        dom_list = self.get_doms(node)
        if dom_list:
            doms = self.parse_doms(dom_list)
            fake_seq = '-' * int(node.props.get('len_alg'))
            seqFace = SeqMotifFace(seq=fake_seq, motifs=doms, width=500)
            node.add_face(seqFace, column=self.column, 
                    position="aligned",
                    collapsed_only=(not node.is_leaf()))


def create_domain_layout(prop, name, column):
    # branch_right; column 2; color black
    class Layout(_LayoutDomains):
        def __init__(self, 
                prop=prop, 
                name=name,
                column=column,
                *args, **kwargs):
            super().__init__(
                    prop=prop, 
                    name=name,
                    column=column,
                    *args, **kwargs)
        def __name__(self):
            return layout_name
    layout_name = "Layout" + TitleCase(name)
    Layout.__name__ = layout_name
    globals()[layout_name] = Layout
    return Layout


domain_layout_args = [ 
        [ "pfam",  "Pfam domain",  _pfam2color  ],
        [ "smart", "Smart domain", _smart2color ],
    ]

col0 = 20
domain_layouts = [ create_domain_layout(*args, i+col0)\
                 for i, args in enumerate(domain_layout_args) ]

__all__ = [ *[layout.__name__ for layout in domain_layouts],
            "LayoutEvolEvents", "LayoutLastCommonAncestor",
            "LayoutPfamDomains", ]
