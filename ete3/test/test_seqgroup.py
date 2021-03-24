from __future__ import absolute_import
import unittest

from .. import SeqGroup
from .datasets import *

class Test_Coretype_SeqGroup(unittest.TestCase):
    """ Tests core functionality of Alignmnets objects """
    def test_fasta_parser(self):
        """ test fasta read an write """
        # FASTA IO
        with open("/tmp/ete_test_fasta.txt", "w") as f: f.write(fasta_example)
        # Test reading from file and from string
        SEQS = SeqGroup(fasta_example)
        SEQS2 = SeqGroup("/tmp/ete_test_fasta.txt")

        # Compare the result is the same
        self.assertEqual(SEQS.write(), SEQS2.write())

        # Test writing into file
        SEQS.write(format="fasta", outfile="/tmp/ete_fastaIO")
        self.assertEqual(SEQS.write(), fasta_example_output)

        # Test SeqGroup obj integrity
        self.assertEqual(SEQS.get_seq("Ago0000003"), Ago0000003)
        self.assertEqual(SEQS2.get_seq("Ago0000003"), Ago0000003)
        self.assertEqual(len(SEQS), len(SEQS.id2seq))
        self.assertEqual("Ago0000003" in SEQS, True)
        self.assertEqual("Ago" in SEQS, False)
        self.assertEqual(SEQS.get_entries(), [e for e in SEQS])

        # Check that the default  write format is FASTA
        self.assertEqual(SEQS.__str__(), SEQS.write(format="fasta"))


    def test_phylip_parser(self):
        """ Tests phylip read and write """
        # PHYLIP INTERLEAVED
        with open("/tmp/ete_test_iphylip.txt", "w") as f1: f1.write(phylip_interlived)
        SEQS = SeqGroup("/tmp/ete_test_iphylip.txt", format="iphylip")
        SEQS2 = SeqGroup(phylip_interlived, format="iphylip")
        self.assertEqual(SEQS.write(), SEQS2.write())
        SEQS.write(format="iphylip",  outfile="/tmp/ete_write_file")
        self.assertEqual(SEQS.write(format="iphylip"), phylip_interlived)

        # Test SeqGroup obj integrity
        self.assertEqual(SEQS.get_seq("CYS1_DICDI"), CYS1_DICDI)
        self.assertEqual(SEQS2.get_seq("CYS1_DICDI"), CYS1_DICDI)
        self.assertEqual(len(SEQS), len(SEQS.id2seq))
        self.assertEqual("CYS1_DICDI" in SEQS, True)
        self.assertEqual(SEQS.get_entries(), [e for e in SEQS])

        # PHYLIP SEQUENCIAL FORMAT
        with open("/tmp/ete_test_phylip.txt","w") as f2: f2.write(phylip_sequencial)
        SEQS = SeqGroup("/tmp/ete_test_phylip.txt", format="phylip")
        SEQS2 = SeqGroup(phylip_sequencial, format="phylip")
        self.assertEqual(SEQS.write(), SEQS2.write())
        SEQS.write(format="phylip",  outfile="/tmp/ete_write_file")
        self.assertEqual(SEQS.write(format="phylip"), phylip_sequencial)

        # Test SeqGroup obj integrity
        self.assertEqual(SEQS.get_seq("CYS1_DICDI"), CYS1_DICDI)
        self.assertEqual(SEQS2.get_seq("CYS1_DICDI"), CYS1_DICDI)
        self.assertEqual(len(SEQS), len(SEQS.id2seq))
        self.assertEqual("CYS1_DICDI" in SEQS, True)
        self.assertEqual("CYS1" in SEQS, False)
        self.assertEqual(SEQS.get_entries(), [e for e in SEQS])

        # test write speed
        #SEQS = SeqGroup()
        #for i in xrange(25):
        #    SEQS.set_seq("seq%s" %i, "A"*500000)
        #SEQS.write(outfile="/tmp/iphylip_write_test.phy", format="iphylip")
        #SEQS.write(outfile="/tmp/iphylip_write_test.phy", format="phylip")

    def test_alg_from_scratch(self):

        alg = SeqGroup(phylip_sequencial, format="phylip")

        random_seq = alg.get_seq("CATH_HUMAN")

        # Add a new sequence to the alg
        alg.set_seq("randomseq", random_seq.replace("A","X"))

        self.assertEqual(alg.get_seq("randomseq"), random_seq.replace("A","X"))

        # Exports the alignment to different formats
        alg.write(format ="fasta")
        alg.write(format ="iphylip")
        alg.write(format ="phylip")

if __name__ == '__main__':
    unittest.main()
