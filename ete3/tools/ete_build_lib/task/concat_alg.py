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
from os.path import join as pjoin
import logging
from collections import defaultdict
import six
from six.moves import zip
log = logging.getLogger("main")

from . import Msf
from ..master_task import ConcatAlgTask
from ..master_job import Job
from ..utils import SeqGroup, GLOBALS, generate_runid, pexist, md5, cmp
from .. import db
from ..errors import TaskError

__all__ = ["ConcatAlg"]

class ConcatAlg(ConcatAlgTask):
    def __init__(self, cogs, seqtype, conf, confname, workflow_checksum):
        self.confname = confname
        self.conf = conf
        #self.cogs_hard_limit = int(conf[confname]["_max_cogs"])
        #used_cogs = cogs[:self.cogs_hard_limit]
        used_cogs = cogs

        cog_string = '#'.join([','.join(sorted(c)) for c in used_cogs])
        cog_keyid = md5(cog_string) # This will be nodeid
        base_args = {}
        ConcatAlgTask.__init__(self, cog_keyid, "concat_alg", "ConcatAlg",
                               workflow_checksum=workflow_checksum,
                               base_args=base_args, extra_args=conf[confname])
        self.avail_cogs = len(cogs)
        self.used_cogs = len(used_cogs)
        self.cogs = used_cogs
        self.seqtype = seqtype
        self.cog_ids = set()

        self.job2alg = {}
        self.job2model = {}
        if seqtype == "aa":
            self.default_model = conf[confname]["_default_aa_model"]
        elif seqtype == "nt":
            self.default_model = conf[confname]["_default_nt_model"]

        self.genetree_workflow = conf[confname]["_workflow"][1:]
        self.init()

    def load_jobs(self):
        # I want a single phylognetic tree for each cog
        from ..workflow.genetree import pipeline

        for co in self.cogs:
            # Register a new msf task for each COG, using the same
            # config file but opening an new tree reconstruction
            # thread.
            job = Msf(set(co), set(), seqtype = self.seqtype)
            job.main_tree = None
            job.threadid = generate_runid()
            job.configid = self.conf["_configid"]
            # This converts the job in a workflow job. As soon as a
            # task is done, it will be automatically processed and the
            # new tasks will be registered as new jobs.
            job.task_processor = pipeline
            job.target_wkname = self.genetree_workflow
            self.jobs.append(job)
            self.cog_ids.add(job.nodeid)

    def finish(self):
        # Assumes tasks resulting from genetree workflow, in which
        # only Alg and Acleaner tasks could contain the results
        log.log(26, "Collecting supermatrix data")
        jobtypes = set()
        job2alg, job2acleaner = {}, {}
        alg_seqtypes = set()
        clean_alg_seqtypes = set()
        for job in self.jobs:
            jobtypes.add(job.ttype)
            if job.ttype == "alg" and job.nodeid not in self.job2alg:
                try:
                    tid, datatype = job.alg_nt_fasta_file.split(".")
                except:
                    tid, datatype = job.alg_fasta_file.split(".")
                    alg_seqtypes.add(job.seqtype)
                else:
                    alg_seqtypes.add("nt")
                    
                dataid = db.get_dataid(tid, datatype)
                job2alg[job.nodeid] = db.get_data(dataid)
            elif job.ttype == "acleaner":
                try:
                    tid, datatype = job.alg_nt_fasta_file.split(".")
                except:
                    tid, datatype = job.clean_alg_fasta_file.split(".")
                    clean_alg_seqtypes.add(job.seqtype)
                else:
                    clean_alg_seqtypes.add("nt")
                    
                dataid = db.get_dataid(tid, datatype)
                job2acleaner[job.nodeid] = db.get_data(dataid)
            elif job.ttype == "mchooser":
                # clean model comming from pmodeltest
                clean_model = job.best_model.replace('pmodeltest-', '').split("+")[0].split("!")[0]
                self.job2model[job.nodeid] = clean_model

        if "acleaner" in jobtypes:
            log.warning("Concatenating trimmed alignments")
            self.job2alg = job2acleaner
            seqtypes = clean_alg_seqtypes
        else:
            log.warning("Concatenating alignments")
            self.job2alg = job2alg
            seqtypes = alg_seqtypes
                
        if len(seqtypes) > 1:
            raise TaskError("Mixed nt/aa concatenated alignments not yet supported")
        else:
            seqtype = seqtypes.pop()

        log.warning("Using %s concatenated alignment" %seqtype)
            
        if seqtype == "aa":
            self.default_model = self.conf[self.confname]["_default_aa_model"]
        elif seqtype == "nt":
            self.default_model = self.conf[self.confname]["_default_nt_model"]            
        self.seqtype = seqtype            

        if self.cog_ids - set(self.job2alg):
            log.error("Missing %s algs", len(self.cog_ids -
                                             set(self.job2alg)))
            missing = self.cog_ids - set(self.job2alg)
            raise TaskError(self, "Missing algs (%d): i.e. %s" %(len(missing),missing[:10]))
        
        alg_data = [(self.job2alg[nid],
                     self.job2model.get(nid, self.default_model))
                    for nid in self.job2alg]
        filenames, models = list(zip(*alg_data))

        mainalg, partitions, sp2alg, species, alg_lenghts = get_concatenated_alg(
            filenames,
            models, sp_field=0,
            sp_delimiter=GLOBALS["spname_delimiter"])

        log.log(20, "Done concat alg, now writting fasta format")
        fasta = mainalg.write(format="fasta")
        log.log(20, "Done concat alg, now writting phylip format")
        phylip = mainalg.write(format="iphylip_relaxed")
        txt_partitions = '\n'.join(partitions)
        log.log(26, "Modeled regions: \n"+'\n'.join(partitions))
        ConcatAlg.store_data(self, fasta, phylip, txt_partitions)

def get_species_code(name, splitter, field):
    # By default, taxid is the first par of the seqid, separated by
    # underscore
    return name.split(splitter, 1)[field].strip()

def get_concatenated_alg(alg_filenames, models=None,
                        sp_field=0, sp_delimiter="_",
                        kill_thr=0.0,
                        keep_species=None):
    # Concat alg container
    if keep_species is None:
        keep_species = set()
    concat = SeqGroup()
    # Used to store different model partitions
    concat.id2partition = {}

    if not models:
        models = ["None"]*len(alg_filenames)
    else:
        if len(models) != len(alg_filenames):
            raise ValueError("Different number of algs and model names was found!")

    expected_total_length = 0
    # Check algs and gets the whole set of species
    alg_objects = []
    sp2alg = defaultdict(list)

    for algfile, matrix in zip(alg_filenames, models):
        alg = SeqGroup(algfile, "fasta")
        alg_objects.append(alg)
        lenseq = None
        browsed_species = set()
        alg.sp2seq = {}
        # Set best matrix for this alignment
        alg.matrix = matrix
        # Change seq names to contain only species names
        for i, seq in six.iteritems(alg.id2seq):
            name = db.get_seq_name(alg.id2name[i])
            taxid = get_species_code(name, splitter=sp_delimiter, field=sp_field)
            if lenseq is not None and len(seq) != lenseq:
                raise Exception("Inconsistent alignment when concatenating: Unequal length")
            elif lenseq is None:
                lenseq = len(seq)
                alg.seqlength = len(seq)
                expected_total_length += len(seq)
            if taxid in browsed_species:
                raise Exception("Inconsistent alignment when concatenating: Repeated species")
            browsed_species.add(taxid) # Check no duplicated species in the same alg
            sp2alg[taxid].append(alg) # Records all species seen in all algs.
            alg.sp2seq[taxid] = seq

    valid_species = [sp for sp in six.iterkeys(sp2alg) \
                         if sp in keep_species or \
                         len(sp2alg[sp])/float(len(alg_objects)) > kill_thr]

    log.info("%d out of %d will be kept (missing factor threshold=%g, %d species forced to kept)" %\
                 (len(valid_species), len(sp2alg), kill_thr, len(keep_species)))

    def single_algs_comparator_key(alg):
        return (alg.matrix, sorted(alg.id2name.values()))
    def sort_single_algs(alg1, alg2):
        r = cmp(alg1.matrix, alg2.matrix)
        if r == 0:
            return cmp(sorted(alg1.id2name.values()),
                       sorted(alg2.id2name.values()))
        else:
            return r

    sorted_algs = sorted(alg_objects, key=single_algs_comparator_key)
    concat_alg_lengths = [alg.seqlength for alg in sorted_algs]
    model2win = {}
    model2size = {}
    for alg in sorted_algs:
        model2size[alg.matrix] = model2size.get(alg.matrix, 0) + alg.seqlength

    # Create concat alg
    concat.id2seq = defaultdict(list)
    for sp in sorted(valid_species):
        log.log(20, "Concatenating sequences of [%s]" %sp)
        for alg in sorted_algs:
            seq = alg.sp2seq.get(sp, "-" * alg.seqlength)
            concat.id2seq[sp].append(seq)
            #current_seq = concat.id2seq.get(sp, "")
            #concat.id2seq[sp] = current_seq + seq.strip()
            concat.id2name[sp] = sp
            concat.name2id[sp] = sp
            concat.id2comment[sp] = [""]
        concat.id2seq[sp] = ''.join(concat.id2seq[sp])

    current_pos = 0
    partitions = []
    for model in sorted(model2size.keys()):
        size = model2size[model]
        part = "%s, %s = %d-%d" % (model, model+"_genes", \
                                       current_pos + 1,\
                                       current_pos + size)
        current_pos += size
        partitions.append(part)

    # Basic Checks
    seq_sizes = [len(seq) for seq in list(concat.id2seq.values())]
    if len(set(seq_sizes)) != 1:
        raise Exception("Concatenated alignment is not consistent: unequal seq length ")
    if seq_sizes[0] != expected_total_length:
        raise Exception("The size of concatenated alg is not what expected")
    return concat, partitions, sp2alg, valid_species, concat_alg_lengths


