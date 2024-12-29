.. currentmodule:: ete4

The Tree structure
==================

.. contents::

Trees
-----

A **tree** is a widely-used data structures that emulates a tree shape
with a set of linked **nodes**. Each node in a tree has zero or more
child nodes, and one parent node (except the **root node**, which has
no parent).

Formally, a tree is a *graph* (set of connected nodes) which is
*directed* (connections have direction), *acyclic* (there are no
loops), and *totally connected* (can reach all nodes starting from the
root node).

Nodes with children are called **internal nodes**, and nodes with no
children are called **leaf nodes** (or simply **leaves**).

::

        ╭╴leaf
  ╴root╶┤          ╭╴internal╶┬╴leaf
        ╰╴internal╶┤          ╰╴internal╶┬╴leaf
                   │                     ╰╴leaf
                   ╰╴internal╶┬╴leaf
                              ╰╴leaf

Every node in a tree can be seen as the root node of the *subtree*
composed of that node and all its descendants.

In bioinformatics, trees are the result of many analyses, such as
phylogenetics or clustering. To assists in their manipulation,
analysis and visualization, we developed ETE (the *Environment for
Tree Exploration*). It is a Python package that provides general
methods to handle and visualize tree topologies, as well as specific
modules to deal with phylogenetic trees.


.. _sec:newick-formats:

Reading and writing newick trees
--------------------------------

The `Newick format <https://en.wikipedia.org/wiki/Newick_format>`_ is
one of the most widely used standard representations of trees in
bioinformatics. It uses nested parentheses to represent hierarchical
data structures as text strings. The original newick standard is able
to encode information about the tree topology, branch distances and
node names. Nevertheless, it is not uncommon to find slightly
different variations of the format.

ETE can read and write many of them:

.. table::

  ====== ========================================= =============================================
  Format Description                               Example
  ====== ========================================= =============================================
  0      internal nodes with support (flexible)    ((D:0.7,F:0.5)1.0:0.6,(B:0.2,H:0.7)1.0:0.8);
  1      internal nodes with names (flexible)      ((D:0.7,F:0.5)E:0.6,(B:0.2,H:0.7)B:0.8);
  2      internal w/ support, all lengths present  ((D:0.7,F:0.5)1.0:0.6,(B:0.2,H:0.7)1.0:0.8);
  3      internal w/ names, all lengths present    ((D:0.7,F:0.5)E:0.6,(B:0.2,H:0.7)B:0.8);
  4      names and lengths for leaves only         ((D:0.7,F:0.5),(B:0.2,H:0.7));
  5      leaf names and all lengths                ((D:0.7,F:0.5):0.6,(B:0.2,H:0.7):0.8);
  6      leaf names and internal lengths           ((D,F):0.6,(B,H):0.8);
  7      all names and leaf lengths                ((D:0.7,F:0.5)E,(B:0.2,H:0.7)B);
  8      all names (leaves and internal nodes)     ((D,F)E,(B,H)B);
  9      leaf names only                           ((D,F),(B,H));
  100    topology only                             ((,),(,));
  ====== ========================================= =============================================

Formats labeled as *flexible* allow for missing information. For
instance, format 0 will be able to load a newick tree even if it does
not contain branch support information. However, format 2 would raise
an exception. In other words, if you want to control that your newick
files strictly follow a given pattern you can use **strict** format
definitions.


Creating a tree
~~~~~~~~~~~~~~~

ETE's class :class:`Tree`, provided by the main module :mod:`ete4`,
can be used to construct trees. You can create a single node by
calling :func:`Tree` without any arguments::

  from ete4 import Tree

  # Empty tree (single node).
  t = Tree()

Or you can call it with a dictionary specifying the properties of that
single node. You can also use the :func:`populate <Tree.populate>`
method to populate a tree with a random topology::

  from ete4 import Tree

  # Also a single node, but with some properties.
  t = Tree({'name': 'root', 'dist': 1.0, 'support': 0.5, 'coolness': 'high'})

  # Populate t with a random topology of size 10.
  t.populate(10)

(In all the examples we will want to write ``from ete4 import Tree``
first to use the :class:`Tree` class, as we did above. In the
remaining examples we will assume that you have already imported it.)

The properties of a node are stored in its :attr:`props <Tree.props>`
dictionary. With the previous example, writing ``print(t.props)`` will
show us a dictionary that should look familiar. And if you
``print(t)`` a tree, you will see a simple visualization. For our
example of the previously populated tree::

  print(t.props)  # where the properties of a node are stored
  # {'name': 'root', 'dist': 1.0, 'support': 0.5, 'coolness': 'high'}

  print(t)  # will look more or less like:
  #  ╭─┬╴a
  #  │ ╰╴b
  # ─┤ ╭─┬╴c
  #  │ │ ╰─┬╴d
  #  ╰─┤   ╰─┬╴e
  #    │     ╰╴f
  #    ╰─┬╴g
  #      ╰─┬╴h
  #        ╰─┬╴i
  #          ╰╴j


Reading newick trees
~~~~~~~~~~~~~~~~~~~~

To load a tree from a newick text string you can pass to :func:`Tree`
the text string containing the newick structure. Alternatively, you
can pass a file object that contains the newick string. And
optionally, you can also specify the format that should be used to
parse it (0 by default, see :ref:`sec:newick-formats`).

::

  # Load a tree structure from a newick string. It returns the root node.
  t1 = Tree('(A:1,(B:1,(E:1,D:1):0.5):0.5);')

  # Load a tree structure from a newick file.
  t2 = Tree(open('genes_tree.nw'))

  # You can also specify how to parse the newick. For instance,
  # internal nodes by default are interpreted as support values
  # (parser=0), but we can interpret them as names with parser=1.
  t3 = Tree('(A:1,(B:1,(E:1,D:1)E:0.5)F:0.5);', parser=1)


Writing newick trees
~~~~~~~~~~~~~~~~~~~~

Any ETE tree instance can be exported using newick notation using the
:func:`Tree.write` method. It also allows for parser selection, so you
can use the same function to convert between newick formats.

::

  # Load a tree with internal names.
  t = Tree('(A:1,(B:1,(E:1,D:1)E:0.5)F:0.5);', parser=1)

  # Print its newick using the default parser.
  print(t.write())  # (A:1,(B:1,(E:1,D:1):0.5):0.5);

  # To print the internal names you can change the parser.
  print(t.write(parser=1))  # (A:1,(B:1,(E:1,D:1)E:0.5)F:0.5);

  # We can also write into a file.
  t.write(parser=1, outfile='new_tree.nw')


Understanding ETE trees
-----------------------

Any tree topology can be represented as a succession of **nodes**
connected in a hierarchical way. Thus, for practical reasons, ETE
makes no distinction between the concepts of tree and node, as any
tree can be represented by its root node. This allows to use any
internal node within a tree as another sub-tree instance.

Once trees are loaded, they can be manipulated as normal python
objects. Given that a tree is actually a collection of nodes connected
in a hierarchical way, what you usually see as a tree will be the root
node instance from which the tree structure is hanging. However, every
node within a ETE's tree structure can be also considered a subtree.
This means, for example, that all the operational methods that we will
review in the following sections are available at any possible level
within a tree. Moreover, this feature will allow you to separate large
trees into smaller partitions, or concatenate several trees into a
single structure.


Basic tree attributes
---------------------

Each tree node has two basic attributes used to establish its position
in the tree: :attr:`up <Tree.up>` and :attr:`children
<Tree.children>`. The first is a pointer to its parent's node, while
the latter is a list of children nodes. Although it is possible to
modify the structure of a tree by changing these attributes, it is
strongly recommend not to do it. Several methods are provided to
manipulate each node's connections in a safe way (see
:ref:`sec:modifying-tree-topology`).

In addition, three other basic attributes are always present in any
tree node instance (let's call it ``node``):

.. table::

  ==================== ==========================================================================
  Method               Description
  ==================== ==========================================================================
  :attr:`node.dist`    Distance from the node to its parent (branch length)
  :attr:`node.support` Reliability of the partition defined by the node (like bootstrap support)
  :attr:`node.name`    Node's name
  ==================== ==========================================================================

In addition, several methods are provided to perform basic operations
on tree node instances:

.. table::

  ======================== ====================================================================
  Method                   Description
  ======================== ====================================================================
  :attr:`node.is_leaf`     True if node has no children
  :attr:`node.is_root`     True if node has no parent
  :attr:`node.root`        The top-most node within the same tree structure as node
  :attr:`len(node)`        Returns the number of leaves under node
  :attr:`print(node)`      Prints a text-based representation of the tree topology under node
  :attr:`n in node`        True if *n* is a leaf under node
  :attr:`for leaf in node` Iterates over all leaves under node
  :func:`node.explore`     Explore node graphically using a GUI
  ======================== ====================================================================

This is an example on how to access such attributes::

  # Create a random tree topology.
  t.populate(15)

  print(t)  # text visualization of the tree
  print(t.children)  # list of children nodes directly hanging from the root
  print(t.up)  # should be None, since t is the root

  # You can also iterate over tree leaves using a simple syntax.
  for leaf in t:
      print(leaf.name)

  n = next(iter(t))  # take the first leaf
  print('First leaf name:', n.name)
  print('First leaf distance:', n.dist)
  print('t.is_leaf = %s   n.is_leaf = %s' % (t.is_leaf, n.is_leaf))
  print(n.root == t)  # True
  print(t.children[0].root == t)  # True too
  print(t.children[0].children[0].root == t)  # and True again


The meaning of the "root node" in unrooted trees
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a tree is loaded from external sources, a pointer to the top-most
node is returned. This is called the tree root, and **it will exist
even if the tree is conceptually considered as unrooted**. That is,
the root node can be considered as the master node, since it
represents the whole tree structure.

ETE will consider that a tree is "unrooted" if the master root node
has more than two children.

::

  unrooted_tree = Tree('(A,B,(C,D));')
  print(unrooted_tree)
  #  ╭╴A
  # ─┼╴B
  #  ╰─┬╴C
  #    ╰╴D

  rooted_tree = Tree('((A,B),(C,D));')
  print(rooted_tree)
  #  ╭─┬╴A
  # ─┤ ╰╴B
  #  ╰─┬╴C
  #    ╰╴D


Browsing trees (traversing)
---------------------------

One of the most basic operations for tree analysis is *tree browsing*.
This is, essentially, visiting nodes within a tree. ETE provides a
number of methods to search for specific nodes or to navigate over the
hierarchical structure of a tree.


Getting leaves, descendants and node's relatives
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tree instances contain several functions to access their descendants.
Available methods are self explanatory:

.. autosummary::

   Tree.descendants
   Tree.ancestors
   Tree.leaves
   Tree.leaf_names
   Tree.get_children
   Tree.get_sisters


Traversing (browsing) trees
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Often, when processing trees, all nodes need to be visited. This is
called tree traversing. There are different ways to traverse a tree
structure depending on the order in which children nodes are visited.
ETE implements the three most common strategies: *preorder*,
*postorder* and *levelorder*. The following scheme shows the
differences in the strategy for visiting nodes (note that in all cases
the whole tree is browsed):

* *preorder*: 1) visit the root, 2) traverse the left subtree, 3)
  traverse the right subtree.
* *postorder*: 1) traverse the left subtree, 2) traverse the right
  subtree, 3) visit the root.
* *levelorder* (default): every node on a level is visited before going
  to a lower level.

Every node in a tree includes a :func:`traverse <Tree.traverse>`
method, which can be used to visit, one by one, every node node under
the current partition. In addition, the :func:`descendants
<Tree.descendants>` method can be set to use either a post- or a
preorder strategy. The only difference between :func:`traverse
<Tree.traverse>` and :func:`descendants <Tree.descendants>` is that
the first will include the root node in the iteration.

.. autosummary::

   Tree.traverse
   Tree.descendants
   Tree.leaves

The argument :attr:`strategy` can take the values "levelorder",
"preorder", or "postorder"::

  # Make a tree.
  t = Tree('((((H,K)D,(F,I)G)B,E)A,((L,(N,Q)O)J,(P,S)M)C);', parser=1)

  # Traverse the nodes in postorder.
  for node in t.traverse('postorder'):
      print(node.name)  # or do some analysis with the node

  # If we want to iterate over a tree excluding the root node, we can
  # use the descendants method instead.
  for node in t.descendants('postorder'):
      print(node.name)  # or do some analysis with the node

Additionally, you can implement your own traversing function using the
structural attributes of nodes. In the following example, only nodes
between a given leaf and the tree root are visited::

  t = Tree('(A:1,(B:1,(C:1,D:1):0.5):0.5);')

  # Browse the tree from a specific leaf to the root.
  node = t['C']  # selects the node named 'C'
  while node:
      print(node.dist)  # for example, or do some operations with it
      node = node.up


Advanced traversing
~~~~~~~~~~~~~~~~~~~

.. _is_leaf_fn:

Collapsing nodes while traversing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ETE supports the use of the :attr:`is_leaf_fn` argument in most of its
traversing functions. The value of :attr:`is_leaf_fn` is expected to
be a pointer to any python function that accepts a node instance as
its first argument and returns a boolean value (True if node should be
considered a leaf node).

By doing so, all traversing methods will use such a custom function to
decide if a node is a leaf. This becomes specially useful when dynamic
collapsing of nodes is needed, thus avoiding to prune the same tree in
many different ways.

For instance, given a large tree structure, the following code will
export the newick of the pruned version of the topology, where nodes
grouping the same tip labels are collapsed::

  t = Tree('((((a,a,a)a,a)aa,(b,b)b)ab,(c,(d,d)d)cd);', parser=1)

  print(t.to_str(props=['name'], compact=True))  # show internal names too
  #                  ╭╴a
  #              ╭╴a╶┼╴a
  #         ╭╴aa╶┤   ╰╴a
  #    ╭╴ab╶┤    ╰╴a
  # ╴⊗╶┤    ╰╴b╶┬╴b
  #    │        ╰╴b
  #    ╰╴cd╶┬╴c
  #         ╰╴d╶┬╴d
  #             ╰╴d

  # Cache for every node (for each node, a set of all its leaves' names).
  node2labels = t.get_cached_content('name')

  def collapsed_leaf(node):
      return len(node2labels[node]) == 1

  print(t.write(parser=1, is_leaf_fn=collapsed_leaf))
  # ((aa,b)ab,(c,d)cd);

  # We can even load the collapsed version as a new tree.
  t2 = Tree(t.write(parser=1, is_leaf_fn=collapsed_leaf), parser=1)

  print(t2.to_str(props=['name'], compact=True))
  #    ╭╴ab╶┬╴aa
  # ╴⊗╶┤    ╰╴b
  #    ╰╴cd╶┬╴c
  #         ╰╴d

Another interesting use of this approach is to find the first matching
nodes in a given tree that match a custom set of criteria, without
browsing the whole tree structure.

Let's say we want to get all deepest nodes in a tree whose branch
length is defined and larger than one::

  t = Tree('(((a,b)ab:2,(c,d)cd:2)abcd:2,((e,f):2,g)efg:2);', parser=1)

  print(t.to_str(props=['name', 'dist'], compact=True))  # name and distance
  #                 ╭╴ab,2.0╶┬╴a,⊗
  #      ╭╴abcd,2.0╶┤        ╰╴b,⊗
  #      │          ╰╴cd,2.0╶┬╴c,⊗
  # ╴⊗,⊗╶┤                   ╰╴d,⊗
  #      │         ╭╴⊗,2.0╶┬╴e,⊗
  #      ╰╴efg,2.0╶┤       ╰╴f,⊗
  #                ╰╴g,⊗

  def processable_node(node):
      return node.dist and node.dist > 1

  for leaf in t.leaves(is_leaf_fn=processable_node):
      print(leaf.name)
  # Will print just these two "leaves" (according to processable_node):
  #   abcd
  #   efg


Iterators or lists?
~~~~~~~~~~~~~~~~~~~

The methods used to iterate over nodes are `python iterators
<https://docs.python.org/3/library/stdtypes.html#typesseq>`_. The
iterators produce only one element at a time, and thus are normally
faster and take less memory than lists.

Sometimes you will need a list instead, for example if you want to
refer to nodes that have appeared before in the iteration. In that
case, you can create it by adding ``list(...)`` to your call.

For example::

  leaves = list(t.leaves())  # constructs a list with all the leaves

The same is valid for :func:`traverse`, :func:`descendants`,
:func:`ancestors` and so on.


Finding nodes by their properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Both terminal and internal nodes can be located by searching along the
tree structure. Several methods are available:

.. table::

  ========================================= =========================================================================
  Method                                    Description
  ========================================= =========================================================================
  t.search_nodes(prop=value)                Iterator over nodes that have property prop equal to value, as name='A'
  t.search_descendants(prop=value)          Same, but only on descendants (excludes the node t itself)
  t.search_ancestors(prop=value)            Iterator over ancestor nodes
  t.search_leaves_by_name(name)             Iterator over leaf nodes matching a given name
  t.common_ancestor([node1, node2, node3])  Return the first internal node grouping node1, node2 and node3
  t[name]                                   Return the first node named name, same as next(t.search_nodes(name=name))
  ========================================= =========================================================================


Search all nodes matching a given criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A custom list of nodes matching a given name can be easily obtained
through the :func:`Tree.search_nodes` function.

::

  t = Tree('((H:1,I:1):0.5,A:1,(B:1,(C:1,D:1):0.5):0.5);')

  print(t)
  #  ╭─┬╴H
  # ─┤ ╰╴I
  #  ├╴A
  #  ╰─┬╴B
  #    ╰─┬╴C
  #      ╰╴D

  n1 = t['D']  # get node named 'D'

  # Get all nodes with distance=0.5
  nodes = list(t.search_nodes(dist=0.5))
  print(len(nodes), 'nodes have distance 0.5')

  # We can limit the search to leaves and node names
  n2 = next(t.search_leaves_by_name('D'))  # takes the first match
  print(n1 == n2)  # True


Search nodes matching a given criteria
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A limitation of the :func:`Tree.search_nodes` method is that you
cannot use complex conditional statements to find specific nodes. When
the search criteria is too complex, you may want to create your own search
function. For example::

  def search_by_size(node, size):
      """Yield nodes with a given number of leaves."""
      for n in node.traverse():
          if len(n) == size:
              yield n

  t = Tree()
  t.populate(40)

  # Get a list of all nodes containing 6 leaves.
  list(search_by_size(t, size=6))


Find the first common ancestor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Searching for the first common ancestor of a given set of nodes is a
handy way of finding internal nodes::

  t = Tree('(((a,b)ab,(c,d)cd:2)abcd,((e,f)ef,g)efg)root;', parser=1)

  print(t.to_str(props=['name'], compact=True))
  #              ╭╴ab╶┬╴a
  #       ╭╴abcd╶┤    ╰╴b
  #       │      ╰╴cd╶┬╴c
  # ╴root╶┤           ╰╴d
  #       │     ╭╴ef╶┬╴e
  #       ╰╴efg╶┤    ╰╴f
  #             ╰╴g

  ancestor = t.common_ancestor(['a', 'c', 'ab'])  # will be node abcd


Custom searching functions
^^^^^^^^^^^^^^^^^^^^^^^^^^

A limitation of the previous methods is that you cannot use complex
conditional statements to find specific nodes. However you can use
traversing methods and apply your custom filters::

  t = Tree('((H:0.3,I:0.1):0.5,A:1,(B:0.4,(C:1,D:1):0.5):0.5):0;')

  # Use a list comprehension, iterating with the traverse() method.
  matches = [node for node in t.traverse() if node.dist > 0.3]
  print(len(matches), 'nodes have distance > 0.3')

  # Or create a small function to filter your nodes.
  def condition(node):
      return node.dist > 0.3 and node.is_leaf

  matches2 = [node for node in t.traverse() if condition(node)]
  print(len(matches2), 'nodes have distance > 0.3 and are leaves')


Shortcuts
^^^^^^^^^

Finally, ETE implements a built-in method to find the first node
matching a given name, which is one of the most common tasks needed
for tree analysis. This can be done through the operator ``[]``. Thus,
``t['A']`` will return the first node whose name is "A" and that is
under the tree ``t``.

::

  t = Tree('((H,I),A,(B,(C,(J,(F,D)))));')

  # Get the node D in a simple way.
  D = t['D']

  # Get the path from D to the root (similar to list(t.ancestors())).
  path = []
  node = D
  while node.up:
      node = node.up
      path.append(node)

  print('There are', len(path)-1, 'nodes between D and the root.')


.. _check_monophyly:

Checking the monophyly of properties within a tree
--------------------------------------------------

Although monophyly is actually a phylogenetic concept used to refer to
a set of species that group exclusively together within a tree
partition, the idea can be easily used for any type of trees.

Therefore, we could consider that a set of values for a given node
property present in our tree is monophyletic, if such values group
exclusively together as a single tree partition. If not, the
corresponding relationship connecting such values (para- or
poly-phyletic) could be also be inferred.

The :func:`Tree.check_monophyly` method will do so when a given tree
is queried for any custom attribute.

::

  t = Tree('((((((a,e),i),o),h),u),((f,g),j));')
  print(t)
  #          ╭─┬╴a
  #        ╭─┤ ╰╴e
  #      ╭─┤ ╰╴i
  #    ╭─┤ ╰╴o
  #  ╭─┤ ╰╴h
  # ─┤ ╰╴u
  #  │ ╭─┬╴f
  #  ╰─┤ ╰╴g
  #    ╰╴j

  # We can check how, indeed, all vowels are not monophyletic in the previous
  # tree, but paraphyletic (monophyletic except for a group that is monophyletic):
  print(t.check_monophyly(values=['a', 'e', 'i', 'o', 'u'], prop='name'))
  # False (not monophyletic), 'paraphyletic' (type of group), {h} (the leaves not included)

  # However, the following set of vowels are monophyletic:
  print(t.check_monophyly(values=['a', 'e', 'i', 'o'], prop='name'))
  # True (it is monophyletic), 'monophyletic' (type of group), set() (no leaves left)

  # When a group is not monophyletic nor paraphyletic, it is called polyphyletic.
  print(t.check_monophyly(values=['i', 'h'], prop='name'))
  # False, 'polyphyletic', {e, a, o}

.. note::

   When the property is set to "species" in a :class:`PhyloTree` node,
   this method will correspond to the standard phylogenetic definition
   of monophyletic, paraphyletic, and polyphyletic.

Finally, the :func:`Tree.get_monophyletic` method is also provided,
which returns a list of nodes within a tree where a given set of
properties are monophyletic. Note that, although a set of values are
not monophyletic regarding the whole tree, several independent
monophyletic partitions could be found within the same topology.

In the following example we get all clusters within the same tree
exclusively grouping a custom set of annotations::

  t = Tree("((((((a,e),i),o),h),u),((f,g),(j,k)));")

  # Annotate the tree using external data.
  colors = {'a': 'green', 'e': 'green',
            'i': 'yellow', 'o': 'black', 'u':'purple',
            'f': 'yellow', 'g': 'green',
            'j': 'yellow', 'k': 'yellow'}

  for leaf in t:
      leaf.add_props(color=colors.get(leaf.name, 'none'))

  print(t.to_str(props=['name', 'color'], show_internal=False, compact=True))
  #          ╭─┬╴a,green
  #        ╭─┤ ╰╴e,green
  #      ╭─┤ ╰╴i,yellow
  #    ╭─┤ ╰╴o,black
  #  ╭─┤ ╰╴h,none
  # ─┤ ╰╴u,purple
  #  │ ╭─┬╴f,yellow
  #  ╰─┤ ╰╴g,green
  #    ╰─┬╴j,yellow
  #      ╰╴k,yellow

  # Obtain clusters exclusively green and yellow.
  print('Green-yellow clusters:')
  for node in t.get_monophyletic(prop='color', values=['green', 'yellow']):
      print()
      print(node.to_str(props=['name', 'color'], show_internal=False, compact=True))
  # Green-yellow clusters:
  #
  #  ╭─┬╴a,green
  # ─┤ ╰╴e,green
  #  ╰╴i,yellow
  #
  #  ╭─┬╴f,yellow
  # ─┤ ╰╴g,green
  #  ╰─┬╴j,yellow
  #    ╰╴k,yellow


.. _cache_node_content:

Caching tree content for faster lookup operations
-------------------------------------------------

If your program needs to access to the content of different nodes very
frequently, traversing the tree to get the leaves of each node over
and over will produce significant slowdowns in your algorithm.

ETE provides a convenient methods to cache frequently used data. The
method :func:`Tree.get_cached_content` returns a dictionary in which
keys are node instances and values represent the content of such
nodes. By default, "content" is understood as a set of leaf nodes.
After you retrieve this cached data, looking up the size or tip names
under a given node will be instantaneous.

Instead of caching the nodes themselves, specific properties can be
cached by setting a custom :attr:`prop` value.

::

  t = Tree()
  t.populate(50)

  node2leaves = t.get_cached_content()

  # Print the size of each node, without the need of traversing the subtrees every time.
  for n in t.traverse():
      print('Node %s contains %d tips.' % (n.name, len(node2leaves[n])))


Node annotation
---------------

Adding properties to the nodes of a tree is called tree annotation.
ETE stores the properties (annotations) of a node in a dictionary
called ``props``.

In a phylogenetic tree, the nodes (with their branches) often have
names, branch lengths, and branch supports. ETE provides a shortcut
for their corresponding properties :attr:`name`, :attr:`dist`, and
:attr:`support`, so instead of writing ``n.props.get('name')``, you
can write ``n.name``, and similarly for ``n.dist`` and ``n.support``.

The :func:`Tree.add_prop` and :func:`Tree.add_props` methods allow to
add extra properties (features, annotations) to any node. The first
one allows to add one one feature at a time, while the second one can
be used to add many features with the same call.

Similarly, :func:`Tree.del_prop` can be used to delete a property.

Example using annotations when working on a tree::

  t = Tree('((H:0.3,I:0.1),A:1,(B:0.4,(C:0.5,(J:1.3,(F:1.2,D:0.1)))));')

  print(t.to_str())
  #      ╭╴name=H,dist=0.3
  #   ╭──┤
  #   │  ╰╴name=I,dist=0.1
  #   │
  # ──┼╴name=A,dist=1.0
  #   │
  #   │  ╭╴name=B,dist=0.4
  #   ╰──┤
  #      │  ╭╴name=C,dist=0.5
  #      ╰──┤
  #         │  ╭╴name=J,dist=1.3
  #         ╰──┤
  #            │  ╭╴name=F,dist=1.2
  #            ╰──┤
  #               ╰╴name=D,dist=0.1

  # Reference some nodes (to use later).
  A = t['A']  # by name
  C = t['C']
  H = t['H']
  ancestor_JFC = t.common_ancestor(['J', 'F', 'C'])  # by common ancestor

  # Let's now add some custom features to our nodes.
  C.add_props(vowel=False, confidence=1.0)
  A.add_props(vowel=True, confidence=0.8)
  ancestor_JFC.add_props(nodetype='internal')
  H.add_props(vowel=False, confidence=0.3)

  for node in [A, C, H, ancestor_JFC]:
      print(f'Properties of {node.name}: {node.props}')

  # Let's annotate by looping over all nodes.
  # (Note that this overwrites the previous values.)
  for leaf in t:
      is_vowel = leaf.name in 'AEIOU'
      leaf.add_props(vowel=is_vowel, confidence=1)

  # Now we use this information to analyze the tree.
  print('This tree has', sum(1 for n in t.search_nodes(vowel=True)), 'vowel nodes')
  print('They are:', [leaf.name for leaf in t.leaves() if leaf.props['vowel']])

  # But features may refer to any kind of data, not only simple values.
  # For example, we can calculate some values and store them within nodes.
  #
  # Let's detect leaves under 'ancestor_JFC' with distance higher than 1.
  # Note that it traverses a subtree which starts from 'ancestor_JFC'.
  matches = [leaf for leaf in ancestor_JFC.leaves() if leaf.dist > 1.0]

  # And save this pre-computed information into the ancestor node.
  ancestor_JFC.add_props(long_branch_nodes=matches)

  # Prints the precomputed nodes
  print('These are the leaves under ancestor_JFC with long branches:',
        [n.name for n in ancestor_JFC.props['long_branch_nodes']])

  # We can also use the add_props() method to dynamically add new features.
  value = input('Custom label value: ')
  ancestor_JFC.add_props(label=value)
  print(f'Ancestor has now the "label" property with value "{value}":')
  print(ancestor_JFC.props)

The original newick format did not support adding extra features to a
tree. ETE includes support for the `New Hampshire eXtended format
<http://phylosoft.org/NHX>`_ (NHX), which uses the original newick
standard and adds the possibility of saving additional data related to
each tree node.

Here is an example of a extended newick representation in which extra
information is added to an internal node::

 (A:0.3,(B:0.7,(D:0.6,G:0.1):0.6[&&NHX:conf=0.1:name=internal]):0.5);

As you can see, extra node features in the NHX format are enclosed
between brackets. ETE is able to read and write features using this
format, however, the encoded information is expected to be exportable
as plain text.

The NHX format is automatically detected when reading a newick file,
and the detected node properties are added. You can access the
information by using ``node.props[prop_name]``.

Similarly, properties added to a tree can be included within the
normal newick representation using the NHX notation. For this, you can
call the :func:`Tree.write` method using the :attr:`props` argument,
which is expected to be a list with the feature names that you want to
include in the newick string. Use :attr:`props=None`) to include all
the node's data into the newick string.

::

  t = Tree('((H:0.3,I:0.1),A:1,(B:0.4,(C:0.5,(J:1.3,(F:1.2,D:0.1)))));')

  print(t)
  #  ╭─┬╴H
  # ─┤ ╰╴I
  #  ├╴A
  #  ╰─┬╴B
  #    ╰─┬╴C
  #      ╰─┬╴J
  #        ╰─┬╴F
  #          ╰╴D

  # Add some more properties to leaves:
  for leaf in t:
      is_vowel = leaf.name in 'AEIOU'
      leaf.add_props(vowel=is_vowel, confidence=1)

  print('NHX notation including vowel and confidence properties:')
  print(t.write(props=['vowel']))

  print('NHX notation including all data in the nodes:')
  print(t.write(props=None))

To read NHX notation you can just read it as a normal newick::

  # Load the NHX example from https://www.phylosoft.org/NHX/
  nw = """
  (((ADH2:0.1[&&NHX:S=human:E=1.1.1.1], ADH1:0.11[&&NHX:S=human:E=1.1.1.1]):0.05
  [&&NHX:S=Primates:E=1.1.1.1:D=Y:B=100], ADHY:0.1[&&NHX:S=nematode:
  E=1.1.1.1],ADHX:0.12[&&NHX:S=insect:E=1.1.1.1]):0.1[&&NHX:S=Metazoa:
  E=1.1.1.1:D=N], (ADH4:0.09[&&NHX:S=yeast:E=1.1.1.1],ADH3:0.13[&&NHX:S=yeast:
  E=1.1.1.1], ADH2:0.12[&&NHX:S=yeast:E=1.1.1.1],ADH1:0.11[&&NHX:S=yeast:E=1.1.1.1]):0.1
  [&&NHX:S=Fungi])[&&NHX:E=1.1.1.1:D=N];
  """

  t = Tree(nw)

  print(t.to_str(props=['name', 'S'], compact=True))
  #                  ╭╴⊗,Primates╶┬╴ADH2,human
  #      ╭╴⊗,Metazoa╶┤            ╰╴ADH1,human
  #      │           ├╴ADHY,nematode
  # ╴⊗,⊗╶┤           ╰╴ADHX,insect
  #      │         ╭╴ADH4,yeast
  #      ╰╴⊗,Fungi╶┼╴ADH3,yeast
  #                ├╴ADH2,yeast
  #                ╰╴ADH1,yeast

  # And access the node's properties.
  print('S property for the nodes that have it:')
  for n in t.traverse():
      if 'S' in n.props:
         print('  %s: %s' % (n.name if n.name else n.id, n.props['S']))
  # S property for the nodes that have it:
  #   [0]: Metazoa
  #   [1]: Fungi
  #   [0, 0]: Primates
  #   ADHY: nematode
  #   ADHX: insect
  #   ADH4: yeast
  #   ADH3: yeast
  #   ADH2: yeast
  #   ADH1: yeast
  #   ADH2: human
  #   ADH1: human


.. _robinson_foulds:

Comparing trees
---------------

Distances between trees
~~~~~~~~~~~~~~~~~~~~~~~

The :func:`Tree.compare` function allows to calculate distances
between two trees based on any node property (i.e. name, species,
other tags) using Robinson-Foulds and edge compatibility distances. It
automatically handles differences in tree sizes, shared nodes and
duplicated feature names.

Its result is a dictionary with the following contents:

- result['rf'] = Robinson-Foulds distance between the two trees.
  (Average of Robinson-Foulds distances if target tree contained
  duplication and was split in several subtrees.)
- result['max_rf'] = Maximum Robinson-Foulds distance expected for this comparison.
- result['norm_rf'] = Normalized Robinson-Foulds distance (from 0 to 1).
- result['effective_tree_size'] = Size of the compared trees, which
  are pruned to the common shared nodes.
- result['ref_edges_in_source'] = Compatibility score of the target
  tree with respect to the source tree (how many edges in reference
  are found in the source).
- result['source_edges_in_ref'] = Compatibility score of the source
  tree with respect to the reference tree (how many edges in source
  are found in the reference).
- result['source_subtrees'] = Number of subtrees in the source tree (1
  if it does not contain duplications).
- result['common_edges'] = Set of common edges between source tree and
  reference.
- result['source_edges'] = Set of edges found in the source tree.
- result['ref_edges'] = Set of edges found in the reference tree.
- result['treeko_dist'] = TreeKO speciation distance for comparisons
  including duplication nodes.


Robinson-Foulds distance
~~~~~~~~~~~~~~~~~~~~~~~~

Two tree topologies can be compared using the Robinson-Foulds (RF)
metric. The method :func:`Tree.robinson_foulds` available for any ETE
tree node allows to:

- Compare two tree topologies by their name labels (default) or any
  other annotated feature in the tree.
- Compare topologies of different size and content. When two trees
  contain a different set of labels, only shared leaves will be used.
- Examine size and content of matching and missing partitions. Since
  the method returns the list of partitions found in both trees,
  details about matching partitions can be obtained easily.
- Discard edges from the comparison based on their support value.
- Automatically expand polytomies (multifurcations) in source and
  target trees.

There is also a command line tool providing most used features:
``ete compare``.

The following example shows several of the above mentioned features::

  t1 = Tree('(((a,b),c),((e,f),g));')
  t2 = Tree('(((a,c),b),((e,f),g));')

  print(t1)
  print(t2)
  #    ╭─┬╴a
  #  ╭─┤ ╰╴b
  # ─┤ ╰╴c
  #  │ ╭─┬╴e
  #  ╰─┤ ╰╴f
  #    ╰╴g
  #    ╭─┬╴a
  #  ╭─┤ ╰╴c
  # ─┤ ╰╴b
  #  │ ╭─┬╴e
  #  ╰─┤ ╰╴f
  #    ╰╴g

  rf, rf_max, common, parts_t1, parts_t2, _, _ = t1.robinson_foulds(t2)

  print(f'RF distance is {rf} over a total of {rf_max}')
  print('Partitions in tree2 that were not found in tree1:', parts_t1 - parts_t2)
  print('Partitions in tree1 that were not found in tree2:', parts_t2 - parts_t1)
  # RF distance is 2 over a total of 8
  # Partitions in tree2 that were not found in tree1: {('a', 'b')}
  # Partitions in tree1 that were not found in tree2: {('a', 'c')}

We can also compare trees sharing only part of their labels::

  t1 = Tree('(((a,b),c),((e,f),g));')
  t2 = Tree('(((a,c),b),(g,H));')

  print(t1)
  print(t2)
  #    ╭─┬╴a
  #  ╭─┤ ╰╴b
  # ─┤ ╰╴c
  #  │ ╭─┬╴e
  #  ╰─┤ ╰╴f
  #    ╰╴g
  #    ╭─┬╴a
  #  ╭─┤ ╰╴c
  # ─┤ ╰╴b
  #  ╰─┬╴g
  #    ╰╴H

  rf, rf_max, common, parts_t1, parts_t2, _, _ = t1.robinson_foulds(t2)

  # Same distance holds even for partially overlapping trees.
  print(f'RF distance is {rf} over a total of {rf_max}')
  print('Partitions in tree2 that were not found in tree1:', parts_t1 - parts_t2)
  print('Partitions in tree1 that were not found in tree2:', parts_t2 - parts_t1)
  # RF distance is 2 over a total of 4
  # Partitions in tree2 that were not found in tree1: {('a', 'b')}
  # Partitions in tree1 that were not found in tree2: {('a', 'c')}


.. _sec:modifying-tree-topology:

Modifying tree topology
-----------------------

Creating trees from scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If no arguments are passed to the :class:`Tree` class constructor,
an empty tree node will be returned. Such an orphan node can be used
to populate a tree from scratch. For this, the :attr:`Tree.up`,
and :attr:`Tree.children` attributes should never be used (unless
it is strictly necessary). Instead, several methods exist to
manipulate the topology of a tree:

.. autosummary::

   Tree.populate
   Tree.add_child
   Tree.add_sister
   Tree.delete
   Tree.detach

As an example of how to use them::

  t = Tree()  # create an empty tree

  A = t.add_child(name='A')  # add new child to the tree root and return it
  B = t.add_child(name='B')

  C = A.add_child(name='C')  # add new child to one of the branches
  D = C.add_sister(name='D')  # add a second child to same branch as before
  # Note that the last one did it by using a sister as the starting point.

  R = A.add_child(name='R')  # add a third child (multifurcations are ok)

  # Add 6 random leaves to the R branch, with names 'r1' to 'r6'.
  R.populate(6, names_library=['r1', 'r2', 'r3', 'r4', 'r5', 'r6'])

  print(t)
  #    ╭╴C
  #  ╭─┼╴D
  #  │ ╰─┬╴r6
  #  │   ╰─┬╴r5
  # ─┤     ╰─┬╴r4
  #  │       ╰─┬╴r3
  #  │         ╰─┬╴r2
  #  │           ╰╴r1
  #  ╰╴B

A common use of the :func:`populate` method is to quickly create
example trees from scratch. Here we create a random tree with 100
leaves::

  t = Tree()
  t.populate(100)


How to delete/eliminate or remove/detach nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In ETE there is a difference between detaching and deleting a node.

Detaching disconnects a complete partition from the tree structure, so
all its descendants are also disconnected from the tree. There are two
methods to perform this action: :func:`Tree.remove_child` and
:func:`Tree.detach`.

In contrast, deleting a node means eliminating such node without
affecting its descendants. Children from the deleted node are
automatically connected to the next possible parent.

This is better understood with the following example::

  t = Tree('((((H,K)D,(F,I)G)B,E)A,((L,(N,Q)O)J,(P,S)M)C);', parser=1)

  print(t.to_str(props=['name'], compact=True))
  #            ╭╴D╶┬╴H
  #        ╭╴B╶┤   ╰╴K
  #    ╭╴A╶┤   ╰╴G╶┬╴F
  #    │   │       ╰╴I
  # ╴⊗╶┤   ╰╴E
  #    │   ╭╴J╶┬╴L
  #    ╰╴C╶┤   ╰╴O╶┬╴N
  #        │       ╰╴Q
  #        ╰╴M╶┬╴P
  #            ╰╴S

  # Get specific nodes.
  G = t['G']
  J = t['J']
  C = t['C']

  # If we REMOVE the node J from the tree, the whole partition under J will
  # be detached from the tree and it will be considered an independent tree.
  # We can do the same with either J.detach() or C.remove_child(J).
  removed_node = J.detach()  # same as C.remove_child(J)

  # Tree after REMOVING the node J:
  print(t.to_str(props=['name'], compact=True))
  #            ╭╴D╶┬╴H
  #        ╭╴B╶┤   ╰╴K
  #    ╭╴A╶┤   ╰╴G╶┬╴F
  # ╴⊗╶┤   │       ╰╴I
  #    │   ╰╴E
  #    ╰╴C╶╌╴M╶┬╴P
  #            ╰╴S

  # However, if we DELETE the node G, only G will be eliminated from the
  # tree, and all its descendants will then hang from the next upper node.
  G.delete()

  # Tree after DELETING the node G:
  print(t.to_str(props=['name'], compact=True))
  #            ╭╴D╶┬╴H
  #        ╭╴B╶┤   ╰╴K
  #    ╭╴A╶┤   ├╴F
  # ╴⊗╶┤   │   ╰╴I
  #    │   ╰╴E
  #    ╰╴C╶╌╴M╶┬╴P
  #            ╰╴S


Pruning trees
-------------

Pruning a tree means to obtain the topology that connects a certain
group of items by removing the unnecessary edges. To facilitate this
task, ETE implements the :func:`Tree.prune` method, which can be used
by providing the list of terminal and/or internal nodes that must be
kept in the tree.

The `preserve_branch_length` flag allows to remove nodes from a tree
while keeping original distances among remaining nodes.

Example::

  t = Tree('((((H,K),(F,I)G),E),((L,(N,Q)O),(P,S)));', parser=1)

  print(t)
  #      ╭─┬╴H
  #    ╭─┤ ╰╴K
  #  ╭─┤ ╰─┬╴F
  #  │ │   ╰╴I
  # ─┤ ╰╴E
  #  │ ╭─┬╴L
  #  ╰─┤ ╰─┬╴N
  #    │   ╰╴Q
  #    ╰─┬╴P
  #      ╰╴S

  # Prune the tree in order to keep only some leaf nodes.
  t.prune(['H', 'F', 'E', 'Q', 'P'])

  # Pruned tree:
  print(t)
  #    ╭─┬╴H
  #  ╭─┤ ╰╴F
  # ─┤ ╰╴E
  #  ╰─┬╴Q
  #    ╰╴P

In the next section we will see how to re-create the same tree again.


Concatenating trees
-------------------

Given that all tree nodes share the same basic properties, they can be
connected freely. In fact, any node can add a whole subtree as a
child, so we can actually *cut & paste* partitions.

To do so, you can call the :func:`Tree.add_child` method using another tree
node as first argument. If such a node is the root node of a
different tree, you will concatenate the two tree structures.

.. warning::
  This kind of operation may result in circular tree structures if you
  add a node's ancestor as one of its descendants. ETE performs some
  basic checks, but a full check would affect seriously the
  performance. For this reason, users themselves should take care not
  to create circular structures by mistake.

::

  t1 = Tree('(A,(B,C));')
  t2 = Tree('((D,E),(F,G));')
  t3 = Tree('(H,((I,J),(K,L)));')

  print(t1)
  print(t2)
  print(t3)
  # ─┬╴A
  #  ╰─┬╴B
  #    ╰╴C
  #  ╭─┬╴D
  # ─┤ ╰╴E
  #  ╰─┬╴F
  #    ╰╴G
  #  ╭╴H
  # ─┤ ╭─┬╴I
  #  ╰─┤ ╰╴J
  #    ╰─┬╴K
  #      ╰╴L

  # Add two other trees as children of node A.
  A = t1['A']

  A.add_child(t2)
  A.add_child(t3)

  # Resulting concatenated tree:
  print(t1)
  #      ╭─┬╴D
  #    ╭─┤ ╰╴E
  #    │ ╰─┬╴F
  #  ╭─┤   ╰╴G
  #  │ │ ╭╴H
  #  │ ╰─┤ ╭─┬╴I
  # ─┤   ╰─┤ ╰╴J
  #  │     ╰─┬╴K
  #  │       ╰╴L
  #  ╰─┬╴B
  #    ╰╴C


.. _sec:tree-rooting:

.. _copying_trees:

Copying (duplicating) trees
---------------------------

ETE provides several strategies to clone tree structures. The method
:func:`Tree.copy()` can be used to produce a new independent tree
object with the exact same topology and features as the original.
However, as trees may involve many intricate levels of branches and
nested features, 4 different methods are available to create a tree
copy:

 - "newick": Tree topology, node names, branch lengths and branch
   support values will be copied as represented in the newick string
   This method is based on newick format serialization works very fast
   even for large trees.

 - "newick-extended": Tree topology and all node features will be
   copied based on the extended newick format representation. Only
   node features will be copied, thus excluding other node
   attributes. As this method is also based on newick serialisation,
   features will be converted into text strings when making the
   copy. Performance will depend on the tree size and the number and
   type of features being copied.

 - "cpickle": This is the default method. The whole node structure and
   its content will be cloned based on the cPickle object
   serialization python approach.  This method is slower, but
   recommended for full tree copying.

 - "deepcopy": The whole node structure and its content is copied
   based on the standard "copy" Python functionality. This is the
   slowest method, but it allows to copy very complex objects even
   when attributes point to lambda functions.

Example::

   t = Tree('((A,B)Internal_1:0.7,(C,D)Internal_2:0.5)root:1.3;', parser=1)

   # Add a custom annotation to the node named A.
   t['A'].add_props(label='custom value')

   # Add a complex feature to the A node, consisting of a list of lists.
   t['A'].add_props(complex=[[0,1], [2,3]])

   print(t.to_str())
   #                                                ╭╴name=A,label=custom value,complex=[[0, 1], [2, 3]]
   #                     ╭╴name=Internal_1,dist=0.7╶┤
   #                     │                          ╰╴name=B
   # ╴name=root,dist=1.3╶┤
   #                     │                          ╭╴name=C
   #                     ╰╴name=Internal_2,dist=0.5╶┤
   #                                                ╰╴name=D

   # Newick copy will lose custom node annotations, complex features,
   # but not names and branch values.

   print(t.copy('newick').to_str())
   #                                                ╭╴name=A
   #                     ╭╴name=Internal_1,dist=0.7╶┤
   #                     │                          ╰╴name=B
   # ╴name=root,dist=1.3╶┤
   #                     │                          ╭╴name=C
   #                     ╰╴name=Internal_2,dist=0.5╶┤
   #                                                ╰╴name=D

   # Extended newick copy will transfer custom annotations as text
   # strings, so complex features are lost.

   print(t.copy('newick-extended').to_str())
   #                              ╭╴name=A,complex=_0_ 1_|_2_ 3_,label=custom value
   #   ╭╴name=Internal_1,dist=0.7╶┤
   #   │                          ╰╴name=B
   # ──┤
   #   │                          ╭╴name=C
   #   ╰╴name=Internal_2,dist=0.5╶┤
   #                              ╰╴name=D

   # The default pickle method will produce an exact clone of the
   # original tree, where features are duplicated keeping their
   # python data type.

   print(t.copy().to_str())
   #                                                ╭╴name=A,label=custom value,complex=[[0, 1], [2, 3]]
   #                     ╭╴name=Internal_1,dist=0.7╶┤
   #                     │                          ╰╴name=B
   # ╴name=root,dist=1.3╶┤
   #                     │                          ╭╴name=C
   #                     ╰╴name=Internal_2,dist=0.5╶┤
   #                                                ╰╴name=D


.. _resolve_polytomy:

Solving multifurcations
-----------------------

When a tree contains a polytomy (a node with more than 2 children),
the method :func:`resolve_polytomy` can be used to convert the node
into an arbitrarily bifurcated structure. This is really not a solution
for the polytomy but it allows to export the tree as a strictly
bifurcated newick structure, which is a requirement for some external
software.

The method can be used on a very specific node while keeping the rest
of the tree intact by disabling the :attr:`recursive` flag.

Example::

  t = Tree('(((a,b,c),(d,e,f,g)),(h,i,j));')

  print(t)
  #      ╭╴a
  #    ╭─┼╴b
  #  ╭─┤ ╰╴c
  #  │ │ ╭╴d
  #  │ ╰─┼╴e
  # ─┤   ├╴f
  #  │   ╰╴g
  #  │ ╭╴h
  #  ╰─┼╴i
  #    ╰╴j

  polynode = t.common_ancestor(['a', 'b'])
  polynode.resolve_polytomy(descendants=False)

  print(t)
  #      ╭─┬╴a
  #    ╭─┤ ╰╴b
  #  ╭─┤ ╰╴c
  #  │ │ ╭╴d
  #  │ ╰─┼╴e
  # ─┤   ├╴f
  #  │   ╰╴g
  #  │ ╭╴h
  #  ╰─┼╴i
  #    ╰╴j

  t.resolve_polytomy(descendants=True)

  print(t)
  #      ╭─┬╴a
  #    ╭─┤ ╰╴b
  #    │ ╰╴c
  #  ╭─┤   ╭─┬╴d
  #  │ │ ╭─┤ ╰╴e
  # ─┤ ╰─┤ ╰╴f
  #  │   ╰╴g
  #  │ ╭─┬╴h
  #  ╰─┤ ╰╴i
  #    ╰╴j


Tree rooting
------------

Tree rooting is understood as the technique by with a given tree is
conceptually polarized from more basal to more terminal nodes.

In phylogenetics, for instance, this a crucial step prior to the
interpretation of trees, since it will determine the evolutionary
relationships among the species involved.

The concept of rooted trees is different than just having a root node,
which is always necessary to handle a tree data structure. Usually,
the way in which a tree is differentiated between rooted and unrooted,
is by counting the number of branches of the current root node. Thus,
if the root node has more than two child branches, the tree is
considered unrooted. By contrast, when only two main branches exist
under the root node, the tree is considered rooted.

Having an unrooted tree means that any internal branch within the tree
could be regarded as the root node, and there is no conceptual reason
to place the root node where it is placed at the moment. Therefore, in
an unrooted tree, there is no information about which internal nodes
are more basal than others.

By setting the root node between a given edge/branch of the tree
structure the tree is polarized, meaning that the two branches under
the root node are the most basal nodes. In practice, this is usually
done by setting an **outgroup node**, which would represent one of
these main root branches. The second one will be, obviously, the
brother node. When you set an outgroup on unrooted trees, the
multifurcations at the current root node are solved.

In order to root an unrooted tree or re-root a tree structure, ETE
implements the :func:`Tree.set_outgroup` method, which is present in
any tree node instance. Similarly, the :func:`Tree.unroot` method can
be used to perform the opposite action.

Example::

  # Create an unrooted tree. Note that 3 branches hang from the root
  # node. This usually means that no information is available about
  # which of the nodes is more basal.
  t = Tree('(A,(H,F),(B,(E,D)));')

  print(t)
  #  ╭╴A
  # ─┼─┬╴H
  #  │ ╰╴F
  #  ╰─┬╴B
  #    ╰─┬╴E
  #      ╰╴D

  # Let's define the ancestor of E and D as the tree outgroup.
  # Of course, the definition of an outgroup will depend on user criteria.
  ancestor = t.common_ancestor(['E', 'D'])
  t.set_outgroup(ancestor)

  print(t)  # tree rooted at E and D's ancestor is more basal that the others
  #  ╭─┬╴E
  # ─┤ ╰╴D
  #  ╰─┬╴B
  #    ╰─┬╴A
  #      ╰─┬╴H
  #        ╰╴F

  # Note that setting a different outgroup, a different interpretation
  # of the tree is possible.
  t.set_outgroup(t['A'])

  print(t)  # tree rooted at a terminal node
  #  ╭╴A
  # ─┤ ╭─┬╴H
  #  ╰─┤ ╰╴F
  #    ╰─┬╴B
  #      ╰─┬╴E
  #        ╰╴D

Note that although **rooting** is usually regarded as a whole-tree
operation, ETE allows to root subparts of the tree without affecting
its parent tree structure::

  t = Tree('(((A,C),((H,F),(L,M))),((B,(J,K)),(E,D)));')

  print(t)
  #    ╭─┬╴A
  #  ╭─┤ ╰╴C
  #  │ │ ╭─┬╴H
  #  │ ╰─┤ ╰╴F
  # ─┤   ╰─┬╴L
  #  │     ╰╴M
  #  │ ╭─┬╴B
  #  ╰─┤ ╰─┬╴J
  #    │   ╰╴K
  #    ╰─┬╴E
  #      ╰╴D

  # Each main branch of the tree is independently rooted.
  node1 = t.common_ancestor(['A', 'H'])
  node2 = t.common_ancestor(['B', 'D'])

  node1.set_outgroup('H')
  node2.set_outgroup('E')

  print(t)  # tree after rooting each node independently
  #    ╭╴H
  #  ╭─┤ ╭╴F
  #  │ ╰─┤ ╭─┬╴L
  # ─┤   ╰─┤ ╰╴M
  #  │     ╰─┬╴A
  #  │       ╰╴C
  #  ╰─┬╴E
  #    ╰─┬╴D
  #      ╰─┬╴B
  #        ╰─┬╴J
  #          ╰╴K


Working with branch distances
-----------------------------

The branch length between one node an its parent is encoded as the
:attr:`Tree.dist` property. Together with tree topology, branch
lengths define the relationships among nodes.


Getting distances between nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`Tree.get_distance` method can be used to calculate the
distance between two connected nodes. The method accepts as arguments
two descendant nodes.

Example::

  # Create a tree with branch lenght information.
  nw = """(((A:1,B:2):1,C:3):1,
  (((((D:0.5,I:0):0,F:0):0,G:0):0,H:0):0,E:0.2):3):2;
  """

  t = Tree(nw)

  print(t)
  print(t.to_str(props=['dist'], compact=True))
  #    ╭─┬╴A
  #  ╭─┤ ╰╴B
  #  │ ╰╴C
  #  │       ╭─┬╴D
  # ─┤     ╭─┤ ╰╴I
  #  │   ╭─┤ ╰╴F
  #  │ ╭─┤ ╰╴G
  #  ╰─┤ ╰╴H
  #    ╰╴E
  #            ╭╴1.0╶┬╴1.0
  #      ╭╴1.0╶┤     ╰╴2.0
  #      │     ╰╴3.0
  #      │                       ╭╴0.0╶┬╴0.5
  # ╴2.0╶┤                 ╭╴0.0╶┤     ╰╴0.0
  #      │           ╭╴0.0╶┤     ╰╴0.0
  #      │     ╭╴0.0╶┤     ╰╴0.0
  #      ╰╴3.0╶┤     ╰╴0.0
  #            ╰╴0.2

  # Calculate distance between two nodes.
  print('The distance between A and C is', t.get_distance('A', 'C'))
  # The distance between A and C is 5.0

  # Calculate the toplogical distance (number of nodes in between).
  print('The number of nodes between A and D is',
        t.get_distance('A', 'D', topological=True))
  # The number of nodes between A and D is 9

Additionally to this, ETE incorporates two more methods to calculate
the most distant node from a given point in a tree. You can use the
:func:`Tree.get_farthest_node` method to retrieve the most distant
point from a node within the whole tree structure. Alternatively,
:func:`Tree.get_farthest_leaf` will return the most distant descendant
(always a leaf). If more than one node matches the farthest distance,
the first occurrence is returned.

Distance between nodes can also be computed as the number of nodes
between them (considering all branch lengths equal to 1.0). To do so,
use ``topological=True`` as an argument::

  # Find the farthest node from E within the whole structure.
  farthest, dist = t['E'].get_farthest_node()

  print('The farthest node from E is', farthest.name, 'with dist', dist)
  # The farthest node from E is B with dist 7.2

  # Find the farthest node from E within the whole structure,
  # regarding the number of nodes in between as distance value.
  farthest, dist = t['E'].get_farthest_node(topological=True)

  print('The farthest (topologically) node from E is',
        farthest.name, 'with', dist, 'nodes in between')
  # The farthest (topologically) node from E is D with 4.0 nodes in between


.. _sub:getting-midpoint-outgroup:

Getting midpoint outgroup
-------------------------

In order to obtain a balanced rooting of the tree, you can set as the
tree outgroup that partition which splits the tree into two equally
distant clusters (using branch lengths). This is called the midpoint
outgroup.

The :func:`Tree.get_midpoint_outgroup` method will return the outgroup
partition that splits the current node into two balanced branches in
terms of node distances.

Example::

  # Generate a random tree.
  t = Tree()
  t.populate(15)

  print(t)  # will look more or less like...
  #    ╭─┬╴f
  #  ╭─┤ ╰─┬╴g
  #  │ │   ╰╴h
  #  │ ╰─┬╴i
  #  │   ╰╴j
  # ─┤   ╭─┬╴k
  #  │   │ ╰─┬╴l
  #  │ ╭─┤   ╰╴m
  #  │ │ │ ╭─┬╴n
  #  ╰─┤ ╰─┤ ╰╴o
  #    │   ╰─┬╴a
  #    │     ╰╴b
  #    ╰─┬╴c
  #      ╰─┬╴d
  #        ╰╴e

  # Calculate the midpoint node.
  R = t.get_midpoint_outgroup()

  # And set it as tree outgroup.
  t.set_outgroup(R)

  print(t)  # will look more or less like...
  #      ╭─┬╴k
  #      │ ╰─┬╴l
  #    ╭─┤   ╰╴m
  #    │ │ ╭─┬╴n
  #  ╭─┤ ╰─┤ ╰╴o
  #  │ │   ╰─┬╴a
  #  │ │     ╰╴b
  # ─┤ ╰─┬╴c
  #  │   ╰─┬╴d
  #  │     ╰╴e
  #  │ ╭─┬╴f
  #  ╰─┤ ╰─┬╴g
  #    │   ╰╴h
  #    ╰─┬╴i
  #      ╰╴j
