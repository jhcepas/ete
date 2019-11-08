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
from __future__ import absolute_import
from __future__ import print_function

from six import StringIO
import six.moves.cPickle
from collections import defaultdict
import logging
import os
import six
from six.moves import map
log = logging.getLogger("main")

from ..master_task import CogSelectorTask
from ..errors import DataError, TaskError
from ..utils import (GLOBALS, print_as_table, generate_node_ids, encode_seqname,
                     md5, pjoin, _min, _max, _mean, _median, _std, iter_cog_seqs, cmp)
from .. import db

__all__ = ["CogSelector"]

class CogSelector(CogSelectorTask):
    def __init__(self, target_sp, out_sp, seqtype, conf, confname):
        self.missing_factor = float(conf[confname]["_species_missing_factor"])
        self.max_missing_factor = float(conf[confname]["_max_species_missing_factor"])
        self.cog_hard_limit = int(conf[confname]["_max_cogs"])
        node_id, clade_id = generate_node_ids(target_sp, out_sp)
        # Initialize task
        CogSelectorTask.__init__(self, node_id, "cog_selector",
                                 "MCL-COGs", None, conf[confname])

        # taskid does not depend on jobs, so I set it manually
        self.cladeid = clade_id
        self.seqtype = seqtype
        self.targets = target_sp
        self.outgroups = out_sp
        self.init()
        self.size = len(target_sp | out_sp)
        self.cog_analysis = None
        self.cogs = None

    def finish(self):
        def cog_size_comparator_key(c):
            return (len(c), _min([sp2cogs[_sp] for _sp, _seq in c]))
        def sort_cogs_by_size(c1, c2):
            '''
            sort cogs by descending size. If two cogs are the same size, sort
            them keeping first the one with the less represented
            species. Otherwise sort by sequence name sp_seqid.'''

            r = -1 * cmp(len(c1), len(c2))
            if r == 0:
                # finds the cog including the less represented species
                c1_repr = _min([sp2cogs[_sp] for _sp, _seq in c1])
                c2_repr = _min([sp2cogs[_sp] for _sp, _seq in c2])
                r = cmp(c1_repr, c2_repr)
                if r == 0:
                    return cmp(sorted(c1), sorted(c2))
                else:
                    return r
            else:
                return r

        def cog_sp_comparator_key(c):
            return (_min([sp2cogs[_sp] for _sp, _seq in c]), sorted(c))
        def sort_cogs_by_sp_repr(c1, c2):
            c1_repr = _min([sp2cogs[_sp] for _sp, _seq in c1])
            c2_repr = _min([sp2cogs[_sp] for _sp, _seq in c2])
            r = cmp(c1_repr, c2_repr)
            if r == 0:
                r = -1 * cmp(len(c1), len(c2))
                if r == 0:
                    return cmp(sorted(c1), sorted(c2))
                else:
                    return r
            else:
                return r

        all_species = self.targets | self.outgroups
        # strict threshold
        #min_species = len(all_species) - int(round(self.missing_factor * len(all_species)))

        # Relax threshold for cog selection to ensure sames genes are always included
        min_species = len(all_species) - int(round(self.missing_factor * len(GLOBALS["target_species"])))
        min_species = max(min_species, (1-self.max_missing_factor) * len(all_species))

        smallest_cog, largest_cog = len(all_species), 0
        all_singletons = []
        sp2cogs = defaultdict(int)

        for cognumber, seq_cogs in iter_cog_seqs(GLOBALS["cogs_file"], GLOBALS["spname_delimiter"]):
            sp2seqs = defaultdict(list)
            for seqname, spcode, seqcode in seq_cogs:
                sp2seqs[spcode].append(seqcode)
                
            one2one_cog = set()
            for sp, seqs in six.iteritems(sp2seqs):
                #if len(seqs) != 1:
                #    print sp, len(seqs)
                if sp in all_species and len(seqs) == 1:
                    sp2cogs[sp] += 1
                    one2one_cog.add((sp, seqs[0]))
                    
            smallest_cog = min(smallest_cog, len(one2one_cog))
            largest_cog = max(largest_cog, len(one2one_cog))
            all_singletons.append(one2one_cog)
            #if len(one2one_cog) >= min_species:
            #    valid_cogs.append(one2one_cog)

        cognumber += 1 # sets the ammount of cogs in file
        for sp, ncogs in sorted(list(sp2cogs.items()), key=lambda x: x[1], reverse=True):
            log.log(28, "% 20s  found in single copy in  % 6d (%0.1f%%) COGs " %(sp, ncogs, 100 * ncogs/float(cognumber)))

        valid_cogs = sorted([sing for sing in all_singletons if len(sing) >= min_species],
                            key=cog_size_comparator_key)

        log.log(28, "Largest cog size: %s. Smallest cog size: %s" %(
                largest_cog, smallest_cog))
        self.cog_analysis = ""

        # save original cog names hitting the hard limit
        if len(valid_cogs) > self.cog_hard_limit:
            log.warning("Applying hard limit number of COGs: %d out of %d available" %(self.cog_hard_limit, len(valid_cogs)))
        self.raw_cogs = valid_cogs[:self.cog_hard_limit]
        self.cogs = []
        # Translate sequence names into the internal DB names
        sp_repr = defaultdict(int)
        sizes = []
        for co in self.raw_cogs:
            sizes.append(len(co))
            for sp, seq in co:
                sp_repr[sp] += 1
            co_names = ["%s%s%s" %(sp, GLOBALS["spname_delimiter"], seq) for sp, seq in co]
            encoded_names = db.translate_names(co_names)
            if len(encoded_names) != len(co):
                print(set(co_names) - set(encoded_names.keys()))
                raise DataError("Some sequence ids could not be translated")
            self.cogs.append(list(encoded_names.values()))

        # ERROR! COGs selected are not the prioritary cogs sorted out before!!!
        # Sort Cogs according to the md5 hash of its content. Random
        # sorting but kept among runs
        #map(lambda x: x.sort(), self.cogs)
        #self.cogs.sort(lambda x,y: cmp(md5(','.join(x)), md5(','.join(y))))

        log.log(28, "Analysis of current COG selection:")
        for sp, ncogs in sorted(list(sp_repr.items()), key=lambda x:x[1], reverse=True):
            log.log(28, " % 30s species present in % 6d COGs (%0.1f%%)" %(sp, ncogs, 100 * ncogs/float(len(self.cogs))))

        log.log(28, " %d COGs selected with at least %d species out of %d" %(len(self.cogs), min_species, len(all_species)))
        log.log(28, " Average COG size %0.1f/%0.1f +- %0.1f" %(_mean(sizes), _median(sizes), _std(sizes)))

        # Some consistency checks
        missing_sp = (all_species) - set(sp_repr.keys())
        if missing_sp:
            log.error("%d missing species or not present in single-copy in any cog:\n%s" %\
                      (len(missing_sp), '\n'.join(missing_sp)))
            open('etebuild.valid_species_names.tmp', 'w').write('\n'.join(list(sp_repr.keys())) +'\n')
            log.error("All %d valid species have been dumped into etebuild.valid_species_names.tmp."
                      " You can use --spfile to restrict the analysis to those species." %len(sp_repr))
            raise TaskError('missing or not single-copy species under current cog selection')

        CogSelectorTask.store_data(self, self.cogs, self.cog_analysis)

if __name__ == "__main__":
    ## TEST CODE
    import argparse
    parser = argparse.ArgumentParser()

    # Input data related flags

    parser.add_argument("--cogs_file", dest="cogs_file",
                        required=True,
                        help="Cogs file")

    parser.add_argument("--spname_delimiter", dest="spname_delimiter",
                             type=str, default = "_",
                             help="species name delimiter character")

    parser.add_argument("--target_sp", dest="target_sp",
                             type=str, nargs="+",
                             help="target species sperated by")

    parser.add_argument("-m", dest="missing_factor",
                             type=float, required=True,
                             help="missing factor for cog selection")

    parser.add_argument("--max_missing", dest="max_missing_factor",
                             type=float, default = 0.3,
                             help="max missing factor for cog selection")

    parser.add_argument("--total_species", dest="total_species",
                             type=int, required=True,
                             help="total number of species in the analysis")

    args = parser.parse_args()

    GLOBALS["cogs_file"] = args.cogs_file
    GLOBALS["spname_delimiter"] = args.spname_delimiter
    target_sp = args.target_sp
    logging.basicConfig(level=logging.DEBUG)
    log = logging
    GLOBALS["target_species"] = [1] * args.total_species

    conf = { "user": {"_species_missing_factor": args.missing_factor,
                      "_max_species_missing_factor": args.max_missing_factor,
                      "_max_cogs": 10000
                  }}
    CogSelectorTask.store_data=lambda a,b,c: True
    C =  CogSelector(set(target_sp), set(), "aa", conf, "user")

    db.translate_names = lambda x: {n: n for n in x}

    C.finish()
