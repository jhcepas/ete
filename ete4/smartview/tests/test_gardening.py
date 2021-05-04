"""
Test the functionality of gardening.py. To run with pytest.
"""

import sys
from os.path import abspath, dirname
sys.path.insert(0, f'{abspath(dirname(__file__))}/../../..')

from ete4 import Tree
from ete4.smartview.ete import gardening


def load_sample_tree():
    return Tree('((d,e)b,(f,g)c):0;')
    # :0
    # ├─b
    # │ ├─d
    # │ └─e
    # └─c
    #   ├─f
    #   └─g


def strip(text):
    # Helps compare tree visualizations.
    indent = next(len(line) - len(line.lstrip())
        for line in text.splitlines() if line.strip())
    return '\n'.join(line[indent:].rstrip()
        for line in text.splitlines() if line.strip())


def test_sort():
    t = load_sample_tree()

    t2 = t.copy()
    gardening.sort(t2)
    assert str(t2) == str(t)

    gardening.sort(t2, reverse=True)
    assert str(t2) == """
      /-g
   /-|
  |   \-f
--|
  |   /-e
   \-|
      \-d\
"""

    t3 = Tree('((f,g)b,c,d,((j,k)h,i)e)a;')
    gardening.sort(t3, key=lambda node: len(node.children))
    assert str(t3) == """
   /-c
  |
  |--d
  |
--|   /-f
  |--|
  |   \-g
  |
  |   /-i
   \-|
     |   /-j
      \-|
         \-k\
"""


def test_root_at():
    t = load_sample_tree()

    t = gardening.root_at(gardening.get_node(t, [0,1]))
    assert str(t) == """
   /-e
--|
  |   /-d
   \-|
     |   /-f
      \-|
         \-g\
"""


    t = gardening.root_at(t&'d')
    assert str(t) == """
   /-d
  |
--|      /-f
  |   /-|
   \-|   \-g
     |
      \-e\
"""

    t = gardening.root_at(t&'c')
    assert str(t) == """
      /-f
   /-|
  |   \-g
--|
  |   /-e
   \-|
      \-d\
"""

    t = gardening.root_at(t&'b')
    assert str(t) == """
      /-e
   /-|
  |   \-d
--|
  |   /-f
   \-|
      \-g\
"""


def test_get_root_id():
    t = load_sample_tree()

    for node_name, node_id in [
            ('', []),
            ('b', [0]),
            ('c', [1]),
            ('d', [0,0]),
            ('e', [0,1]),
            ('f', [1,0]),
            ('g', [1,1])]:
        node = t&node_name
        assert gardening.get_root_id(node) == (t, node_id)
        assert node == gardening.get_node(t, node_id)


def test_move():
    t = load_sample_tree()

    gardening.move(t&'b')
    assert str(t) == """
      /-f
   /-|
  |   \-g
--|
  |   /-d
   \-|
      \-e\
"""


def test_remove():
    t = load_sample_tree()

    gardening.remove(t&'c')
    assert str(t) == """
      /-d
-- /-|
      \-e\
"""

    gardening.remove(t&'d')
    assert str(t) == """
-- /- /-e\
"""
