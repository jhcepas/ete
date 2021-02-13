import random
from ... import Tree, TreeStyle, NodeStyle, faces, AttrFace, TreeFace, TextFace

# Tree Style used to render small trees used as leaf faces
small_ts = TreeStyle()
small_ts.show_leaf_name = True
small_ts.scale = 10

def get_example_tree():
    # Random tree
    t = Tree()
    t.populate(20, random_branches=True)

    # Some random features in all nodes
    for n in t.traverse():
        n.add_features(weight=random.randint(0, 50))

    # Create an empty TreeStyle
    ts = TreeStyle()

    # Draw a tree
    ts.mode = "r"

    # We will add node names manually
    ts.show_leaf_name = False
    # Show branch data
    ts.show_branch_length = True
    ts.show_branch_support = True
    ts.show_scale = False
    return t, ts

if __name__ == "__main__":
    t1, ts1 = get_example_tree()
    ts1.legend.add_face(TextFace("Tree 1"), column=0)
    ts1.legend_position = 1
    ts1.margin_bottom = 40
    ts1.margin_right = 100

    t2, ts2 = get_example_tree()
    ts2.legend.add_face(TextFace("Tree 2"), column=0)
    ts2.legend_position = 2
    ts2.margin_bottom = 40
    
    t3, ts3 = get_example_tree()
    ts3.legend.add_face(TextFace("Tree 3"), column=0)
    ts3.legend_position = 3

    
    t4, ts4 = get_example_tree()
    ts4.legend.add_face(TextFace("Tree 4"), column=0)
    ts4.legend_position = 4
    
    # Trying to reproduce this
    #
    #  t1  |  t2  
    #______|______
    #      |
    #  t3  |  t4  
    #
    
    # The order in which the faces are added matter here

    # add t2 to the right of t1
    ts1.aligned_treeface_hz.add_face(TreeFace(t2, ts2), column=0)
    # add t3 below t1
    ts1.aligned_treeface_vt.add_face(TreeFace(t3, ts3), column=0)
    # add t4 below t2
    ts2.aligned_treeface_vt.add_face(TreeFace(t4, ts4), column=0)
    
    t1.show(tree_style=ts1)


