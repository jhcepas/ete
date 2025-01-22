API
===

The server exposes a `RESTful API
<https://en.wikipedia.org/wiki/Representational_state_transfer#Applied_to_web_services>`_,
with the following endpoints (defined in ``explorer.py``)::

  GET:
  /api  # get info about the api endpoints
  /trees  # get info about all the existing trees
  /trees/<name>  # get info about the given tree
  /trees/<name>/draw  # get graphical commands to draw the tree
  /trees/<name>/layouts  # get available layouts for the tree
  /trees/<name>/style  # get tree style
  /trees/<name>/newick  # get newick representation
  /trees/<name>/size  # get inner width and height of the full tree
  /trees/<name>/properties  # names of extra ones defined in any node
  /trees/<name>/nodecount  # total count of nodes and leaves
  /trees/<name>/search  # search for nodes

  PUT:
  /trees/<name>/sort  # sort branches
  /trees/<name>/set_outgroup  # set node as outgroup (1st child of root)
  /trees/<name>/move  # move branch
  /trees/<name>/remove  # prune branch
  /trees/<name>/rename  # change the name of a node
  /trees/<name>/edit  # edit any node property
  /trees/<name>/clear_searches  # clear stored searches (free server memory)
  /trees/<name>/to_dendrogram  # convert tree to dendogram (no distances)
  /trees/<name>/to_ultrametric  # convert tree to ultrametric (equidistant leaves)

  POST:
  /trees  # add a new tree

  DELETE:
  /trees/<name>  # remove tree

In addition to the api endpoints, the server has these other ones::

  /  # redirects to /static/gui.html?tree=<name>
  /help  # gives some pointers for using ete
  /static/<path>  # all the static content, including javascript like gui.js

The api can be directly queried with the browser (for some endpoints
that accept a GET request), or with tools such as `curl
<https://curl.se/>`_ or `httpie <https://httpie.io/>`_.

The frontend uses those endpoints to draw and manipulate the trees. It
works as a web application, which mainly translates the list of
graphical commands coming from ``/trees/<name>/draw`` into svgs.

It is possible to use the same backend and write a different frontend
(as a desktop application, or in a different language, or using a
different graphics library), while still taking advantage of all the
optimizations done for the drawing.
