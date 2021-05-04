#!/usr/bin/env python3

"""
Dump all the trees existing in the database, as newicks in files with the
name of each tree.
"""

import sys
from os.path import abspath, dirname, basename, exists
sys.path.insert(0, f'{abspath(dirname(__file__))}/..')

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter as fmt

import sqlite3


def main():
    try:
        args = get_args()
        assert exists(args.db), f'Missing database file: "{args.db}"'
        print(f'Dumping trees from database {args.db} ...')
        with sqlite3.connect(args.db) as connection:
            c = connection.cursor()
            for name,newick in c.execute('SELECT name,newick FROM trees'):
                fname = name + '.tree'
                if args.overwrite or not exists(fname):
                    print('  ->', fname)
                    open(fname, 'wt').write(newick)
                else:
                    print(f'Skipping existing file: "{fname}"')
    except (AssertionError, sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        sys.exit(e)


def get_args():
    "Return the command-line arguments"
    parser = ArgumentParser(description=__doc__, formatter_class=fmt)

    add = parser.add_argument  # shortcut
    add('--db', default='trees.db', help='sqlite database file')
    add('--overwrite', action='store_true', help='overwrite files if they exist')

    return parser.parse_args()



if __name__ == '__main__':
    main()
