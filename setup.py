# -*- coding: utf-8 -*-

#! /usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
#import ez_setup
import hashlib
import time, random
import re
from Cython.Build import cythonize
from distutils.core import setup, Extension

HERE = os.path.abspath(os.path.split(os.path.realpath(__file__))[0])

PYTHON_DEPENDENCIES = [
    ["numpy", "Numpy is required for the ArrayTable and ClusterTree classes.", 0],
    ["PyQt", "PyQt4/5 is required for tree visualization and image rendering.", 0],
    ["lxml", "lxml is required from Nexml and Phyloxml support.", 0]
]

CLASSIFIERS= [
    "Development Status :: 6 - Mature",
    "Environment :: Console",
    "Environment :: X11 Applications :: Qt",
    "Intended Audience :: Developers",
    "Intended Audience :: Other Audience",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU General Public License (GPL)",
    "Natural Language :: English",
    "Operating System :: MacOS",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Topic :: Scientific/Engineering :: Visualization",
    "Topic :: Software Development :: Libraries :: Python Modules",
    ]

def can_import(mname):
    'Test if a module can be imported '
    if mname == "PyQt":
        try:
            __import__("PyQt4.QtCore")
            __import__("PyQt4.QtGui")
        except ImportError:
            try:
                __import__("PyQt5.QtCore")
                __import__("PyQt5.QtGui")
            except ImportError:
                return False
            else:
                return True
        else:
            return True
    else:
        try:
            __import__(mname)
        except ImportError:
            return False
        else:
            return True

try:
    ETE_VERSION = open(os.path.join(HERE, "VERSION")).readline().strip()
except IOError:
    ETE_VERSION = 'unknown'

print("\nInstalling ETE (%s) \n" %ETE_VERSION)
print()
    
MOD_NAME = "ete4"

LONG_DESCRIPTION="""
The Environment for Tree Exploration (ETE) is a Python programming
toolkit that assists in the recontruction, manipulation, analysis and
visualization of phylogenetic trees (although clustering trees or any
other tree-like data structure are also supported).

ETE is currently developed as a tool for researchers working in
phylogenetics and genomics. If you use ETE for a published work,
please cite:

::

   Jaime Huerta-Cepas, François Serra and Peer Bork. "ETE 3: Reconstruction,
   analysis and visualization of phylogenomic data."  Mol Biol Evol (2016) doi:
   10.1093/molbev/msw046

Visit http://etetoolkit.org for more info.
"""

extensions = [
        Extension('ete4.coretype.tree', ['ete4/coretype/tree.pyx']), 
        Extension('ete4.parser.newick', ['ete4/parser/newick.pyx']), 
        Extension('ete4.smartview.ete.gardening', ['ete4/smartview/ete/gardening.pyx']), 
            ],

try:
    _s = setup(
        include_package_data = True,

        name = MOD_NAME,
        version = ETE_VERSION,
        packages = ["ete4"],

        entry_points = {"console_scripts":
                        ["ete4 = %s.tools.ete:main" %MOD_NAME]},
        requires = ["six"],

        # Project uses reStructuredText, so ensure that the docutils get
        # installed or upgraded on the target machine
        install_requires = [
            ],
        package_data = {

        },
        data_files = [("%s/tools" %MOD_NAME, 
                       ["%s/tools/ete_build.cfg" %MOD_NAME])],

        # metadata for upload to PyPI
        author = "Jaime Huerta-Cepas, Jordi Burguet-Castells",
        author_email = "jhcepas@gmail.com",
        maintainer = "Jaime Huerta-Cepas, Jordi Burguet-Castells",
        maintainer_email = "jhcepas@gmail.com",
        platforms = "OS Independent",
        license = "GPLv3",
        description = "A Python Environment for (phylogenetic) Tree Exploration",
        long_description = LONG_DESCRIPTION,
        classifiers = CLASSIFIERS,
        provides = [MOD_NAME],
        keywords = "tree, tree reconstruction, tree visualization, tree comparison, phylogeny, phylogenetics, phylogenomics",
        url = "http://etetoolkit.org",
        download_url = "http://etetoolkit.org/static/releases/ete4/",


        ext_modules = cythonize(*extensions),
        # scripts=glob('scripts/*.py'),
        # data_files=[
        #     ('server', glob('scripts/static/*.*')),
        #     ('server/external', glob('scripts/static/external/*')),
        #     ('sql', glob('scripts/*.sql')),
        #     ('examples', glob('examples/*'))])
    )
 
except:
    print("\033[91m - Errors found! - \033[0m")
    raise

else:

    print("\033[92m - Done! - \033[0m")
    missing = False
    for mname, msg, ex in PYTHON_DEPENDENCIES:
        if not can_import(mname):
            print(" Warning:\033[93m Optional library [%s] could not be found \033[0m" %mname)
            print("  ",msg)
            missing=True
