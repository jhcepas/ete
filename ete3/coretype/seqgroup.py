# #START_LICENSE###########################################################
#
#
# This file is part of the Environment for Tree Exploration program
# (ETE).  http://etetoolkit.org
#
# ETE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ETE is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ETE.  If not, see <http://www.gnu.org/licenses/>.
#
#
#                     ABOUT THE ETE PACKAGE
#                     =====================
#
# ETE is distributed under the GPL copyleft license (2008-2015).
#
# If you make use of ETE in published work, please cite:
#
# Jaime Huerta-Cepas, Joaquin Dopazo and Toni Gabaldon.
# ETE: a python Environment for Tree Exploration. Jaime BMC
# Bioinformatics 2010,:24doi:10.1186/1471-2105-11-24
#
# Note that extra references to the specific methods implemented in
# the toolkit may be available in the documentation.
#
# More info at http://etetoolkit.org. Contact: huerta@embl.de
#
#
# #END_LICENSE#############################################################

"""
The 'seqgroup' module provides methods and classes to operate with
Multiple Sequence Files, including Multiple Sequence Alignments.

Currently, Fasta, Phylip sequencial and Phylip interleaved formats are
supported.
"""
from __future__ import absolute_import

from ..parser.fasta import read_fasta, write_fasta
from ..parser.paml import read_paml, write_paml
from ..parser.phylip import read_phylip, write_phylip
import six
from six.moves import zip

__all__ = ["SeqGroup"]

class SeqGroup(object):
    """
    SeqGroup class can be used to store a set of sequences (aligned
    or not).


    :argument sequences: Path to the file containing the sequences or,
        alternatively, the text string containing the same
        information.

    :argument fasta format: the format in which sequences are
        encoded. Current supported formats are: ``fasta``, ``phylip``
        (phylip sequencial) and ``iphylip`` (phylip
        interleaved). Phylip format forces sequence names to a maximum
        of 10 chars. To avoid this effect, you can use the relaxed
        phylip format: ``phylip_relaxed`` and ``iphylip_relaxed``.

    ::

     msf = ">seq1\\nAAAAAAAAAAA\\n>seq2\\nTTTTTTTTTTTTT\\n"
     seqs = SeqGroup(msf, format="fasta")
     print seqs.get_seq("seq1")
     """

    def __len__(self):
        return len(self.id2seq)

    def __contains__(self, item):
        return item in self.name2id

    def __str__(self):
        return write_fasta(self)

    def __iter__(self):
        return self.iter_entries()

    def __init__(self, sequences=None, format="fasta", fix_duplicates=True, **kwargs):
        self.parsers = {
            "fasta": [read_fasta, write_fasta, {}],
            "phylip": [read_phylip, write_phylip, {"interleaved":False, "relaxed":False}],
            "iphylip": [read_phylip, write_phylip, {"interleaved":True, "relaxed":False}],
            "phylip_relaxed": [read_phylip, write_phylip, {"interleaved":False, "relaxed":True}],
            "iphylip_relaxed": [read_phylip, write_phylip, {"interleaved":True, "relaxed":True}],
            "paml"   : [read_paml  , write_paml  , kwargs                   ]
            }

        self.id2name = {}
        self.name2id = {}
        self.id2comment= {}
        self.id2seq = {}

        if sequences is not None:
            format = format.lower()
            if format in self.parsers:
                read = self.parsers[format][0]
                args = self.parsers[format][2]
                read(sequences, obj=self, fix_duplicates=fix_duplicates, **args)
            else:
                raise ValueError("Unsupported format: [%s]" %format)

    def __repr__(self):
        return "SeqGroup (%s)" %hex(self.__hash__())

    def write(self, format="fasta", outfile=None):
        """ Returns the text representation of the sequences in the
        supplied given format (default=FASTA). If "oufile" argument is
        used, the result is written into the given path."""

        format = format.lower()
        if format in self.parsers:
            write = self.parsers[format][1]
            args = self.parsers[format][2]
            return write(self, outfile, **args)
        else:
            raise ValueError("Unsupported format: [%s]" %format)

    def iter_entries(self):
        """ Returns an iterator over all sequences in the
        collection. Each item is a tuple with the sequence name,
        sequence, and sequence comments """
        for i, seq in six.iteritems(self.id2seq):
            yield self.id2name[i], seq,  self.id2comment.get(i, [])

    def get_seq(self, name):
        """ Returns the sequence associated to a given entry name."""
        return self.id2seq[self.name2id[name]]

    def get_entries(self):
        """ Returns the list of entries currently stored."""
        keys = list(self.id2seq.keys())
        seqs = list(self.id2seq.values())
        comments = [self.id2comment.get(x, []) for x in  keys]
        names = [self.id2name[x] for x in keys]
        return list(zip(names, seqs, comments))

    def set_seq(self, name, seq, comments = None):
        """Updates or adds a sequence """
        if comments is None:
            comments = []
        name = name.strip()
        seq = seq.replace(" ", "")
        seq = seq.replace("\t", "")
        seq = seq.replace("\n", "")
        seq = seq.replace("\r", "")
        seqid = self.name2id.get(name, max([0]+list(self.name2id.values()))+1)
        self.name2id[name] = seqid
        self.id2name[seqid] = name
        self.id2comment[seqid] = comments
        self.id2seq[seqid] = seq

