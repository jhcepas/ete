from __future__ import absolute_import
from __future__ import print_function
import unittest
import random
import itertools
import json

import sys
from six.moves import range

from .. import Tree, PhyloTree, TreeNode
from ..coretype.tree import TreeError
from ..parser.newick import NewickError
from .datasets import *

class Test_Coretype_Tree(unittest.TestCase):
    """ Tests tree basics. """
    def test_read_write_exceptions(self):

        def wrong_dist():
            t = Tree()
            t.dist = '1a'

        def wrong_support():
            t = Tree()
            t.support = '1a'

        def wrong_up():
            t = Tree()
            t.up = 'Something'

        def wrong_children():
            t = Tree()
            t.children = 'Something'

        self.assertRaises(TreeError, wrong_dist)
        self.assertRaises(TreeError, wrong_support)
        self.assertRaises(TreeError, wrong_up)
        self.assertRaises(TreeError, wrong_children)

    def test_add_remove_features(self):
        #The features concept will probably change in future versions. It is
        #very inefficient in larg trees.
        t = Tree()
        t.add_features(testf1=1, testf2="1", testf3=[1])
        t.add_feature('testf4', set([1]))
        self.assertEqual(t.testf1, 1)
        self.assertEqual(t.testf2, "1")
        self.assertEqual(t.testf3, [1])
        self.assertEqual(t.testf4, set([1]))

        t.del_feature('testf4')
        self.assertTrue('testf4' not in t.features)

    def test_tree_read_and_write(self):
        """ Tests newick support """
        # Read and write newick tree from file (and support for NHX
        # format): newick parser
        with open("/tmp/etetemptree.nw","w") as OUT:
            OUT.write(nw_full)

        t = Tree("/tmp/etetemptree.nw")
        t.write(outfile='/tmp/etewritetest.nw')
        self.assertEqual(nw_full, t.write(features=["flag","mood"]))
        self.assertEqual(nw_topo,  t.write(format=9))
        self.assertEqual(nw_dist, t.write(format=5))

        # Read and write newick tree from *string* (and support for NHX
        # format)
        t = Tree(nw_full)
        self.assertEqual(nw_full, t.write(features=["flag","mood"]))
        self.assertEqual(nw_topo, t.write(format=9))
        self.assertEqual( nw_dist, t.write(format=5))

        # Read complex newick
        t = Tree(nw2_full)
        self.assertEqual(nw2_full,  t.write())

        # Read wierd topologies
        t = Tree(nw_simple5)
        self.assertEqual(nw_simple5,  t.write(format=9))
        t = Tree(nw_simple6)
        self.assertEqual(nw_simple6,  t.write(format=9))

        #Read single node trees:
        self.assertEqual(Tree("hola;").write(format=9),  "hola;")
        self.assertEqual(Tree("(hola);").write(format=9),  "(hola);")

        #Test export root features
        t = Tree("(((A[&&NHX:name=A],B[&&NHX:name=B])[&&NHX:name=NoName],C[&&NHX:name=C])[&&NHX:name=I],(D[&&NHX:name=D],F[&&NHX:name=F])[&&NHX:name=J])[&&NHX:name=root];")
        #print t.get_ascii()
        self.assertEqual(t.write(format=9, features=["name"], format_root_node=True),
                         "(((A[&&NHX:name=A],B[&&NHX:name=B])[&&NHX:name=NoName],C[&&NHX:name=C])[&&NHX:name=I],(D[&&NHX:name=D],F[&&NHX:name=F])[&&NHX:name=J])[&&NHX:name=root];")

        #Test exporting ordered features
        t = Tree("((A,B),C);")
        expected_nw = "((A:1[&&NHX:dist=1.0:name=A:support=1.0],B:1[&&NHX:0=0:1=1:2=2:3=3:4=4:5=5:6=6:7=7:8=8:9=9:a=a:b=b:c=c:d=d:dist=1.0:e=e:f=f:g=g:h=h:i=i:j=j:k=k:l=l:m=m:n=n:name=B:o=o:p=p:q=q:r=r:s=s:support=1.0:t=t:u=u:v=v:w=w])1:1[&&NHX:dist=1.0:name=:support=1.0],C:1[&&NHX:dist=1.0:name=C:support=1.0]);"
        features = list("abcdefghijklmnopqrstuvw0123456789")
        random.shuffle(features)
        for letter in features:
            (t & "B").add_feature(letter, letter)
        self.assertEqual(expected_nw, t.write(features=[]))

        # Node instance repr
        self.assertTrue(Tree().__repr__().startswith('Tree node'))

    def test_concat_trees(self):
        t1 = Tree('((A, B), C);')
        t2 = Tree('((a, b), c);')
        concat_tree = t1 + t2
        concat_tree.sort_descendants()
        self.assertEqual(concat_tree.write(format=9), '(((A,B),C),((a,b),c));')
        t3 = PhyloTree('((a, b), c);')
        mixed_types = lambda: t1 + t3
        self.assertRaises(TreeError, mixed_types)


    def test_newick_formats(self):
        """ tests different newick subformats """
        from ..parser.newick import print_supported_formats, NW_FORMAT
        print_supported_formats()

        # Let's stress a bit
        for i in range(10):
            t = Tree()
            t.populate(4, random_branches=True)
            for f in NW_FORMAT:
                self.assertEqual(t.write(format=f), Tree(t.write(format=f),format=f).write(format=f))

        # Format 0 = ((H:1,(G:1,F:1)1:1)1:1,I:1)1:1;
        # Format 1 = ((H:1,(G:1,F:1):1):1,I:1):1;
        # Format 2 = ((H:1,(G:1,F:1)1:1)1:1,I:1)1:1;
        # Format 3 = ((H:1,(G:1,F:1)NoName:1)NoName:1,I:1)NoName:1;
        # Format 4 = ((H:1,(G:1,F:1)),I:1);
        # Format 5 = ((H:1,(G:1,F:1):1):1,I:1):1;
        # Format 6 = ((H,(G,F):1):1,I):1;
        # Format 7 = ((H:1,(G:1,F:1)NoName)NoName,I:1)NoName;
        # Format 8 = ((H,(G,F)NoName)NoName,I)NoName;
        # Format 9 = ((H,(G,F)),I);
        # Format 100 = ((,(,)),);

        t = Tree()
        t.populate(50, random_branches=True)
        t.sort_descendants()
        expected_distances = [round(x, 6) for x in [n.dist for n in t.traverse('postorder')]]
        expected_leaf_distances = [round(x, 6) for x in [n.dist for n in t]]
        expected_internal_distances = [round(x, 6) for x in [n.dist for n in t.traverse('postorder') if not n.is_leaf()]]
        expected_supports = [round(x, 6) for x in [n.support for n in t.traverse('postorder') if not n.is_leaf()]]
        expected_leaf_names = [n.name for n in t]

        # Check that all formats read names correctly
        for f in [0,1,2,3,5,6,7,8,9]:
            t2 = Tree(t.write(format=f, dist_formatter="%0.6f", support_formatter="%0.6f", format_root_node=True), format=f)
            t2.sort_descendants()
            observed_names = [n.name for n in t]
            self.assertEqual(observed_names, expected_leaf_names)

        # Check that all formats reading distances, recover original distances
        for f in [0,1,2,3,5]:
            t2 = Tree(t.write(format=f, dist_formatter="%0.6f", support_formatter="%0.6f", format_root_node=True), format=f)
            t2.sort_descendants()
            observed_distances = [round(x, 6) for x in [n.dist for n in t2.traverse('postorder')]]
            self.assertEqual(observed_distances, expected_distances)

        # formats reading only leaf distances
        for f in [4,7]:
            t2 = Tree(t.write(format=f, dist_formatter="%0.6f", support_formatter="%0.6f", format_root_node=True), format=f)
            t2.sort_descendants()
            observed_distances = [round(x, 6) for x in [n.dist for n in t2]]
            self.assertEqual(observed_distances, expected_leaf_distances)

        # formats reading only leaf distances
        for f in [6]:
            t2 = Tree(t.write(format=f, dist_formatter="%0.6f", support_formatter="%0.6f", format_root_node=True), format=f)
            t2.sort_descendants()
            observed_distances = [round(x, 6) for x in [n.dist for n in t2.traverse('postorder') if not n.is_leaf()]]
            self.assertEqual(observed_distances, expected_internal_distances)


        # Check that all formats reading supports, recover original distances
        #print t.get_ascii(attributes=["support"])
        for f in [0,2]:
            t2 = Tree(t.write(format=f, dist_formatter="%0.6f", support_formatter="%0.6f", format_root_node=True), format=f)
            t2.sort_descendants()
            observed_supports = [round(x, 6) for x in [n.support for n in t2.traverse('postorder') if not n.is_leaf()]]
            self.assertEqual(observed_supports, expected_supports)


       # Check that formats reading supports, do not accept node names
        for f in [0,2]:
            # format 3 forces dumping internal node names, NoName in case is missing
            self.assertRaises(Exception, Tree, t.write(format=3), format=f)

       # Check that formats reading names, do not load supports
        for f in [1, 3]:
            # format 3 forces dumping internal node names, NoName in case is missing
            t2 = Tree(t.write(format=0), format=f)
            default_supports = set([n.support for n in t2.traverse()])
            self.assertEqual(set([1.0]), default_supports)


        # Check errors reading numbers
        error_nw1 = "((A:0.813705,(E:0.545591,D:0.411772)error:0.137245)1.000000:0.976306,C:0.074268);"
        for f in [0, 2]:
            self.assertRaises(NewickError, Tree, error_nw1, format=f)

        error_nw2 = "((A:0.813705,(E:0.545error,D:0.411772)1.0:0.137245)1.000000:0.976306,C:0.074268);"
        for f in [0, 1, 2]:
            self.assertRaises(NewickError, Tree, error_nw2, format=f)


        error_nw3 = "((A:0.813705,(E:0.545error,D:0.411772)1.0:0.137245)1.000000:0.976306,C:0.074268);"
        for f in [0, 1, 2]:
            self.assertRaises(NewickError, Tree, error_nw2, format=f)

        # Check errors derived from reading names with weird or illegal chars
        base_nw = "((NAME1:0.813705,(NAME2:0.545,NAME3:0.411772)NAME6:0.137245)NAME5:0.976306,NAME4:0.074268);"
        valid_names = ['[name]', '[name', '"name"', "'name'", "'name", 'name', '[]\'"&%$!*.']
        error_names = ['error)', '(error', "erro()r",  ":error", "error:", "err:or", ",error", "error,"]
        for ename in error_names:
            #print ename, base_nw.replace('NAME2', ename)
            self.assertRaises(NewickError, Tree, base_nw.replace('NAME2', ename), format=1)
            if not ename.startswith(','):
                #print ename, base_nw.replace('NAME6', ename)
                self.assertRaises(NewickError, Tree, base_nw.replace('NAME6', ename), format=1)

        for vname in valid_names:
            expected_names = set(['NAME1', vname, 'NAME3', 'NAME4'])
            #print set([n.name for n in Tree(base_nw.replace('NAME2', vname), format=1)])
            self.assertEqual(set([n.name for n in Tree(base_nw.replace('NAME2', vname), format=1)]),
                             expected_names)

        # invalid NHX format
        self.assertRaises(NewickError, Tree, "(((A, B), C)[&&NHX:nameI]);")
        # unsupported newick stream
        self.assertRaises(NewickError, Tree, [1,2,3])

    def test_quoted_names(self):
        complex_name = "((A:0.0001[&&NHX:hello=true],B:0.011)90:0.01[&&NHX:hello=true],(C:0.01, D:0.001)hello:0.01);"
        # A quoted tree within a tree
        nw1 = '(("A:0.1":1,"%s":2)"C:0.00":3,"D":4);' %complex_name
        #escaped quotes
        nw2 = '''(("A:\\"0.1\\"":1,"%s":2)"C:'0.00'":3,"D'sd''\'":4);''' %complex_name
        for nw in [nw1, nw2]:
            self.assertRaises(NewickError, Tree, newick=nw)
            self.assertRaises(NewickError, Tree, newick=nw, quoted_node_names=True, format=0)
            t = Tree(newick=nw, format=1, quoted_node_names=True)
            self.assertTrue(any(n for n in t if n.name == '%s'%complex_name))
            # test writing and reloading tree
            nw_back = t.write(quoted_node_names=True, format=1)
            t2 = Tree(newick=nw, format=1, quoted_node_names=True)
            nw_back2 = t2.write(quoted_node_names=True, format=1)
            self.assertEqual(nw, nw_back)
            self.assertEqual(nw, nw_back2)

    def test_custom_formatting_formats(self):
        """ test to change dist, name and support formatters """
        t = Tree('((A:1.111111, B:2.222222)C:3.33333, D:4.44444);', format=1)
        t.sort_descendants()

        check = [[0, '((TEST-A:1.1,TEST-B:2.2)SUP-1.0:3.3,TEST-D:4.4);'],
                 [1, '((TEST-A:1.1,TEST-B:2.2)TEST-C:3.3,TEST-D:4.4);'],
                 [2, '((TEST-A:1.1,TEST-B:2.2)SUP-1.0:3.3,TEST-D:4.4);'],
                 [3, '((TEST-A:1.1,TEST-B:2.2)TEST-C:3.3,TEST-D:4.4);'],
                 [4, '((TEST-A:1.1,TEST-B:2.2),TEST-D:4.4);'],
                 [5, '((TEST-A:1.1,TEST-B:2.2):3.3,TEST-D:4.4);'],
                 [6, '((TEST-A,TEST-B):3.3,TEST-D);'],
                 [7, '((TEST-A:1.1,TEST-B:2.2)TEST-C,TEST-D:4.4);'],
                 [8, '((TEST-A,TEST-B)TEST-C,TEST-D);'],
                 [9, '((TEST-A,TEST-B),TEST-D);']]

        for f, result in check:
            nw = t.write(format=f, dist_formatter="%0.1f", name_formatter="TEST-%s", support_formatter="SUP-%0.1f")
            self.assertEqual(nw, result)

    def test_tree_manipulation(self):
        """ tests operations which modify tree topology """
        nw_tree = "((Hola:1,Turtle:1.3)1:1,(A:0.3,B:2.4)1:0.43);"

        # Manipulate Topologies
        # Adding and removing nodes (add_child, remove_child,
        # add_sister, remove_sister). The resulting newick tree should
        # match the nw_tree defined before.
        t = Tree()

        remove_child_except = lambda: t.remove_child(t)
        add_sister_except = lambda: t.add_sister()
        self.assertRaises(TreeError, remove_child_except)
        self.assertRaises(TreeError, add_sister_except)


        c1 = t.add_child(dist=1, support=1)
        c2 = t.add_child(dist=0.43, support=1)
        n = TreeNode(name="Hola", dist=1, support=1)
        _n = c1.add_child(n)
        c3 = _n.add_sister(name="Turtle", dist="1.3")
        c4 = c2.add_child(name="A", dist="0.3")

        c5 = c2.add_child(name="todelete")
        _c5 = c2.remove_child(c5)

        c6 = c2.add_child(name="todelete")
        _c6 = c4.remove_sister()

        c7 = c2.add_child(name="B", dist=2.4)

        self.assertEqual(nw_tree, t.write())
        self.assertEqual(_c5, c5)
        self.assertEqual(_c6, c6)
        self.assertEqual(_n, n)

        # Delete,
        t = Tree("(((A, B), C)[&&NHX:name=I], (D, F)[&&NHX:name=J])[&&NHX:name=root];")
        D = t.search_nodes(name="D")[0]
        F = t.search_nodes(name="F")[0]
        J = t.search_nodes(name="J")[0]
        root = t.search_nodes(name="root")[0]
        J.delete()
        self.assertEqual(J.up, None)
        self.assertEqual(J in t, False)
        self.assertEqual(D.up, root)
        self.assertEqual(F.up, root)

        # Delete preventing non dicotomic
        t = Tree('((((A:1,B:1):1,C:1):1,D:1):1,E:1);')
        orig_dist = t.get_distance('A')
        C = t&('C')
        C.delete(preserve_branch_length=True)
        self.assertEqual(orig_dist, t.get_distance('A'))

        t = Tree('((((A:1,B:1):1,C:1):1,D:1):1,E:1);')
        orig_dist = t.get_distance('A')
        C = t&('C')
        C.delete(preserve_branch_length=False)
        self.assertEqual(orig_dist, t.get_distance('A')+1)

        t = Tree('((((A:1,B:1):1,C:1):1,D:1):1,E:1);')
        orig_dist = t.get_distance('A')
        C = t&('C')
        C.delete(prevent_nondicotomic=False)
        self.assertEqual(orig_dist, t.get_distance('A'))

        #detach
        t = Tree("(((A, B)[&&NHX:name=H], C)[&&NHX:name=I], (D, F)[&&NHX:name=J])[&&NHX:name=root];")
        D = t.search_nodes(name="D")[0]
        F = t.search_nodes(name="F")[0]
        J = t.search_nodes(name="J")[0]
        root = t.search_nodes(name="root")[0]
        J.detach()
        self.assertEqual(J.up, None)
        self.assertEqual(J in t, False)
        self.assertEqual(set([n.name for n in t.iter_descendants()]),set(["A","B","C","I","H"]))

        # sorting branches
        t1 = Tree('((A,B),(C,D,E,F), (G,H,I));')
        t1.ladderize()
        self.assertEqual(t1.get_leaf_names(), [_ for _ in 'ABGHICDEF'])
        t1.ladderize(direction=1)
        self.assertEqual(t1.get_leaf_names(), [_ for _ in 'FEDCIHGBA'])
        t1.sort_descendants()
        self.assertEqual(t1.get_leaf_names(), [_ for _ in 'ABCDEFGHI'])

        # prune
        t1 = Tree("(((A, B), C)[&&NHX:name=I], (D, F)[&&NHX:name=J])[&&NHX:name=root];")
        D1 = t1.search_nodes(name="D")[0]
        t1.prune(["A","C", D1])
        sys.stdout.flush()
        self.assertEqual(set([n.name for n in t1.iter_descendants()]),  set(["A","C","D","I"]))

        t1 = Tree("(((A, B), C)[&&NHX:name=I], (D, F)[&&NHX:name=J])[&&NHX:name=root];")
        D1 = t1.search_nodes(name="D")[0]
        t1.prune(["A","B"])
        self.assertEqual( t1.write(), "(A:1,B:1);")

        # test prune keeping internal nodes

        t1 = Tree('(((((A,B)C)D,E)F,G)H,(I,J)K)root;', format=1)
        #print t1.get_ascii()
        t1.prune(['A', 'B', 'F', 'H'])
        #print t1.get_ascii()
        self.assertEqual(set([n.name for n in t1.traverse()]),
                         set(['A', 'B', 'F', 'H', 'root']))

        t1 = Tree('(((((A,B)C)D,E)F,G)H,(I,J)K)root;', format=1)
        #print t1.get_ascii()
        t1.prune(['A', 'B'])
        #print t1.get_ascii()
        self.assertEqual(set([n.name for n in t1.traverse()]),
                         set(['A', 'B', 'root']))

        t1 = Tree('(((((A,B)C)D,E)F,G)H,(I,J)K)root;', format=1)
        #print t1.get_ascii()
        t1.prune(['A', 'B', 'C'])
        #print t1.get_ascii()
        self.assertEqual(set([n.name for n in t1.traverse()]),
                         set(['A', 'B', 'C', 'root']))

        t1 = Tree('(((((A,B)C)D,E)F,G)H,(I,J)K)root;', format=1)
        #print t1.get_ascii()
        t1.prune(['A', 'B', 'I'])
        #print t1.get_ascii()
        self.assertEqual(set([n.name for n in t1.traverse()]),
                         set(['A', 'B', 'C', 'I', 'root']))

    def test_pruninig(self):
        # test prune preserving distances
        for i in range(10):
            t = Tree()
            t.populate(40, random_branches=True)
            orig_nw = t.write()
            distances = {}
            for a in t.iter_leaves():
                for b in t.iter_leaves():
                    distances[(a,b)] = round(a.get_distance(b), 6)

            to_keep = set(random.sample(t.get_leaves(), 6))
            t.prune(to_keep, preserve_branch_length=True)
            for a,b in distances:
                if a in to_keep and b in to_keep:
                    self.assertEqual(distances[(a,b)], round(a.get_distance(b), 6))

        # Total number of nodes is correct (no single child nodes)
        for x in range(10):
            t_fuzzy = Tree("(((A,B)1, C)2,(D,E)3)root;", format=1)
            t_fuzzy.sort_descendants()
            orig_nw = t_fuzzy.write()
            ref_nodes = t_fuzzy.get_leaves()
            t_fuzzy.populate(10)
            (t_fuzzy&'1').populate(3)
            (t_fuzzy&'2').populate(5)
            (t_fuzzy&'3').populate(5)
            t_fuzzy.prune(ref_nodes)
            t_fuzzy.sort_descendants()
            self.assertEqual(orig_nw, t_fuzzy.write())
            self.assertEqual(len(t_fuzzy.get_descendants()), (len(ref_nodes)*2)-2 )

        # Total number of nodes is correct (no single child nodes)
        t = Tree()
        sample_size = 5
        t.populate(1000)
        sample = random.sample(t.get_leaves(), sample_size)
        t.prune(sample)
        self.assertEqual(len(t), sample_size)
        self.assertEqual(len(t.get_descendants()), (sample_size*2)-2 )

        # Test preserve branch dist when pruning
        t = Tree()
        t.populate(100, random_branches=True)
        orig_leaves = t.get_leaves()
        sample_size = 50
        sample= random.sample(t.get_leaves(), sample_size)
        matrix1 = ["%f" %t.get_distance(a, b) for (a,b) in itertools.product(sample, sample)]
        t.prune(sample, preserve_branch_length=True)
        matrix2 = ["%f" %t.get_distance(a, b) for (a,b)in itertools.product(sample, sample)]

        self.assertEqual(matrix1, matrix2)
        self.assertEqual(len(t.get_descendants()), (sample_size*2)-2 )

    def test_resolve_polytomies(self):
        # resolve polytomy
        t = Tree("((a,a,a,a), (b,b,b,(c,c,c)));")
        t.resolve_polytomy()
        t.ladderize()
        self.assertEqual(t.write(format=9), "((a,(a,(a,a))),(b,(b,(b,(c,(c,c))))));")

        t = Tree("((((a,a,a,a))), (b,b,b,(c,c,c)));")
        t.standardize()
        t.ladderize()
        self.assertEqual(t.write(format=9), "((a,(a,(a,a))),(b,(b,(b,(c,(c,c))))));")

    def test_common_ancestors(self):
        # getting nodes, get_childs, get_sisters, get_tree_root,
        # get_common_ancestor, get_nodes_by_name
        # get_descendants_by_name, is_leaf, is_root
        t = Tree("(((A,B)N1,C)N2[&&NHX:tag=common],D)[&&NHX:tag=root:name=root];", format=1)
        self.assertEqual(t.get_sisters(), [])

        A = t.search_nodes(name="A")[0]
        B = t.search_nodes(name="B")[0]
        C = t.search_nodes(name="C")[0]
        root = (t&"root")
        self.assertEqual("A", A.name)
        test_not_found = lambda: t&'noffound'
        self.assertRaises(TreeError, test_not_found)

        self.assertEqual("common", A.get_common_ancestor(C).tag)
        self.assertEqual("common", A.get_common_ancestor([C]).tag)
        self.assertEqual("common", t.get_common_ancestor(A, C).tag)
        self.assertEqual("common", A.get_common_ancestor(C, B).tag)
        self.assertEqual(root, t.get_common_ancestor([A, "D"]))

        self.assertEqual("root", A.get_tree_root().tag)
        self.assertEqual("root", B.get_tree_root().tag)
        self.assertEqual("root", C.get_tree_root().tag)

        common = A.get_common_ancestor(C)
        self.assertEqual("root", common.get_tree_root().tag)

        self.assertTrue(common.get_tree_root().is_root())
        self.assertTrue(not A.is_root())
        self.assertTrue(A.is_leaf())
        self.assertTrue(not A.get_tree_root().is_leaf())
        self.assertRaises(TreeError, A.get_common_ancestor, Tree())

        # Test multiple target nodes and get_path argument
        common, path = t.get_common_ancestor(['A', 'C'], get_path=True)
        N1 = t & "N1"
        N2 = t & "N2"
        expected_path = {A: set([A, root, N1, N2]), C: set([C, N2, root])}
        self.assertEqual(common, N2)
        self.assertEqual(path.keys(), expected_path.keys())
        for k in path.keys():
            self.assertEqual(list(sorted(path[k], key=lambda x: x.name)),
                             list(sorted(expected_path[k], key=lambda x: x.name)))

        # Test common ancestor function using self as single argument (issue #398)
        common = A.get_common_ancestor(A)
        self.assertEqual(common, A)
        common = C.get_common_ancestor("C")
        self.assertEqual(common, C)
        common, path = C.get_common_ancestor("C", get_path=True)
        self.assertEqual(common, C)
        self.assertDictEqual(path, {})

    def test_getters_iters(self):

        # Iter ancestors
        t = Tree("(((((a,b)A,c)B,d)C,e)D,f)root;", format=1)
        ancestor_names = [n.name for n in (t&"a").get_ancestors()]
        self.assertEqual(ancestor_names, ["A", "B", "C", "D", "root"])
        ancestor_names = [n.name for n in (t&"B").get_ancestors()]
        self.assertEqual(ancestor_names, ["C", "D", "root"])


        # Tree magic python features
        t = Tree(nw_dflt)
        self.assertEqual(len(t), 20)
        self.assertTrue("Ddi0002240" in t)
        self.assertTrue(t.children[0] in t)
        for a in t:
            self.assertTrue(a.name)

        # Populate
        t = Tree(nw_full)
        prev_size= len(t)
        t.populate(25)
        self.assertEqual(len(t), prev_size+25)
        for i in range(10):
            t = Tree()
            t.populate(100, reuse_names=False)
            # Checks that all names are actually unique
            self.assertEqual(len(set(t.get_leaf_names())), 100)

        # Adding and removing features
        t = Tree("(((A,B),C)[&&NHX:tag=common],D)[&&NHX:tag=root];")
        A = t.search_nodes(name="A")[0]

        # Check gettters and itters return the same
        t = Tree(nw2_full)
        self.assertEqual(t.get_leaf_names(), [name for name in  t.iter_leaf_names()])
        self.assertEqual(t.get_leaves(), [name for name in  t.iter_leaves()])
        self.assertEqual(t.get_descendants(), [n for n in  t.iter_descendants()])

        self.assertEqual(set([n for n in t.traverse("preorder")]), \
                             set([n for n in t.traverse("postorder")]))
        self.assertTrue(t in set([n for n in t.traverse("preorder")]))

        # Check order or visiting nodes

        t = Tree("((3,4)2,(6,7)5)1;", format=1)
        #t = Tree("(((A, B)C, (D, E)F)G, (H, (I, J)K)L)M;", format=1)
        #postorder = [c for c in "ABCDEFGHIJKLM"]
        #preorder =  [c for c in reversed(postorder)]
        #levelorder = [c for c in "MGLCFHKABDEIJ"]
        postorder = "3426751"
        preorder = "1234567"
        levelorder = "1253467"

        self.assertEqual(preorder,
                          ''.join([n.name for n in t.traverse("preorder")]))

        self.assertEqual(postorder,
                         ''.join([n.name for n in t.traverse("postorder")]))

        self.assertEqual(levelorder,
                         ''.join([n.name for n in t.traverse("levelorder")]))

        # Swap childs
        n = t.get_children()
        t.swap_children()
        n.reverse()
        self.assertEqual(n, t.get_children())


    def test_distances(self):
        # Distances: get_distance, get_farthest_node,
        # get_farthest_descendant, get_midpoint_outgroup
        t = Tree("(((A:0.1, B:0.01):0.001, C:0.0001):1.0[&&NHX:name=I], (D:0.00001):0.000001[&&NHX:name=J]):2.0[&&NHX:name=root];")
        A = t.search_nodes(name="A")[0]
        B = t.search_nodes(name="B")[0]
        C = t.search_nodes(name="C")[0]
        D = t.search_nodes(name="D")[0]
        I = t.search_nodes(name="I")[0]
        J = t.search_nodes(name="J")[0]
        root = t.search_nodes(name="root")[0]

        self.assertEqual(A.get_common_ancestor(I).name, "I")
        self.assertEqual(A.get_common_ancestor(D).name, "root")
        self.assertEqual(A.get_distance(I), 0.101)
        self.assertEqual(A.get_distance(B), 0.11)
        self.assertEqual(A.get_distance(A), 0)
        self.assertEqual(I.get_distance(I), 0)
        self.assertEqual(A.get_distance(root), root.get_distance(A))

        self.assertEqual(t.get_distance(A, root), root.get_distance(A))
        self.assertEqual(t.get_distance(root, A), A.get_distance(root))

        # Get_farthest_node, get_farthest_leaf
        self.assertEqual(root.get_farthest_leaf(), (A,1.101) )
        self.assertEqual(root.get_farthest_node(), (A,1.101) )
        self.assertEqual(A.get_farthest_leaf(), (A, 0.0))
        self.assertEqual(A.get_farthest_node(), (D, 1.101011))
        self.assertEqual(I.get_farthest_node(), (D, 1.000011))

        # Topology only distances
        t = Tree('(((A:0.5, B:1.0):1.0, C:5.0):1, (D:10.0, F:1.0):2.0):20;')

        self.assertEqual(t.get_closest_leaf(), (t&'A', 2.5))
        self.assertEqual(t.get_farthest_leaf(), (t&'D', 12.0))
        self.assertEqual(t.get_farthest_leaf(topology_only=True), (t&'A', 2.0))
        self.assertEqual(t.get_closest_leaf(topology_only=True), (t&'C', 1.0))
        self.assertEqual(t.get_distance(t), 0.0)
        self.assertEqual(t.get_distance(t, topology_only=True), 0.0)
        self.assertEqual(t.get_distance(t&'A', topology_only=True), 2.0)

        self.assertEqual((t&'F').get_farthest_node(topology_only=True), (t&'A', 3.0))
        self.assertEqual((t&'F').get_farthest_node(topology_only=False), (t&'D', 11.0))

    def test_rooting(self):
        # Test set_outgroup and get_midpoint_outgroup
        t = Tree(nw2_full)
        YGR028W = t.get_leaves_by_name("YGR028W")[0]
        YGR138C = t.get_leaves_by_name("YGR138C")[0]
        d1 = YGR138C.get_distance(YGR028W)
        nodes = t.get_descendants()
        t.set_outgroup(t.get_midpoint_outgroup())
        o1, o2 = t.children[0], t.children[1]
        nw_original = t.write()
        d2 = YGR138C.get_distance(YGR028W)
        self.assertEqual(d1, d2)
        # Randomizing outgroup test: Can we recover original state
        # after many manipulations?
        for i in range(10):
            for j in range(1000):
                n = random.sample(nodes, 1)[0]
                t.set_outgroup(n)
            t.set_outgroup(t.get_midpoint_outgroup())
            self.assertEqual(set([t.children[0], t.children[1]]), set([o1, o2]))
            ##  I need to sort branches first
            #self.assertEqual(t.write(), nw_original)
        d3 = YGR138C.get_distance(YGR028W)
        self.assertEqual(d1, d3)

        t = Tree('(A,B,(C,D)E)root;', format=1);
        t.sort_descendants()
        nw_unrooted = t.write()
        t.set_outgroup(t.get_common_ancestor('C', 'D'));
        t.unroot()
        t.sort_descendants()
        self.assertEqual(nw_unrooted, t.write())

        t = Tree('(A:10,B:1,(C:1,D:1)E:1)root;', format=1);
        t.set_outgroup(t.get_midpoint_outgroup())
        self.assertEqual(t.children[0].dist, 5.0)
        self.assertEqual(t.children[1].dist, 5.0)


    def test_unroot(self):
        t = Tree("(('a':0.5, 'b':0.5):0.5, ('c':0.2, 'd':0.2):0.8):1;" )
        t2 = Tree("(('a':0.5, 'b':0.5):0.5, ('c':0.2, 'd':0.2):0.8):1;" )
        t.unroot(mode="keep")
        with self.assertRaises(ValueError):
            t.unroot(mode="new")
        t2.unroot(mode="legacy")
        self.assertEqual("(('c':0.2,'d':0.2)1:1.3,'a':0.5,'b':0.5);", t.write())
        self.assertEqual("(('c':0.2,'d':0.2)1:0.8,'a':0.5,'b':0.5);", t2.write())

    def test_tree_navigation(self):
        t = Tree("(((A, B)H, C)I, (D, F)J)root;", format=1)
        postorder = [n.name for n in t.traverse("postorder")]
        preorder = [n.name for n in t.traverse("preorder")]
        levelorder = [n.name for n in t.traverse("levelorder")]

        self.assertEqual(postorder, ['A', 'B', 'H', 'C', 'I', 'D', 'F', 'J', 'root'])
        self.assertEqual(preorder, ['root', 'I', 'H', 'A', 'B', 'C', 'J', 'D', 'F'])
        self.assertEqual(levelorder, ['root', 'I', 'J', 'H', 'C', 'D', 'F', 'A', 'B'])
        ancestors = [n.name for n in (t&"B").get_ancestors()]
        self.assertEqual(ancestors, ["H", "I", "root"])
        self.assertEqual(t.get_ancestors(), [])

        # add something of is_leaf_fn etc...
        custom_test = lambda x: x.name in set("JCH")
        custom_leaves = t.get_leaves(is_leaf_fn=custom_test)
        self.assertEqual(set([n.name for n in custom_leaves]), set("JHC"))

        # Test cached content
        t = Tree()
        t.populate(20)

        cache_node = t.get_cached_content()
        cache_node_leaves_only_false = t.get_cached_content(leaves_only=False)
        self.assertEqual(cache_node[t], set(t.get_leaves()))
        self.assertEqual(cache_node_leaves_only_false[t], set(t.traverse()))

        cache_name = t.get_cached_content(store_attr="name")
        cache_name_leaves_only_false = t.get_cached_content(store_attr="name", leaves_only=False)
        self.assertEqual(cache_name[t], set(t.get_leaf_names()))
        self.assertEqual(cache_name_leaves_only_false[t], set([n.name for n in t.traverse()]))

        cache_many = t.get_cached_content(store_attr=["name", "dist", "support"])
        cache_many_lof = t.get_cached_content(store_attr=["name", "dist", "support"], leaves_only=False)
        self.assertEqual(cache_many[t], set([(leaf.name, leaf.dist, leaf.support) for leaf in t.get_leaves()]))
        self.assertEqual(cache_many_lof[t], set([(n.name, n.dist, n.support) for n in t.traverse()]))


        #self.assertEqual(cache_name_lof[t], [t.name])


    def test_rooting(self):
        """ Check branch support and distances after rooting """

        t = Tree("((((a,b)1,c)2,i)3,(e,d)4)5;", format=1)
        t.set_outgroup(t&"a")


        t = Tree("(((a,b)2,c)x)9;", format=1)
        t.set_outgroup(t&"a")

        # Test branch support and distances after rooting
        SIZE = 35
        t = Tree()
        t.populate(SIZE, reuse_names=False)
        t.unroot()
        for n in t.iter_descendants():
            if n is not t:
                n.support = random.random()
                n.dist = random.random()
        for n in t.children:
            n.support = 0.999
        t2 = t.copy()

        names = set(t.get_leaf_names())
        cluster_id2support = {}
        cluster_id2dist = {}
        for n in t.traverse():
            cluster_names = set(n.get_leaf_names())
            cluster_names2 = names - cluster_names
            cluster_id = '_'.join(sorted(cluster_names))
            cluster_id2 = '_'.join(sorted(cluster_names2))
            cluster_id2support[cluster_id] = n.support
            cluster_id2support[cluster_id2] = n.support

            cluster_id2dist[cluster_id] = n.dist
            cluster_id2dist[cluster_id2] = n.dist


        for i in range(100):
            outgroup = random.sample(t2.get_descendants(), 1)[0]
            t2.set_outgroup(outgroup)
            for n in t2.traverse():
                cluster_names = set(n.get_leaf_names())
                cluster_names2 = names - cluster_names
                cluster_id = '_'.join(sorted(cluster_names))
                cluster_id2 = '_'.join(sorted(cluster_names2))
                self.assertEqual(cluster_id2support.get(cluster_id, None), n.support)
                self.assertEqual(cluster_id2support.get(cluster_id2, None), n.support)
                if n.up and n.up.up:
                    self.assertEqual(cluster_id2dist.get(cluster_id, None), n.dist)

        # Test unrooting
        t = Tree()
        t.populate(20)
        t.unroot()

        # Printing and info
        text = t.get_ascii()

        Tree().describe()
        Tree('(a,b,c);').describe()
        Tree('(a,(b,c));').describe()


    def test_treeid(self):
        t = Tree()
        t.populate(50, random_branches=True)
        orig_id = t.get_topology_id()
        nodes = t.get_descendants()
        for i in range(20):
            for n in random.sample(nodes, 10):
                n.swap_children()
                self.assertEqual(t.get_topology_id(), orig_id)


    def test_ultrametric(self):

        # Convert tree to a ultrametric topology in which distance from
        # leaf to root is always 100. Two strategies are available:
        # weighted, balanced or fixed
        t =  Tree()
        t.populate(100, random_branches=True)
        t.convert_to_ultrametric(100, "weighted")
        self.assertEqual(set([round(t.get_distance(n), 6) for n in t]), set([100.0]))

        t =  Tree()
        t.populate(100, random_branches=True)
        t.convert_to_ultrametric(100, "balanced")
        self.assertEqual(set([round(t.get_distance(n), 6) for n in t]), set([100.0]))

        t =  Tree()
        t.populate(100, random_branches=True)
        t.convert_to_ultrametric(100, "fixed")
        self.assertEqual(set([round(t.get_distance(n), 6) for n in t]), set([100.0]))


    def test_expand_polytomies_rf(self):
        gtree = Tree('((a:1, (b:1, (c:1, d:1):1):1), (e:1, (f:1, g:1):1):1);')
        ref1 = Tree('((a:1, (b:1, c:1, d:1):1):1, (e:1, (f:1, g:1):1):1);')
        ref2 = Tree('((a:1, (b:1, c:1, d:1):1):1, (e:1, f:1, g:1):1);')
        for ref in [ref1, ref2]:
            #print gtree, ref
            gtree.robinson_foulds(ref, expand_polytomies=True)[0]


        gtree = Tree('((g, h), (a, (b, (c, (d,( e, f))))));')
        ref3 = Tree('((a, b, c, (d, e, f)), (g, h));')
        ref4 = Tree('((a, b, c, d, e, f), (g, h));')
        ref5 = Tree('((a, b, (c, d, (e, f))), (g, h));')

        for ref in [ref3, ref4, ref5]:
            #print gtree, ref
            gtree.robinson_foulds(ref, expand_polytomies=True, polytomy_size_limit=8)[0]


        gtree = Tree('((g, h), (a, b, (c, d, (e, f))));')
        ref6 = Tree('((a, b, (c, d, e, f)), (g, h));')
        ref7 = Tree('((a, (b, (c, d, e, f))), (g, h));')
        ref8 = Tree('((a, b, c, (d, e, f)), (g, h));')
        ref9 = Tree('((d, b, c, (a, e, f)), (g, h));')

        for ref in [ref6, ref7, ref8, ref9]:
            #print gtree, ref
            gtree.robinson_foulds(ref, expand_polytomies=True)[0]
            #print "REF GOOD", gtree.robinson_foulds(ref, expand_polytomies=True, polytomy_size_limit=8)[0]

        gtree = Tree('((g, h), ((a, b), (c, d), (e, f)));')
        ref10 = Tree('((g, h), ((a, c), ((b, d), (e, f))));')

        for ref in [ref10]:
            #print gtree, ref
            gtree.robinson_foulds(ref, expand_polytomies=True, polytomy_size_limit=8)[0]

    def test_tree_compare(self):
        def _astuple(d):
            keynames = ["norm_rf", "rf", "max_rf", "ref_edges_in_source", "source_edges_in_ref", "effective_tree_size", "source_subtrees", "treeko_dist"]
            # print
            # print "ref", len(d["ref_edges"])
            # print "src", len(d["source_edges"])
            # print "common", len(d["common_edges"]), d['common_edges']
            # print d["rf"], d["max_rf"]

            return tuple([d[v] for v in keynames])


        ref1 = Tree('((((A, B)0.91, (C, D))0.9, (E,F)0.96), (G, H));')
        ref2 = Tree('(((A, B)0.91, (C, D))0.9, (E,F)0.96);')
        s1 = Tree('(((A, B)0.9, (C, D))0.9, (E,F)0.9);')


        small = Tree("((A, B), C);")
        # RF unrooted in too small trees for rf, but with at least one internal node
        self.assertEqual(_astuple(small.compare(ref1, unrooted=True)),
                         ("NA", "NA", 0.0, 1.0, 1.0, 3, 1, "NA"))

        small = Tree("(A, B);")
        # RF unrooted in too small trees
        self.assertEqual(_astuple(small.compare(ref1, unrooted=True)),
                         ("NA", "NA", 0.0, "NA", "NA", 2, 1, "NA"))

        small = Tree("(A, B);")
        # RF unrooted in too small trees
        self.assertEqual(_astuple(small.compare(ref1, unrooted=False)),
                         ("NA", "NA", 0.0, "NA", "NA", 2, 1, "NA"))

        # identical trees, 8 rooted partitions in total (4 an 4), and 6 unrooted
        self.assertEqual(_astuple(s1.compare(ref1)),
                         (0.0, 0.0, 8, 1.0, 1.0, 6, 1, "NA"))

        self.assertEqual(_astuple(s1.compare(ref1, unrooted=True)),
                         (0.0, 0.0, 6, 1.0, 1.0, 6, 1, "NA"))

        # The same stats should be return discarding branches, as the topology
        # is still identical, but branches used should be different
        self.assertEqual(_astuple(s1.compare(ref1, min_support_source=0.99, min_support_ref=.99)),
                         (0.0, 0.0, 2, 1.0, 1.0, 6, 1, "NA"))

        self.assertEqual(_astuple(s1.compare(ref1, min_support_source=0.99, min_support_ref=.99, unrooted=True)),
                         (0.0, 0.0, 2, 1.0, 1.0, 6, 1, "NA"))


        self.assertEqual(_astuple(s1.compare(ref1, min_support_source=0.99)),
                         (0.0, 0.0, 5, 1/4., 1.0, 6, 1, "NA"))


        self.assertEqual(_astuple(s1.compare(ref1, min_support_source=0.99, unrooted=True)),
                         (0.0, 0.0, 4, 6/8., 1.0, 6, 1, "NA"))


        self.assertEqual(_astuple(s1.compare(ref1, min_support_ref=0.99)),
                         (0.0, 0.0, 5, 1.0, 1/4., 6, 1, "NA"))


        self.assertEqual(_astuple(s1.compare(ref1, min_support_ref=0.99, unrooted=True)),
                         (0.0, 0.0, 4, 1.0, 6/8., 6, 1, "NA"))


        # Three partitions different
        s2 = Tree('(((A, E)0.9, (C, D))0.98, (B,F)0.95);')
        self.assertEqual(_astuple(s2.compare(ref1)),
                         (6/8., 6, 8, 1/4., 1/4., 6, 1, "NA"))

        self.assertEqual(_astuple(s2.compare(ref1, unrooted=True)),
                         (4/6., 4, 6, 6/8., 6/8., 6, 1, "NA"))

        # lets discard one branch from source tree.  there are 4 valid edges in
        # ref, 3 in source there is only 2 edges in common, CD and root (which
        # should be discounted for % of found branches)
        self.assertEqual(_astuple(s2.compare(ref1, min_support_source=0.95)),
                         (5/7., 5, 7, 1/4., 1/3., 6, 1, "NA"))

        # similar in unrooted, but we don not need to discount root edges
        self.assertEqual(_astuple(s2.compare(ref1, min_support_source=0.95, unrooted=True)),
                         (3/5., 3, 5, 6/8., 6/7., 6, 1, "NA"))


        # totally different trees
        s3 = Tree('(((A, C)0.9, (E, D))0.98, (B,F)0.95);')
        self.assertEqual(_astuple(s3.compare(ref1)),
                         (1.0, 8, 8, 0.0, 0.0, 6, 1, "NA"))


    def test_tree_diff(self):
        # this is the result of 100 Ktreedist runs on random trees, using rooted
        # and unrooted topologies. ETE should provide the same RF result
        samples = [
        [28, True, '(((z,y),(x,(w,v))),(u,t),((s,r),((q,(p,o)),((n,(m,(l,(k,j)))),(i,(h,g))))));', '(((k,(j,(i,(h,g)))),z),(y,x),((w,v),((u,(t,(s,(r,q)))),(p,(o,(n,(m,l)))))));'],
        [28, False, '(((t,s),((r,(q,p)),(o,n))),(((m,(l,(k,j))),(i,(h,g))),(z,(y,(x,(w,(v,u)))))));', '((((k,(j,i)),((h,g),z)),((y,(x,w)),((v,(u,t)),(s,(r,(q,p)))))),((o,n),(m,l)));'],
        [18, True, '(((v,(u,(t,s))),((r,(q,(p,o))),((n,m),(l,k)))),(j,(i,(h,g))),(z,(y,(x,w))));', '(((z,(y,(x,w))),(v,(u,(t,s)))),((r,(q,p)),(o,(n,m))),((l,(k,(j,i))),(h,g)));'],
        [26, True, '(((l,k),(j,i)),((h,g),(z,(y,(x,w)))),((v,(u,(t,(s,(r,q))))),((p,o),(n,m))));', '(((p,o),((n,(m,l)),(k,j))),((i,(h,g)),(z,y)),((x,(w,v)),((u,(t,s)),(r,q))));'],
        [24, True, '(((o,(n,m)),(l,(k,(j,(i,(h,g)))))),(z,(y,x)),((w,v),((u,(t,(s,r))),(q,p))));', '(((t,(s,(r,(q,(p,o))))),(n,m)),((l,k),(j,(i,(h,g)))),((z,y),((x,w),(v,u))));'],
        [24, True, '(((y,(x,(w,v))),(u,t)),((s,(r,(q,(p,o)))),(n,m)),((l,k),((j,(i,(h,g))),z)));', '(((z,(y,(x,w))),(v,(u,t))),(s,(r,(q,(p,(o,(n,(m,(l,k)))))))),(j,(i,(h,g))));'],
        [28, False, '(((p,(o,(n,(m,l)))),((k,(j,i)),(h,g))),((z,y),((x,(w,(v,u))),(t,(s,(r,q))))));', '((((t,(s,r)),(q,p)),((o,n),(m,(l,(k,(j,i)))))),(((h,g),(z,(y,(x,w)))),(v,u)));'],
        [28, True, '((((i,(h,g)),z),(y,x)),((w,v),((u,(t,(s,r))),(q,p))),((o,n),(m,(l,(k,j)))));', '((((h,g),z),(y,x)),(w,(v,u)),((t,s),((r,(q,p)),((o,(n,m)),(l,(k,(j,i)))))));'],
        [28, True, '(((x,(w,(v,(u,(t,(s,(r,(q,(p,o))))))))),((n,(m,l)),(k,(j,i)))),(h,g),(z,y));', '(((u,t),(s,r)),((q,p),(o,(n,m))),(((l,(k,(j,i))),((h,g),(z,(y,x)))),(w,v)));'],
        [22, False, '(((x,(w,(v,u))),((t,(s,r)),(q,p))),((o,(n,(m,l))),((k,j),((i,(h,g)),(z,y)))));', '(((z,(y,(x,(w,(v,u))))),(t,(s,r))),((q,(p,(o,(n,m)))),((l,k),(j,(i,(h,g))))));'],
        [26, True, '((z,(y,(x,w))),(v,(u,(t,s))),((r,(q,(p,(o,(n,m))))),((l,k),(j,(i,(h,g))))));', '(((v,(u,t)),((s,r),((q,(p,o)),(n,(m,l))))),((k,j),((i,(h,g)),z)),(y,(x,w)));'],
        [34, False, '((((i,(h,g)),(z,(y,x))),(w,v)),((u,t),((s,r),((q,(p,(o,n))),(m,(l,(k,j)))))));', '(((p,(o,(n,(m,(l,k))))),((j,i),(h,g))),(z,(y,(x,(w,(v,(u,(t,(s,(r,q))))))))));'],
        [30, False, '(((i,(h,g)),(z,y)),((x,w),((v,(u,(t,(s,(r,q))))),(p,(o,(n,(m,(l,(k,j)))))))));', '((((l,k),(j,(i,(h,g)))),(z,(y,(x,w)))),((v,u),((t,s),((r,(q,p)),(o,(n,m))))));'],
        [26, False, '(((v,(u,t)),((s,(r,q)),((p,o),((n,m),((l,k),(j,i)))))),((h,g),(z,(y,(x,w)))));', '(((y,(x,(w,v))),(u,(t,s))),(((r,q),((p,o),(n,(m,(l,k))))),((j,i),((h,g),z))));'],
        [20, False, '(((u,(t,s)),(r,q)),(((p,o),((n,m),((l,k),((j,i),((h,g),z))))),(y,(x,(w,v)))));', '((((u,t),(s,r)),(((q,p),(o,(n,m))),(((l,k),(j,i)),((h,g),z)))),((y,x),(w,v)));'],
        [20, True, '(((y,x),(w,v)),((u,(t,s)),((r,q),(p,(o,(n,(m,(l,k))))))),((j,(i,(h,g))),z));', '(((r,q),((p,o),(n,(m,(l,(k,j)))))),((i,(h,g)),(z,(y,(x,(w,v))))),(u,(t,s)));'],
        [24, True, '((((k,(j,i)),(h,g)),((z,(y,(x,w))),((v,(u,t)),(s,r)))),(q,(p,(o,n))),(m,l));', '((((s,r),((q,p),(o,(n,m)))),((l,k),((j,i),((h,g),z)))),(y,x),(w,(v,(u,t))));'],
        [18, True, '((w,(v,(u,(t,s)))),(r,q),((p,(o,n)),((m,(l,k)),((j,(i,(h,g))),(z,(y,x))))));', '(((y,x),((w,v),(u,(t,s)))),((r,(q,(p,(o,n)))),(m,l)),((k,j),((i,(h,g)),z)));'],
        [26, True, '(((j,(i,(h,g))),(z,(y,(x,(w,(v,(u,t))))))),(s,r),((q,p),((o,(n,m)),(l,k))));', '(((s,(r,(q,(p,(o,(n,(m,l))))))),(k,j)),((i,(h,g)),(z,y)),((x,(w,v)),(u,t)));'],
        [30, True, '((((r,(q,(p,(o,n)))),((m,l),(k,(j,i)))),((h,g),z)),(y,(x,(w,v))),(u,(t,s)));', '(((u,t),(s,r)),((q,p),(o,(n,(m,(l,(k,j)))))),(((i,(h,g)),(z,(y,x))),(w,v)));'],
        [30, False, '((((m,(l,k)),(j,i)),(((h,g),(z,y)),(x,w))),((v,u),(t,(s,(r,(q,(p,(o,n))))))));', '(((u,t),((s,(r,q)),(p,(o,(n,(m,(l,k))))))),((j,(i,(h,g))),(z,(y,(x,(w,v))))));'],
        [22, False, '(((k,(j,i)),(h,g)),((z,(y,x)),((w,(v,(u,(t,(s,r))))),((q,(p,(o,n))),(m,l)))));', '(((w,(v,u)),((t,(s,r)),((q,p),((o,(n,(m,l))),((k,(j,i)),((h,g),z)))))),(y,x));'],
        [26, False, '(((x,(w,(v,(u,(t,s))))),(r,q)),((p,(o,(n,(m,l)))),((k,j),((i,(h,g)),(z,y)))));', '(((o,(n,m)),(l,(k,j))),(((i,(h,g)),(z,y)),((x,w),((v,u),((t,(s,r)),(q,p))))));'],
        [28, True, '(((x,(w,v)),(u,(t,s))),((r,(q,(p,(o,(n,m))))),(l,(k,(j,(i,(h,g)))))),(z,y));', '((((i,(h,g)),(z,(y,x))),((w,v),((u,t),(s,(r,(q,p)))))),(o,n),((m,l),(k,j)));'],
        [20, False, '((((m,l),(k,(j,(i,(h,g))))),(z,y)),((x,(w,(v,(u,(t,s))))),(r,(q,(p,(o,n))))));', '((((m,l),((k,(j,i)),(h,g))),(z,(y,(x,(w,v))))),((u,t),(s,(r,(q,(p,(o,n)))))));'],
        [26, True, '(((o,(n,(m,(l,k)))),(j,i)),((h,g),(z,y)),((x,(w,(v,(u,(t,s))))),(r,(q,p))));', '((((t,(s,(r,(q,(p,(o,n)))))),(m,(l,k))),((j,i),(h,g))),(z,(y,x)),(w,(v,u)));'],
        [22, False, '((((p,o),((n,m),((l,k),(j,i)))),((h,g),(z,y))),((x,(w,(v,u))),((t,s),(r,q))));', '((((v,(u,(t,s))),(r,q)),((p,o),((n,m),(l,k)))),(((j,i),(h,g)),(z,(y,(x,w)))));'],
        [28, False, '((((r,(q,(p,(o,n)))),(m,(l,k))),(((j,i),(h,g)),((z,y),(x,w)))),((v,u),(t,s)));', '((((k,j),((i,(h,g)),(z,y))),(x,w)),(((v,(u,t)),(s,r)),((q,p),((o,n),(m,l)))));'],
        [20, True, '((((q,(p,o)),(n,m)),((l,k),((j,i),(h,g)))),(z,(y,x)),((w,v),(u,(t,(s,r)))));', '((((l,(k,(j,i))),(h,g)),((z,y),(x,(w,v)))),(u,t),((s,(r,(q,(p,o)))),(n,m)));'],
        [28, False, '(((t,(s,r)),(q,(p,o))),(((n,(m,(l,k))),(j,(i,(h,g)))),((z,y),(x,(w,(v,u))))));', '(((w,(v,u)),(t,s)),(((r,(q,p)),(o,n)),(((m,l),((k,j),((i,(h,g)),z))),(y,x))));'],
        [24, True, '((((h,g),(z,y)),((x,(w,(v,u))),(t,(s,(r,q))))),(p,o),((n,m),((l,k),(j,i))));', '(((t,s),((r,(q,p)),((o,(n,(m,l))),((k,j),(i,(h,g)))))),(z,y),(x,(w,(v,u))));'],
        [20, True, '(((p,o),(n,(m,(l,(k,(j,i)))))),((h,g),z),((y,(x,w)),((v,u),(t,(s,(r,q))))));', '(((y,(x,w)),(v,(u,t))),((s,r),(q,p)),((o,(n,m)),((l,(k,(j,i))),((h,g),z))));'],
        [32, True, '((((s,(r,q)),((p,(o,n)),(m,(l,k)))),((j,(i,(h,g))),(z,y))),(x,w),(v,(u,t)));', '(((u,(t,(s,r))),((q,(p,o)),((n,(m,l)),(k,(j,i))))),((h,g),(z,(y,x))),(w,v));'],
        [26, True, '(((z,(y,x)),(w,(v,(u,t)))),(s,(r,(q,(p,(o,n))))),((m,l),(k,(j,(i,(h,g))))));', '(((u,t),((s,r),((q,p),((o,n),((m,(l,k)),((j,i),((h,g),z))))))),(y,x),(w,v));'],
        [10, True, '(((p,o),((n,m),((l,(k,(j,i))),((h,g),(z,y))))),(x,(w,(v,u))),((t,s),(r,q)));', '((((n,m),((l,(k,(j,i))),((h,g),(z,y)))),(x,w)),(v,(u,(t,(s,(r,q))))),(p,o));'],
        [30, True, '((((h,g),z),((y,x),((w,v),(u,t)))),(s,r),((q,p),((o,n),((m,l),(k,(j,i))))));', '((((v,(u,(t,(s,r)))),(q,(p,o))),((n,m),((l,k),(j,(i,(h,g)))))),(z,y),(x,w));'],
        [30, False, '(((q,(p,o)),((n,m),((l,(k,(j,(i,(h,g))))),(z,y)))),((x,(w,v)),(u,(t,(s,r)))));', '((((t,s),((r,q),((p,o),(n,m)))),((l,k),(j,i))),(((h,g),z),((y,(x,w)),(v,u))));'],
        [24, False, '(((p,o),(n,m)),(((l,(k,(j,i))),(h,g)),((z,y),((x,w),((v,u),(t,(s,(r,q))))))));', '((x,(w,v)),((u,(t,(s,(r,q)))),((p,(o,(n,(m,(l,(k,(j,(i,(h,g))))))))),(z,y))));'],
        [28, False, '(((z,y),((x,w),((v,u),(t,s)))),((r,(q,(p,(o,(n,m))))),((l,k),((j,i),(h,g)))));', '((((s,(r,q)),((p,o),((n,(m,l)),(k,(j,(i,(h,g))))))),(z,y)),((x,w),(v,(u,t))));'],
        [24, False, '((((o,n),((m,l),((k,(j,i)),(h,g)))),(z,(y,x))),((w,(v,(u,(t,(s,r))))),(q,p)));', '(((q,(p,(o,(n,m)))),((l,(k,j)),(i,(h,g)))),(z,(y,(x,(w,(v,(u,(t,(s,r)))))))));'],
        [22, True, '(((p,(o,(n,m))),((l,k),((j,i),((h,g),(z,y))))),(x,w),((v,u),((t,s),(r,q))));', '(((u,(t,(s,(r,(q,(p,(o,(n,m)))))))),((l,k),((j,i),((h,g),(z,(y,x)))))),w,v);'],
        [28, False, '((((r,q),((p,o),(n,(m,l)))),((k,(j,i)),(h,g))),((z,y),((x,(w,v)),(u,(t,s)))));', '(((h,g),z),((y,x),((w,v),((u,t),((s,(r,(q,(p,(o,(n,m)))))),(l,(k,(j,i))))))));'],
        [30, True, '((((h,g),z),((y,(x,(w,(v,u)))),((t,s),((r,(q,(p,o))),(n,m))))),(l,k),(j,i));', '((((o,n),((m,(l,(k,j))),((i,(h,g)),z))),(y,(x,(w,v)))),(u,(t,s)),(r,(q,p)));'],
        [30, True, '(((v,u),(t,(s,(r,(q,p))))),((o,(n,m)),((l,(k,j)),((i,(h,g)),z))),(y,(x,w)));', '((((m,(l,k)),((j,i),(h,g))),(z,y)),(x,w),((v,(u,(t,(s,(r,q))))),(p,(o,n))));'],
        [26, True, '(((q,p),((o,(n,(m,l))),(k,(j,i)))),((h,g),z),((y,x),((w,(v,(u,t))),(s,r))));', '((((j,(i,(h,g))),(z,(y,x))),((w,v),(u,t))),(s,(r,q)),((p,o),(n,(m,(l,k)))));'],
        [20, False, '((((o,(n,m)),((l,k),((j,i),((h,g),z)))),(y,x)),(((w,v),(u,t)),((s,r),(q,p))));', '((((j,i),((h,g),z)),((y,x),(w,(v,(u,(t,(s,r))))))),((q,p),((o,n),(m,(l,k)))));'],
        [30, False, '(((x,w),(v,(u,(t,(s,(r,(q,(p,(o,(n,m)))))))))),((l,k),((j,(i,(h,g))),(z,y))));', '(((m,l),((k,(j,(i,(h,g)))),z)),((y,(x,(w,(v,(u,t))))),((s,r),((q,p),(o,n)))));'],
        [32, True, '((((y,x),(w,v)),((u,(t,(s,r))),(q,(p,o)))),((n,m),(l,(k,j))),((i,(h,g)),z));', '(((m,l),(k,(j,i))),((h,g),z),((y,(x,w)),((v,u),((t,s),(r,(q,(p,(o,n))))))));'],
        [28, True, '(((v,u),((t,(s,(r,(q,p)))),((o,n),((m,l),(k,(j,(i,(h,g)))))))),(z,y),(x,w));', '((((n,m),((l,k),((j,i),((h,g),(z,(y,(x,(w,(v,u))))))))),(t,s)),(r,q),(p,o));'],
        [32, False, '(((r,(q,p)),(o,n)),(((m,(l,k)),(j,i)),(((h,g),(z,y)),((x,w),((v,u),(t,s))))));', '(((y,x),((w,v),(u,(t,(s,r))))),(((q,(p,(o,n))),(m,l)),((k,(j,(i,(h,g)))),z)));'],
        [20, True, '(((w,v),((u,(t,(s,r))),((q,p),((o,(n,(m,l))),((k,j),((i,(h,g)),z)))))),y,x);', '(((w,v),((u,t),(s,(r,q)))),((p,o),((n,(m,l)),(k,j))),((i,(h,g)),(z,(y,x))));'],
        [24, False, '(((x,(w,v)),((u,(t,s)),(r,q))),(((p,o),((n,(m,l)),(k,j))),((i,(h,g)),(z,y))));', '((((i,(h,g)),z),((y,x),(w,v))),((u,(t,s)),((r,(q,(p,(o,(n,m))))),(l,(k,j)))));'],
        [22, False, '((((k,(j,(i,(h,g)))),(z,(y,x))),((w,v),(u,t))),((s,(r,(q,(p,o)))),(n,(m,l))));', '(((w,v),(u,(t,(s,(r,(q,(p,o))))))),(((n,m),((l,(k,(j,i))),((h,g),z))),(y,x)));'],
        [28, True, '(((x,w),((v,u),((t,s),(r,(q,p))))),((o,n),(m,l)),((k,(j,i)),((h,g),(z,y))));', '((((p,o),(n,m)),((l,(k,(j,i))),((h,g),z))),(y,(x,(w,v))),((u,t),(s,(r,q))));'],
        [30, False, '(((q,p),((o,(n,(m,l))),((k,(j,(i,(h,g)))),z))),((y,x),((w,(v,u)),(t,(s,r)))));', '((((m,(l,k)),((j,(i,(h,g))),z)),(y,(x,w))),((v,(u,(t,(s,(r,q))))),(p,(o,n))));'],
        [30, False, '(((y,x),((w,(v,(u,(t,(s,r))))),(q,p))),((o,(n,(m,(l,(k,(j,i)))))),((h,g),z)));', '((((t,(s,(r,q))),((p,(o,(n,(m,l)))),((k,(j,i)),(h,g)))),(z,y)),((x,w),(v,u)));'],
        [20, False, '(((u,(t,s)),(r,(q,(p,(o,(n,(m,(l,(k,j))))))))),(((i,(h,g)),z),(y,(x,(w,v)))));', '(((o,n),(m,(l,(k,j)))),(((i,(h,g)),(z,y)),((x,(w,v)),((u,(t,(s,r))),(q,p)))));'],
        [26, False, '(((t,s),((r,(q,(p,(o,n)))),(m,(l,k)))),(((j,i),((h,g),z)),((y,(x,w)),(v,u))));', '(((r,(q,(p,o))),((n,(m,(l,k))),((j,i),(h,g)))),((z,(y,(x,(w,v)))),(u,(t,s))));'],
        [28, True, '((((r,q),((p,(o,(n,(m,l)))),((k,(j,i)),(h,g)))),(z,(y,(x,w)))),(v,u),(t,s));', '(((x,(w,(v,(u,(t,s))))),(r,(q,(p,o)))),(n,m),((l,k),((j,(i,(h,g))),(z,y))));'],
        [28, False, '(((t,s),((r,(q,p)),((o,n),(m,(l,(k,(j,i))))))),(((h,g),(z,y)),(x,(w,(v,u)))));', '((((h,g),(z,(y,(x,(w,v))))),(u,(t,(s,r)))),((q,(p,(o,(n,m)))),(l,(k,(j,i)))));'],
        [26, True, '((((q,(p,o)),((n,m),((l,(k,(j,i))),(h,g)))),(z,(y,x))),(w,v),(u,(t,(s,r))));', '(((y,x),(w,(v,u))),((t,(s,r)),((q,p),(o,n))),((m,(l,k)),((j,(i,(h,g))),z)));'],
        [28, False, '((((q,(p,(o,n))),((m,(l,k)),((j,(i,(h,g))),z))),(y,x)),((w,(v,(u,t))),(s,r)));', '(((z,(y,x)),(w,v)),(((u,t),((s,(r,(q,p))),((o,n),(m,l)))),((k,(j,i)),(h,g))));'],
        [22, True, '(((x,w),((v,(u,(t,s))),(r,q))),((p,(o,n)),((m,(l,k)),(j,(i,(h,g))))),(z,y));', '((((j,(i,(h,g))),(z,(y,x))),(w,(v,u))),((t,s),((r,q),(p,o))),((n,m),(l,k)));'],
        [26, False, '((((n,(m,l)),(k,j)),(((i,(h,g)),(z,y)),((x,w),((v,u),(t,s))))),((r,q),(p,o)));', '(((v,u),(t,s)),(((r,(q,(p,(o,n)))),((m,(l,k)),(j,i))),((h,g),(z,(y,(x,w))))));'],
        [32, False, '((((n,(m,(l,(k,j)))),((i,(h,g)),z)),(y,x)),((w,v),((u,(t,(s,r))),(q,(p,o)))));', '((((v,u),(t,(s,(r,(q,p))))),((o,(n,(m,(l,k)))),(j,(i,(h,g))))),((z,y),(x,w)));'],
        [20, False, '((((q,(p,(o,n))),(m,l)),((k,(j,(i,(h,g)))),z)),((y,(x,(w,(v,(u,t))))),(s,r)));', '(((w,(v,(u,t))),(s,r)),(((q,p),(o,n)),(((m,l),(k,(j,i))),((h,g),(z,(y,x))))));'],
        [20, True, '(((z,(y,(x,w))),(v,u)),((t,(s,r)),(q,(p,o))),((n,(m,l)),((k,(j,i)),(h,g))));', '((((q,(p,(o,n))),(m,l)),((k,j),(i,(h,g)))),(z,y),((x,w),((v,u),(t,(s,r)))));'],
        [34, False, '(((w,(v,(u,(t,(s,(r,q)))))),(p,o)),(((n,m),(l,(k,j))),((i,(h,g)),(z,(y,x)))));', '(((y,(x,(w,(v,u)))),(t,(s,r))),(((q,(p,(o,(n,(m,(l,k)))))),(j,i)),((h,g),z)));'],
        [26, False, '(((y,x),(w,(v,(u,t)))),(((s,r),((q,(p,o)),(n,(m,l)))),((k,(j,(i,(h,g)))),z)));', '(((s,(r,(q,(p,o)))),(n,m)),(((l,k),((j,i),((h,g),(z,(y,(x,w)))))),(v,(u,t))));'],
        [30, False, '(((v,(u,t)),((s,r),((q,p),((o,(n,(m,(l,k)))),(j,i))))),(((h,g),z),(y,(x,w))));', '(((y,(x,(w,v))),((u,(t,s)),(r,(q,(p,o))))),((n,(m,l)),((k,(j,i)),((h,g),z))));'],
        [26, False, '(((y,x),(w,v)),(((u,t),((s,(r,(q,p))),(o,n))),((m,(l,k)),((j,i),((h,g),z)))));', '((((s,(r,q)),((p,(o,n)),((m,l),(k,(j,i))))),((h,g),z)),((y,(x,w)),(v,(u,t))));'],
        [22, True, '(((w,v),(u,t)),((s,r),((q,p),((o,(n,m)),((l,k),((j,i),(h,g)))))),(z,(y,x)));', '(((z,y),(x,(w,(v,u)))),(t,(s,r)),((q,(p,o)),((n,m),((l,(k,(j,i))),(h,g)))));'],
        [28, False, '(((y,x),(w,(v,(u,t)))),(((s,(r,q)),((p,o),(n,(m,(l,k))))),((j,i),((h,g),z))));', '((((i,(h,g)),(z,(y,x))),((w,(v,u)),(t,s))),((r,q),((p,o),((n,m),(l,(k,j))))));'],
        [26, False, '(((v,(u,(t,s))),(r,(q,p))),(((o,n),((m,(l,(k,j))),((i,(h,g)),(z,y)))),(x,w)));', '(((q,p),((o,n),((m,l),((k,j),((i,(h,g)),z))))),(y,(x,(w,(v,(u,(t,(s,r))))))));'],
        [26, True, '(((t,(s,(r,q))),((p,o),((n,(m,l)),((k,j),((i,(h,g)),z))))),(y,x),(w,(v,u)));', '(((z,y),(x,w)),(v,u),((t,(s,r)),((q,(p,(o,(n,(m,l))))),((k,(j,i)),(h,g)))));'],
        [30, True, '(((w,(v,(u,(t,(s,r))))),(q,p)),((o,(n,m)),((l,k),(j,i))),(((h,g),z),(y,x)));', '((((p,o),(n,(m,(l,(k,(j,(i,(h,g)))))))),(z,(y,x))),(w,(v,u)),((t,s),(r,q)));'],
        [26, True, '((((i,(h,g)),(z,y)),(x,w)),((v,u),((t,(s,r)),(q,p))),((o,n),(m,(l,(k,j)))));', '(((l,k),((j,i),((h,g),(z,y)))),(x,w),((v,u),((t,s),((r,(q,(p,o))),(n,m)))));'],
        [26, False, '(((x,w),((v,(u,(t,s))),((r,(q,p)),((o,(n,(m,(l,k)))),((j,i),(h,g)))))),(z,y));', '(((p,(o,(n,m))),(l,k)),(((j,i),(h,g)),((z,y),((x,(w,v)),((u,t),(s,(r,q)))))));'],
        [24, True, '(((x,w),((v,(u,t)),(s,r))),((q,p),(o,(n,(m,(l,k))))),((j,i),((h,g),(z,y))));', '(((h,g),(z,y)),(x,(w,(v,u))),((t,(s,r)),(q,(p,(o,(n,(m,(l,(k,(j,i))))))))));'],
        [24, True, '(((y,x),(w,v)),((u,t),((s,r),((q,p),((o,n),(m,(l,k)))))),((j,(i,(h,g))),z));', '((((r,(q,p)),(o,(n,(m,(l,(k,(j,(i,(h,g))))))))),(z,y)),(x,(w,v)),(u,(t,s)));'],
        [28, False, '(((y,(x,(w,v))),((u,t),((s,(r,q)),((p,(o,n)),((m,l),(k,(j,i))))))),((h,g),z));', '(((v,u),(t,(s,(r,(q,(p,(o,n))))))),(((m,l),((k,j),((i,(h,g)),z))),(y,(x,w))));'],
        [26, True, '((((h,g),z),((y,x),((w,(v,u)),((t,(s,(r,q))),(p,(o,n)))))),(m,(l,k)),(j,i));', '((z,y),(x,(w,(v,(u,t)))),((s,r),((q,p),((o,n),((m,(l,k)),(j,(i,(h,g))))))));'],
        [24, True, '(((u,t),(s,r)),((q,p),((o,n),((m,(l,(k,(j,(i,(h,g)))))),z))),(y,(x,(w,v))));', '((((j,(i,(h,g))),z),(y,x)),(w,(v,(u,t))),((s,(r,(q,p))),((o,(n,m)),(l,k))));'],
        [30, True, '(((t,(s,r)),((q,p),((o,n),(m,(l,(k,j)))))),((i,(h,g)),z),((y,x),(w,(v,u))));', '((((w,(v,(u,t))),(s,(r,q))),((p,(o,(n,m))),(l,k))),((j,i),(h,g)),(z,(y,x)));'],
        [30, False, '((((x,(w,v)),(u,t)),((s,(r,q)),(p,o))),(((n,m),((l,k),((j,i),(h,g)))),(z,y)));', '((r,q),((p,(o,n)),((m,(l,(k,(j,i)))),((h,g),(z,(y,(x,(w,(v,(u,(t,s)))))))))));'],
        [28, True, '((((k,j),((i,(h,g)),(z,(y,x)))),(w,v)),(u,t),((s,(r,q)),(p,(o,(n,(m,l))))));', '(((z,y),(x,w)),(v,(u,(t,(s,(r,q))))),((p,o),((n,(m,(l,(k,(j,i))))),(h,g))));'],
        [18, True, '(((t,s),((r,(q,(p,o))),(n,m))),((l,(k,j)),((i,(h,g)),(z,y))),((x,w),(v,u)));', '((((l,k),(j,i)),(((h,g),(z,y)),(x,w))),((v,u),(t,s)),((r,q),((p,o),(n,m))));'],
        [26, True, '(((h,g),z),(y,(x,w)),((v,(u,(t,s))),((r,(q,p)),((o,(n,(m,l))),(k,(j,i))))));', '(((s,r),(q,p)),((o,n),(m,l)),(((k,j),((i,(h,g)),(z,(y,x)))),(w,(v,(u,t)))));'],
        [30, True, '(((x,w),((v,(u,(t,(s,(r,(q,(p,(o,n)))))))),((m,(l,k)),((j,i),(h,g))))),z,y);', '((((h,g),z),(y,x)),((w,v),((u,(t,s)),(r,q))),((p,(o,(n,(m,l)))),(k,(j,i))));'],
        [30, False, '(((v,(u,(t,(s,(r,q))))),((p,(o,(n,m))),((l,(k,(j,i))),(h,g)))),((z,y),(x,w)));', '(((v,u),((t,(s,(r,(q,(p,o))))),(n,(m,(l,(k,j)))))),((i,(h,g)),(z,(y,(x,w)))));'],
        [22, True, '(((z,y),((x,(w,v)),((u,(t,(s,r))),(q,(p,o))))),(n,m),((l,k),(j,(i,(h,g)))));', '(((r,q),(p,(o,(n,m)))),((l,(k,(j,(i,(h,g))))),(z,y)),((x,w),(v,(u,(t,s)))));'],
        [30, True, '(((x,w),((v,(u,(t,(s,r)))),(q,p))),((o,n),(m,l)),((k,j),((i,(h,g)),(z,y))));', '((((p,o),((n,(m,(l,k))),((j,i),(h,g)))),((z,y),(x,(w,v)))),(u,t),(s,(r,q)));'],
        [32, False, '(((r,(q,p)),(o,(n,m))),(((l,(k,(j,i))),(h,g)),((z,(y,(x,(w,(v,u))))),(t,s))));', '((((j,(i,(h,g))),(z,y)),(x,(w,(v,(u,t))))),(((s,r),(q,(p,o))),((n,m),(l,k))));'],
        [30, False, '((((q,p),((o,(n,(m,(l,k)))),((j,(i,(h,g))),(z,y)))),(x,w)),((v,u),(t,(s,r))));', '((((o,(n,m)),((l,(k,(j,i))),((h,g),z))),(y,x)),((w,v),((u,t),((s,r),(q,p)))));'],
        [28, False, '((((s,r),((q,(p,o)),(n,(m,l)))),((k,(j,i)),(h,g))),((z,(y,x)),(w,(v,(u,t)))));', '(((m,l),(k,j)),(((i,(h,g)),z),((y,x),((w,(v,(u,(t,(s,r))))),((q,p),(o,n))))));'],
        [20, True, '((((z,y),(x,(w,(v,u)))),((t,s),(r,q))),((p,o),(n,(m,l))),((k,(j,i)),(h,g)));', '(((j,i),(h,g)),(z,(y,x)),((w,(v,u)),((t,(s,(r,q))),((p,o),((n,m),(l,k))))));'],
        [20, False, '(((v,u),((t,s),(r,q))),(((p,o),(n,(m,l))),(((k,(j,i)),((h,g),z)),(y,(x,w)))));', '((((s,(r,q)),(p,o)),(((n,(m,l)),(k,(j,i))),((h,g),z))),((y,x),((w,v),(u,t))));'],
        [28, True, '((z,y),(x,w),((v,u),((t,(s,(r,q))),((p,(o,(n,m))),(l,(k,(j,(i,(h,g)))))))));', '((((r,q),((p,o),((n,m),((l,k),(j,i))))),((h,g),(z,(y,x)))),(w,v),(u,(t,s)));'],
        [24, False, '((((k,(j,(i,(h,g)))),(z,y)),(x,(w,v))),(((u,t),(s,(r,q))),((p,o),(n,(m,l)))));', '(((w,v),(u,(t,s))),(((r,(q,(p,o))),((n,m),(l,(k,(j,(i,(h,g))))))),(z,(y,x))));'],
        [24, True, '((((n,m),((l,(k,j)),(i,(h,g)))),(z,y)),(x,(w,v)),((u,(t,(s,(r,q)))),(p,o)));', '(((r,q),(p,o)),((n,(m,l)),((k,j),((i,(h,g)),z))),((y,x),(w,(v,(u,(t,s))))));']]

        # test RF exceptions
        t1 = Tree('(a,b,(c,d,e));')
        t2 = Tree('((a,b),(c,d,e));')
        # testing unrooted trees
        self.assertRaises(TreeError, t1.robinson_foulds, t2=t2)

        # expand polytomies and unrooted trees
        self.assertRaises(TreeError, t1.robinson_foulds, t2=t2,
                          unrooted_trees=True, expand_polytomies=True)

        # usisng expand_polytomies and correct_by_size at the same time
        self.assertRaises(TreeError, t1.robinson_foulds, t2=t1,
                          unrooted_trees=True, expand_polytomies=True,
                          correct_by_polytomy_size=True)

        # correct by size when polytomies in both sides
        self.assertRaises(TreeError, t1.robinson_foulds, t2=t1,
                          unrooted_trees=True, correct_by_polytomy_size=True)

        # polytomy larger than deafult limit
        self.assertRaises(TreeError, t2.robinson_foulds, t2=Tree('(a, (b,c,d,e,f,g,h));'),
                          expand_polytomies=True)

        # duplicated items
        t3 = Tree('(a, (b, (c, c)));')
        self.assertRaises(TreeError, t3.robinson_foulds, t2=t2)
        self.assertRaises(TreeError, t2.robinson_foulds, t2=t3)



        # test RF using a knonw set of results
        for RF, unrooted, nw1, nw2 in samples:
            t1 = Tree(nw1)
            t2 = Tree(nw2)
            rf, rf_max, names, r1, r2, d1, d2 = t1.robinson_foulds(t2, unrooted_trees=unrooted)
            real_max = (20*2) - 4 if not unrooted else (20*2) - 6

            self.assertEqual(len(names), 20)
            self.assertEqual(rf_max, real_max)
            self.assertEqual(rf, RF)

            comp = t1.compare(t2, unrooted=unrooted)
            self.assertEqual(20, comp['effective_tree_size'])
            self.assertEqual(rf_max, comp['max_rf'])
            self.assertEqual(RF, comp['rf'])
            # Let's insert some random nodes, that should be ignored
            for target in random.sample([n for n in t2.get_descendants() if not n.is_leaf()], 5):
                target.populate(5)
            comp = t1.compare(t2, unrooted=unrooted)
            self.assertEqual(20, comp['effective_tree_size'])
            self.assertEqual(rf_max, comp['max_rf'])
            self.assertEqual(RF, comp['rf'])

        # test treeko functionality
        t = PhyloTree('((((A,B),C), ((A,B),C)), (((A,B),C), ((A,B),C)));')
        ref = Tree('((A,B),C);')
        comp = t.compare(ref, has_duplications=True)
        #from pprint import pprint
        #pprint(comp)
        self.assertEqual(comp['effective_tree_size'], 3)
        self.assertEqual(comp['treeko_dist'], 0.0)
        self.assertEqual(comp['norm_rf'], 0.0)
        self.assertEqual(comp['rf'], 0.0)
        self.assertEqual(comp['max_rf'], 2)
        self.assertEqual(comp['source_subtrees'], 4)

        # test polytomy corrections

        ref2 = Tree("((a:1, (b:1, c:1, d:1):1):1, (e:1, f:1, g:1):1);")
        gtree = Tree("((a:1, (b:1, (c:1, d:1):1):1), (e:1, (f:1, g:1):1):1);")

        # Basic polytomy
        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref2)
        self.assertEqual(rf, 2)
        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref2, expand_polytomies=True)
        self.assertEqual(rf, 0)


        # nested polytomies
        gtree = Tree('((g, h), (a, (b, (c, (d,( e, f))))));')
        ref3 = Tree('((a, b, c, (d, e, f)), (g, h));')
        ref4 = Tree('((a, b, c, d, e, f), (g, h));')
        ref5 = Tree('((a, b, (c, d, (e, f))), (g, h));')

        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref3)
        self.assertEqual(rf, 3)
        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref3, expand_polytomies=True)
        self.assertEqual(rf, 0)

        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref4)
        self.assertEqual(rf, 4)
        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref4, expand_polytomies=True,
                                                                  polytomy_size_limit=6)
        self.assertEqual(rf, 0)

        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref5)
        self.assertEqual(rf, 2)
        rf, max_rf, names, r1, r2, d1, d2 = gtree.robinson_foulds(ref5, expand_polytomies=True)
        self.assertEqual(rf, 0)

        # two side polytomies
        t1 = Tree("((a:1, (b:1, c:1, d:1):1):1, (e:1, f:1, g:1):1);")
        t2 = Tree("((a:1, (b:1, c:1, d:1):1), (e:1, (f:1, g:1):1):1);")
        rf, max_rf, names, r1, r2, d1, d2 = t1.robinson_foulds(t2, expand_polytomies=True)
        self.assertEqual(rf, 0)


        # test auto pruned tree topology
        for RF, unrooted, nw1, nw2 in samples:
            # Add fake tips in the newick
            for x in "clanger":
                nw1 = nw1.replace(x, "(%s,%s1)" %(x, x) )
                nw2 = nw2.replace(x, "(%s,%s2)" %(x, x) )
            t1 = Tree(nw1)
            t2 = Tree(nw2)
            rf, rf_max, names, r1, r2, d1, d2 = t1.robinson_foulds(t2, unrooted_trees=unrooted)
            self.assertEqual(len(names), 20)
            real_max = (20*2) - 4 if not unrooted else (20*2) - 6
            self.assertEqual(rf_max, real_max)
            self.assertEqual(rf, RF)

        #print 'Testing RF with branch support thresholds...'
        # test discarding lowly supported branches
        for RF, unrooted, nw1, nw2 in samples:
            # Add fake internal nodes with low support
            for x in "jlnqr":
                nw1 = nw1.replace(x, "(%s,(%s1, %s11)0.6)" %(x, x, x) )
                nw2 = nw2.replace(x, "(%s,(%s1, %s11)0.5)" %(x, x, x) )
            t1 = Tree(nw1)
            t2 = Tree(nw2)
            rf, rf_max, names, r1, r2, d1, d2 = t1.robinson_foulds(t2, unrooted_trees=unrooted,
                                                                   min_support_t1 = 0.1, min_support_t2 = 0.1)
            self.assertEqual(len(names), 30)
            real_max = (30*2) - 4 if not unrooted else (30*2) - 6
            self.assertEqual(rf_max, real_max)
            self.assertEqual(rf, RF)

            rf, rf_max, names, r1, r2, d1, d2 = t1.robinson_foulds(t2, unrooted_trees=unrooted,
                                                                   min_support_t1 = 0.0, min_support_t2 = 0.51)
            self.assertEqual(len(names), 30)
            real_max = (30*2) - 4 - 5 if not unrooted else (30*2) - 6 -5 # -5 to discount low support branches
            self.assertEqual(rf_max, real_max)
            self.assertEqual(rf, RF)

            rf, rf_max, names, r1, r2, d1, d2 = t1.robinson_foulds(t2, unrooted_trees=unrooted,
                                                                   min_support_t1 = 0.61, min_support_t2 = 0.0)
            self.assertEqual(len(names), 30)
            real_max = (30*2) - 4 - 5 if not unrooted else (30*2) - 6 -5 # -5 to discount low support branches
            self.assertEqual(rf_max, real_max)
            self.assertEqual(rf, RF)


            rf, rf_max, names, r1, r2, d1, d2 = t1.robinson_foulds(t2, unrooted_trees=unrooted,
                                                                   min_support_t1 = 0.61, min_support_t2 = 0.51)
            self.assertEqual(len(names), 30)
            real_max = (30*2) - 4 - 10 if not unrooted else (30*2) - 6 -10 # -10 to discount low support branches
            self.assertEqual(rf_max, real_max)
            self.assertEqual(rf, RF)





    def test_monophyly(self):
        #print 'Testing monophyly checks...'
        t =  Tree("((((((a, e), i), o),h), u), ((f, g), j));")
        is_mono, monotype, extra  = t.check_monophyly(values=["a", "e", "i", "o", "u"], target_attr="name")
        self.assertEqual(is_mono, False)
        self.assertEqual(monotype, "polyphyletic")
        is_mono, monotype, extra= t.check_monophyly(values=["a", "e", "i", "o"], target_attr="name")
        self.assertEqual(is_mono, True)
        self.assertEqual(monotype, "monophyletic")
        is_mono, monotype, extra =  t.check_monophyly(values=["i", "o"], target_attr="name")
        self.assertEqual(is_mono, False)
        self.assertEqual(monotype, "paraphyletic")

        # Test examples
        #print 'Testing monophyly check with unrooted trees'
        t = PhyloTree('(aaa1, (aaa3, (aaa4, (bbb1, bbb2))));')
        is_mono, montype, extra = t.check_monophyly(values=set(['aaa']), target_attr='species', unrooted=True)
        self.assertEqual(is_mono, True)
        self.assertEqual(extra, set())

        t = PhyloTree('(aaa1, (bbb3, (aaa4, (bbb1, bbb2))));')
        is_mono, montype, extra = t.check_monophyly(values=set(['aaa']), target_attr='species', unrooted=True)
        self.assertEqual(is_mono, False)
        self.assertEqual(extra, set([t&'bbb3']))

        t = PhyloTree('(aaa1, (aaa3, (aaa4, (bbb1, bbb2))));')
        is_mono, montype, extra = t.check_monophyly(values=set(['bbb']), target_attr='species', unrooted=True)
        self.assertEqual(is_mono, True)
        self.assertEqual(extra, set())

        t = PhyloTree('(aaa1, (aaa3, (aaa4, (bbb1, ccc2))));')
        is_mono, montype, extra = t.check_monophyly(values=set(['bbb', 'ccc']), target_attr='species', unrooted=True)
        self.assertEqual(is_mono, True)
        self.assertEqual(extra, set())

        t = PhyloTree('(aaa1, (aaa3, (bbb4, (bbb1, bbb2))));')
        is_mono, montype, extra = t.check_monophyly(values=set(['bbb4', 'bbb2']), target_attr='name', unrooted=True)
        self.assertEqual(is_mono, False)
        self.assertEqual(extra, set([t&'bbb1']))

        t = PhyloTree('(aaa1, (aaa3, (bbb4, (bbb1, bbb2))));')
        is_mono, montype, extra = t.check_monophyly(values=set(['bbb1', 'bbb2']), target_attr='name', unrooted=True)
        self.assertEqual(is_mono, True)
        self.assertEqual(extra, set())

        t = PhyloTree('(aaa1, aaa3, (aaa4, (bbb1, bbb2)));')
        is_mono, montype, extra = t.check_monophyly(values=set(['aaa']), target_attr='species', unrooted=True)
        self.assertEqual(is_mono, True)
        self.assertEqual(extra, set())

        t = PhyloTree('(aaa1, bbb3, (aaa4, (bbb1, bbb2)));')
        is_mono, montype, extra = t.check_monophyly(values=set(['aaa']), target_attr='species', unrooted=True)
        self.assertEqual(is_mono, False)
        self.assertEqual(extra, set([t&'bbb3']))

        #print 'Check monophyly randomization test'
        t = PhyloTree()
        t.populate(100)
        ancestor = t.get_common_ancestor(['aaaaaaaaaa', 'aaaaaaaaab', 'aaaaaaaaac'])
        all_nodes = t.get_descendants()
        # I test every possible node as root for the tree. The content of ancestor
        # should allways be detected as monophyletic
        results = set()
        for x in all_nodes:
            mono, part, extra = t.check_monophyly(values=set(ancestor.get_leaf_names()), target_attr='name', unrooted=True)
            results.add(mono)
            t.set_outgroup(x)
        self.assertEqual(list(results), [True])

        #print 'Testing get_monophyly'
        t =  Tree("((((((4, e), i)M1, o),h), u), ((3, 4), (i, june))M2);", format=1)
        # we annotate the tree using external data
        colors = {"a":"red", "e":"green", "i":"yellow",
                  "o":"black", "u":"purple", "4":"green",
                  "3":"yellow", "1":"white", "5":"red",
                  "june":"yellow"}
        for leaf in t:
            leaf.add_features(color=colors.get(leaf.name, "none"))
        green_yellow_nodes = set([t&"M1", t&"M2"])
        mono_nodes = t.get_monophyletic(values=["green", "yellow"], target_attr="color")
        self.assertEqual(set(mono_nodes), green_yellow_nodes)


    def test_copy(self):
        t = Tree("((A, B)Internal_1:0.7, (C, D)Internal_2:0.5)root:1.3;", format=1)
        # we add a custom annotation to the node named A
        (t & "A").add_features(label="custom Value")
        # we add a complex feature to the A node, consisting of a list of lists
        (t & "A").add_features(complex=[[0,1], [2,3], [1,11], [1,0]])


        t_nw  = t.copy("newick")
        t_nwx = t.copy("newick-extended")
        t_pkl = t.copy("cpickle")
        (t & "A").testfn = lambda: "YES"
        t_deep = t.copy("deepcopy")

        self.assertEqual((t_nw & "root").name, "root")
        self.assertEqual((t_nwx & "A").label, "custom Value")
        self.assertEqual((t_pkl & "A").complex[0], [0,1])
        self.assertEqual((t_deep & "A").testfn(), "YES")


    def test_cophenetic_matrix(self):
        t = Tree(nw_full)
        dists, leaves = t.cophenetic_matrix()
        actualdists = [
            [0, 2.3662779999999994, 2.350554999999999, 2.7002369999999996, 3.527812, 3.305472, 2.424086, 2.424086,
             2.432288, 2.483421, 2.3355079999999995, 2.3355079999999995, 2.389350999999999, 2.3812519999999995,
             2.404005999999999, 2.3945459999999996, 2.4035289999999994, 2.3689599999999995, 2.4048339999999997,
             2.6487609999999995],
            [2.3662779999999994, 0, 0.079009, 1.122461, 2.38897, 2.16663, 0.47755000000000003, 0.47755000000000003,
             0.4857520000000001, 0.5368850000000001, 0.320202, 0.32020200000000004, 0.133729, 0.12563,
             0.14838400000000002, 0.230406, 0.168047, 0.113338, 0.16935199999999997, 0.633455],
            [2.350554999999999, 0.079009, 0, 1.106738, 2.373247, 2.150907, 0.461827, 0.461827, 0.47002900000000003,
             0.521162, 0.304479, 0.30447900000000006, 0.11800599999999999, 0.10990699999999998, 0.132661, 0.214683,
             0.152324, 0.09761499999999998, 0.153629, 0.617732],
            [2.7002369999999996, 1.122461, 1.106738, 0, 2.7229289999999997, 2.5005889999999997, 1.180269, 1.180269,
             1.188471, 1.239604, 1.091691, 1.091691, 1.145534, 1.137435, 1.160189, 1.1507290000000001, 1.159712,
             1.125143, 1.161017, 1.404944],
            [3.527812, 2.38897, 2.373247, 2.7229289999999997, 0, 2.6926, 2.446778, 2.446778, 2.45498, 2.506113,
             2.3581999999999996, 2.3581999999999996, 2.412043, 2.403944, 2.426698, 2.4172379999999998,
             2.4262209999999995, 2.391652, 2.427526, 2.6714529999999996],
            [3.305472, 2.16663, 2.150907, 2.5005889999999997, 2.6926, 0, 2.224438, 2.224438, 2.23264, 2.283773, 2.13586,
             2.13586, 2.189703, 2.181604, 2.204358, 2.194898, 2.2038809999999995, 2.169312, 2.205186, 2.449113],
            [2.424086, 0.47755000000000003, 0.461827, 1.180269, 2.446778, 2.224438, 0, 0.0, 0.01366,
             0.30963300000000005, 0.44678, 0.44677999999999995, 0.5006229999999999, 0.49252399999999996, 0.515278,
             0.505818, 0.5148010000000001, 0.480232, 0.5161060000000001, 0.7600329999999998],
            [2.424086, 0.47755000000000003, 0.461827, 1.180269, 2.446778, 2.224438, 0.0, 0, 0.01366,
             0.30963300000000005, 0.44678, 0.44677999999999995, 0.5006229999999999, 0.49252399999999996, 0.515278,
             0.505818, 0.5148010000000001, 0.480232, 0.5161060000000001, 0.7600329999999998],
            [2.432288, 0.4857520000000001, 0.47002900000000003, 1.188471, 2.45498, 2.23264, 0.01366, 0.01366, 0,
             0.317835, 0.45498200000000005, 0.454982, 0.508825, 0.500726, 0.5234800000000001, 0.51402, 0.523003,
             0.48843400000000003, 0.524308, 0.7682349999999999],
            [2.483421, 0.5368850000000001, 0.521162, 1.239604, 2.506113, 2.283773, 0.30963300000000005,
             0.30963300000000005, 0.317835, 0, 0.506115, 0.506115, 0.559958, 0.551859, 0.574613, 0.565153, 0.574136,
             0.539567, 0.5754410000000001, 0.8193679999999999],
            [2.3355079999999995, 0.320202, 0.304479, 1.091691, 2.3581999999999996, 2.13586, 0.44678, 0.44678,
             0.45498200000000005, 0.506115, 0, 0.0, 0.343275, 0.33517600000000003, 0.35793, 0.34847,
             0.35745299999999997, 0.322884, 0.35875799999999997, 0.531709],
            [2.3355079999999995, 0.32020200000000004, 0.30447900000000006, 1.091691, 2.3581999999999996, 2.13586,
             0.44677999999999995, 0.44677999999999995, 0.454982, 0.506115, 0.0, 0, 0.34327500000000005,
             0.33517600000000003, 0.35793, 0.34847, 0.357453, 0.32288400000000006, 0.358758, 0.531709],
            [2.389350999999999, 0.133729, 0.11800599999999999, 1.145534, 2.412043, 2.189703, 0.5006229999999999,
             0.5006229999999999, 0.508825, 0.559958, 0.343275, 0.34327500000000005, 0, 0.013558999999999998, 0.021967,
             0.25347900000000007, 0.19112, 0.031257, 0.192425, 0.656528],
            [2.3812519999999995, 0.12563, 0.10990699999999998, 1.137435, 2.403944, 2.181604, 0.49252399999999996,
             0.49252399999999996, 0.500726, 0.551859, 0.33517600000000003, 0.33517600000000003, 0.013558999999999998, 0,
             0.028214, 0.24538000000000004, 0.183021, 0.023157999999999998, 0.184326, 0.648429],
            [2.404005999999999, 0.14838400000000002, 0.132661, 1.160189, 2.426698, 2.204358, 0.515278, 0.515278,
             0.5234800000000001, 0.574613, 0.35793, 0.35793, 0.021967, 0.028214, 0, 0.26813400000000004,
             0.20577499999999999, 0.045912, 0.20708, 0.6711830000000001],
            [2.3945459999999996, 0.230406, 0.214683, 1.1507290000000001, 2.4172379999999998, 2.194898, 0.505818,
             0.505818, 0.51402, 0.565153, 0.34847, 0.34847, 0.25347900000000007, 0.24538000000000004,
             0.26813400000000004, 0, 0.267657, 0.233088, 0.268962, 0.661723],
            [2.4035289999999994, 0.168047, 0.152324, 1.159712, 2.4262209999999995, 2.2038809999999995,
             0.5148010000000001, 0.5148010000000001, 0.523003, 0.574136, 0.35745299999999997, 0.357453, 0.19112,
             0.183021, 0.20577499999999999, 0.267657, 0, 0.170729, 0.057269, 0.670706],
            [2.3689599999999995, 0.113338, 0.09761499999999998, 1.125143, 2.391652, 2.169312, 0.480232, 0.480232,
             0.48843400000000003, 0.539567, 0.322884, 0.32288400000000006, 0.031257, 0.023157999999999998, 0.045912,
             0.233088, 0.170729, 0, 0.17203399999999996, 0.636137],
            [2.4048339999999997, 0.16935199999999997, 0.153629, 1.161017, 2.427526, 2.205186, 0.5161060000000001,
             0.5161060000000001, 0.524308, 0.5754410000000001, 0.35875799999999997, 0.358758, 0.192425, 0.184326,
             0.20708, 0.268962, 0.057269, 0.17203399999999996, 0, 0.672011],
            [2.6487609999999995, 0.633455, 0.617732, 1.404944, 2.6714529999999996, 2.449113, 0.7600329999999998,
             0.7600329999999998, 0.7682349999999999, 0.8193679999999999, 0.531709, 0.531709, 0.656528, 0.648429,
             0.6711830000000001, 0.661723, 0.670706, 0.636137, 0.672011, 0]
        ]

        actualleaves = ['Aga0007658', 'Bta0018700', 'Cfa0016700', 'Cin0011239', 'Ddi0002240', 'Dme0014628',
                        'Dre0008390', 'Dre0008391', 'Dre0008392', 'Fru0004507', 'Gga0000981', 'Gga0000982',
                        'Hsa0000001', 'Hsa0010711', 'Hsa0010730', 'Mdo0014718', 'Mms0024821', 'Ptr0000001',
                        'Rno0030248', 'Xtr0044988']

        for i in range(len(actualdists)):
            for j in range(len(actualdists[i])):
                self.assertAlmostEqual(actualdists[i][j], dists[i][j], places=4)
        self.assertEqual(actualleaves, leaves)


    # def test_traversing_speed(self):
    #     return
    #     for x in xrange(10):
    #         t = Tree()
    #         t.populate(100000)

    #         leaves = t.get_leaves()
    #         sample = random.sample(leaves, 100)

    #         t1 = time.time()
    #         a = t.get_common_ancestor_OLD(sample)
    #         t2 = time.time() - t1
    #         print "OLD get common", t2

    #         t1 = time.time()
    #         b = t.get_common_ancestor(sample)
    #         t2 = time.time() - t1
    #         print "NEW get common", t2

    #         self.assertEqual(a, b)


    #         t1 = time.time()
    #         [n for n in t._iter_descendants_postorder_OLD()]
    #         t2 = time.time() - t1
    #         print "OLD postorder", t2

    #         t1 = time.time()
    #         [n for n in t._iter_descendants_postorder()]
    #         t2 = time.time() - t1
    #         print "NEW postorder", t2

if __name__ == '__main__':
    unittest.main()
