"""
Tests for add_tree.py. To run with pytest.
"""

import os
PATH = os.path.abspath(f'{os.path.dirname(__file__)}/..')

import sys
from tempfile import NamedTemporaryFile

import pytest


def exec(command):
    print(command)
    assert os.system(command) == 0


def test_add_trees_to_db():
    path_trees = f''
    print(PATH)
    with NamedTemporaryFile() as fp:
        exec(f'sqlite3 {fp.name} < {PATH}/gui/create_tables.sql')
        exec(f'sqlite3 {fp.name} < {PATH}/gui/sample_data.sql')

        exec(f'{PATH}/gui/add_tree.py --db {fp.name} --name with_test '
                f'{PATH}/examples/HmuY.aln2.tree')

        add_all(db=fp.name)

        with pytest.raises(AssertionError):
            exec(f'{PATH}/gui/add_tree.py --db {fp.name} nonexistent_file')


def add_all(db):
    cmd = f'{PATH}/gui/add_tree.py --db {db} --no-verify '
    for fname in ['aves.tree', 'GTDB_bact_r95.tree', 'HmuY.aln2.tree']:
        exec(cmd + f'{PATH}/examples/{fname}')
        with pytest.raises(AssertionError):
            exec(cmd + f'{PATH}/examples/{fname}')
            # the second time should fail because of repeated name
