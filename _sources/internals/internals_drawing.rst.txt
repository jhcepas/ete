Drawing
=======

This document explains the internal details about how ETE draws trees
on the browser.

The :mod:`smartview` module contains a :func:`draw` function that
takes mainly a tree and a viewport, and can produce a list of
graphical commands.


Graphical Elements
------------------

The :func:`draw` function is a generator that yields graphical
commands. They are mainly a description of basic graphic items, which
are lists that look like::

  ['hz-line', [0.0, 0.5], [8.0, 0.5], [], '']

It always starts with the name of the graphical command, followed by
its parameters. (This is similar to creating a `DSL
<https://en.wikipedia.org/wiki/Domain-specific_language>`_ with
functions that draw, and which will be interpreted in the frontend).


gui.js
------

When the browser opens a tree, it will see the file
``ete4/smartview/static/gui.html``. This is a simple web page, which
loads ``js/gui.js`` to provide all the functionality.

The code in ``gui.js`` loads many different modules to visualize and
interact with trees. It contains an object ``view`` (with information
on the current view of the tree) which is a sort of global variable
repository. This is mainly used in the menus to expose and control its
values.


Drawing areas
-------------

They can be seen in ``gui.html``. They are::

   div_tree
   div_aligned
   div_legend
   div_minimap


API calls
---------

When starting to browse a tree, we see this order of :doc:`api calls
<internals_api>`::

  /trees

  /trees/tree-1/layouts

  /trees/tree-1/style?active=["basic","Example+layout"]

  /trees/tree-1/size

  /trees/tree-1/nodecount

  /trees/tree-1/properties

  /static/images/spritesheet.json

  /static/images/spritesheet.png

  /trees/tree-1/draw?shape=rectangular&node_height_min=30&content_height_min=4&zx=1.2&zy=362.7&x=-0.3&y=-0.1&w=3.3&h=3.3&collapsed_shape=skeleton&collapsed_ids=[]&layouts=["basic","Example+layout"]&labels=[]

and from that moment, when moving and zooming the tree, typically many
similar draw calls like::

  /trees/tree-1/draw?shape=rectangular&node_height_min=30&content_height_min=4&zx=1.4[...]

And there are different kind of api calls made when editing or changing
the tree in different ways.


Code paths
~~~~~~~~~~

The initial api calls come from the following places in the code:

::

  gui.js
    main
      init_trees  # /trees
      populate_layouts  # /trees/tree-1/layouts
      set_tree_style  # /trees/tree-1/style?active=["basic","Example+layout"]
      set_consistent_values  # /trees/tree-1/size
      store_node_count  # /trees/tree-1/nodecount
      store_node_properties  # /trees/tree-1/properties
      init_pixi  # /static/images/spritesheet.json /static/images/spritesheet.png
      update  # (in draw.js)
        draw_tree  # /trees/tree-1/draw?[...]
