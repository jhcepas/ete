Overview
========

Most of the code is written in python. For efficiency reasons, the
``core.tree``, ``core.operations`` and ``parser.newick`` submodules
are written in `cython <https://cython.org/>`_, which makes the parser
about twice as fast while making the final tree take about half the
memory.

When exploring trees ("smartview"), there is an http server
(``ete4/smartview/explorer.py``) that exposes as an api the graphical
capabilities of ETE and also serves a gui to explore the trees
interactively by making use of that api.

The server acts as a *backend* to the requests made by the *frontend*,
which is written in javascript.


Project Layout
--------------

The principal files of the project are::

  ete4/  # the module directory
    core/
      tree.pyx  # the Tree class and related functions
      operations.pyx  # tree-related operations
    parser/
      newick.pyx  # newick parser
    smartview/
      draw.py  # drawing classes and functions to represent a tree
      explorer.py  # http server that exposes an api to interact with trees
      static/
        gui.html  # entry point for the interactive visualization (html)
        js/
          gui.js  # entry point for the interactive visualization (js)

For a more detailed view, see the :doc:`detailed layout
<internals_detailed_layout>`.
