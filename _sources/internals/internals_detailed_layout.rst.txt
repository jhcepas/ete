Detailed Layout
===============

There are several parts to the project.

The module ``ete4`` has submodules to create trees (``core/tree.pyx``)
and parse newicks (``parser/newick.pyx``) and other formats, do
tree-related operations (``core/operations.pyx``), and more.

The ``smartview`` module contains an http server based on `bottle
<https://bottlepy.org/>`_ (in ``explorer.py``). It exposes in an api
all the operations that can be done to manage and represent the trees,
and also provides access to ``gui.html``, which shows a gui on the
browser to explore the trees. It uses the code in ``gui.js`` and all the
other imported js modules in the same directory.

It also serves an entry page with a short description and an easy way
to upload new trees, ``upload.html`` (which uses ``upload.js``).

There are tests for most of the python code in ``tests``. They can be
run with pytest.

A more complete layout with the relevant parts for tree exploration::

  README.md
  pyproject.toml  # build system (see PEP 518)
  setup.py
  ete4/  # the module directory
    core/
      tree.pyx  # the Tree class
      operations.pyx  # tree-related operations
      text_viz.py  # text visualization of trees
    parser/
      newick.pyx  # newick parser
      nexus.py  # functions to handle trees in the nexus format
      ete_format.py  # ete's own optimized format
      indent.py  # parser for indented trees
    smartview/
      draw.py  # drawing classes and functions to represent a tree
      explorer.py  # http server that exposes an api to interact with trees
      layout.py
      faces.py
      coordinates.py
      graphics.py
      static/  # files served for the gui and uploading
        gui.html  # entry point for the interactive visualization (html)
        gui.css
        upload.html  # landing page with the upload tree interface
        upload.css
        images/
          icon.png
          spritesheet.png
          spritesheet.json
        js/
          gui.js  # entry point for the interactive visualization (js)
          menu.js  # initialize the menus
          draw.js  # call to the api to get drawing items and convert to svg
          pixi.js
          minimap.js  # handle the current tree view on the minimap
          zoom.js
          drag.js
          download.js
          contextmenu.js  # what happens when one right-clicks on the tree
          events.js  # hotkeys, mouse events
          search.js
          collapse.js
          label.js
          tag.js
          api.js  # handle calls to the server's api
          upload.js  # upload trees to the server
        external/  # where we keep a copy of external libraries
          readme.md  # description of where to find them
          tweakpane.min.js
          sweetalert2.min.js
          pixi.min.mjs
  tests/  # tests for the existing functionality, to run with pytest
  docs/  # documentation
