from __future__ import absolute_import
import unittest

from .. import ClusterTree, ArrayTable
from .datasets import *

class Test_Coretype_ArrayTable(unittest.TestCase):
    """ Tests reading clustering or phylogenetic profile data"""
    def test_arraytable_parser(self):
        """ Tests reading numneric tables"""
        A = ArrayTable(expression)
        self.assertEqual(A.get_row_vector("A").tolist(), \
                             [-1.23, -0.81, 1.79, 0.78,-0.42,-0.69, 0.58])
        self.assertEqual(A.get_several_row_vectors(["A","C"]).tolist(), \
                             [[-1.23, -0.81, 1.79, 0.78, -0.42, -0.69, 0.58],
                         [-2.19, 0.13, 0.65, -0.51, 0.52, 1.04, 0.36]])

        self.assertEqual(A.get_several_column_vectors(["col2", "col7"]).tolist(), \
                             [[-0.81000000000000005, -0.93999999999999995,\
                                0.13, -0.97999999999999998, -0.82999999999999996,\
                                    -1.1100000000000001, -1.1699999999999999,\
                                    -1.25],
                              [0.57999999999999996, 1.1200000000000001, \
                                   0.35999999999999999, 0.93000000000000005, \
                                   0.65000000000000002, 0.47999999999999998, \
                                   0.26000000000000001, 0.77000000000000002]])


        self.assertEqual(A.get_column_vector("col4").tolist(), \
                             [0.78000000000000003, 0.35999999999999999, \
                                  -0.51000000000000001, -0.76000000000000001, \
                                  0.070000000000000007, -0.14000000000000001, \
                                  0.23000000000000001, -0.29999999999999999])

        A.remove_column("col4")
        self.assertTrue(A.get_column_vector("col4") is None)

        Abis = A.merge_columns({"merged1": \
                                    ["col1", "col2"],\
                                    "merged2": \
                                    ["col5", "col6"]}, \
                                   "mean")

        #self.assert_((Abis.get_column_vector("merged1")==numpy.array([-1.02, -1.35, -1.03, -1.1, -1.15, -1.075, -1.37, -1.39, ])).all()==True )

        # Continue this......

