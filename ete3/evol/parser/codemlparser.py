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
#!/usr/bin/python
"""
ugly parsers for outfiles of codeml, rst file for sites,
and main outfile
"""
from __future__ import absolute_import
from __future__ import print_function
from six.moves import map
from six.moves import filter
from six.moves import range

__author__  = "Francois-Jose Serra"
__email__   = "francois@barrabin.org"
__licence__ = "GPLv3"
__version__ = "0.0"

import re
from warnings import warn

def parse_rst(path):
    '''
    parse rst files from codeml, all site, branch-site models.
    return 2 dicts "classes" of sites, and values at each site "sites"
    '''
    typ       = None
    classes   = {}
    sites     = {}
    n_classes = {}
    k         = 0
    i         = 0
    bsa       = False
    path = '/'.join(path.split('/')[:-1]) + '/rst'
    for line in open(path):
        # get number of classes of sites
        if line.startswith ('dN/dS '):
            k = int(re.sub ('.* \(K=([0-9]+)\)\n', '\\1', line))
            continue
        # get values of omega and proportions
        if typ is None and \
           re.match ('^[a-z]+.*(\d+\.\d{5} *){'+ str(k) +'}', line):
            var = re.sub (':', '', line.split('  ')[0])
            if var.startswith ('p'):
                var = 'proportions'
            classes[var] = [float(v) for v in re.findall('\d+\.\d{5}', line)]
            continue
        # parse NEB and BEB tables
        if '(BEB)' in line :
            k = int(re.sub('.*for (\d+) classes.*\n', '\\1', line))
            typ = 'BEB'
            sites[typ] = {}
            n_classes[typ] = k
            continue
        if '(NEB)' in line :
            k = int(re.sub('.*for (\d+) classes.*\n', '\\1', line))
            typ = 'NEB'
            sites[typ] = {}
            n_classes[typ] = k
            continue
        # at the end of some BEB/NEB tables:
        if line.startswith ('Positively '):
            typ = None
        # continue if we are not in table
        if not re.match ('^ *[0-9]+ [A-Z*-] ', line) or typ is None:
            continue
        # line to list
        line = line.replace(' +- ', ' ')
        line = re.sub ('[()]', '', line.strip()).split()
        # get amino-acid
        sites[typ].setdefault ('aa', []).append (line[1])
        # get site class probability
        probs = []
        for i in range(k):
            probs.append (float (line[2+i]))
            sites [typ].setdefault('p' + str(i), []).append(float(line[2+i]))
        sites [typ].setdefault ('pv', []).append (max(probs))
        # get most likely site class
        classe = int (line [3 + i])
        sites[typ].setdefault ('class', []).append(classe)
        # if there, get omega and error
        try:
            sites [typ].setdefault('w' , []).append(float (line [4 + i]))
        except IndexError:
            # in this case we are with branch-site A or A1 and we should sum
            # probabilities of categories 2a and 2b
            probs = probs[:-2] + [sum(probs[-2:])]
            sites[typ]['pv'][-1] = max(probs)
            bsa = True
            try:
                sites[typ].setdefault('w' , []).append(
                    classes['foreground w'][classe - 1])
            except KeyError: # clade models
                del (sites [typ]['w'])
        try:
            sites [typ].setdefault ('se', []).append (float (line [5 + i]))
        except IndexError:
            del (sites [typ]['se'])
    return {'classes': classes,
            'sites' :sites,
            'n_classes': {k: n_classes[k] - bsa for k in n_classes}}


def divide_data(pamout, model):
    '''
    for multiple dataset, divide outfile.
    '''
    for num in range (1, int (model.properties['params']['ndata'])):
        model.name = model.name + '_' + str(num)
        out = open (pamout + '_' + str(num), 'w')
        copy = False
        for line in open (pamout):
            if copy == False and \
                   line.startswith('Data set '+ str (num) + '\n'):
                copy = True
                continue
            if copy == True and \
                   line.startswith('Data set '+ str (num+1) + '\n'):
                break
            if copy == True:
                out.write(line)
        out.close()
        if copy == False:
            warn ('WARNING: seems that you have no multiple dataset here...'\
                  + '\n    trying as with only one dataset')
        if model.typ == 'site':
            rst = '/'.join (pamout.split('/')[:-1])+'/rst'
            rstout = open (rst + '_' + str(num), 'w')
            copy = False
            for line in open(rst):
                if copy == False and \
                       re.match('\t' + str (num)+'\n', line) is not None:
                    copy = True
                    continue
                if copy == True and \
                       re.match('\t' + str (num + 1)+'\n', line) is not None:
                    copy = False
                if copy == True:
                    rstout.write(line)
            rstout.close()
            setattr (model, 'data_' + str (num),
                     parse_paml (pamout + '_' + str(num), model))
        else:
            setattr (model, 'data_' + str (num),
                     parse_paml (pamout + '_' + str(num), model))


def get_ancestor (pamout, model):
    '''
    only for fb_ancestor model, retrieves ancestral sequences also
    from rst file.
    '''
    for line in open ('/'.join (pamout.split('/')[:-1])+'/rst'):
        if line.startswith ('node #'):
            pamlid, seq = re.sub ('node#([0-9]+)([A-Z]*)\n', '\\1\t\\2',
                                  re.sub (' ', '', line)).split ('\t')
            n = model._tree.get_descendant_by_node_id (int (pamlid))
            n.add_feature ('nt_sequence', seq)
        elif line.startswith ('Node #'):
            pamlid, seq = re.sub ('Node#([0-9]+)([A-Z]*)\n', '\\1\t\\2',
                                  re.sub (' ', '', line)).split ('\t')
            n = model._tree.get_descendant_by_node_id (int (pamlid))
            n.add_feature ('sequence', seq)
        elif line.startswith ('Counts of changes at sites'):
            break

def parse_paml (pamout, model):
    '''
    parser function for codeml files,
    with values of w,dN,dS etc... dependending of the model
    tested.
    '''
    # if multiple dataset in same file we divide the outfile and model.name+x
    if not '*' in str (model.properties['params']['ndata']):
        divide_data (pamout, model)
        return
    all_lines = open (pamout).readlines()
    # if we do not have tree, load it
    if model._tree is None:
        from ..evol import EvolTree
        model._tree = EvolTree (re.findall ('\(.*\);', ''.join(all_lines))[2])
        model._tree._label_as_paml()
    # starts parsing
    for i, line in enumerate (all_lines):
        if line is '\n':
            continue
        # codon frequency
        if line.startswith('Codon frequencies under model'):
            model.stats ['codonFreq'] = []
            for j in range (16):
                line = list(map (float, re.findall ('\d\.\d+', all_lines [i+j+1])))
                model.stats ['codonFreq'] += [line]
            continue
        if line.startswith('Nei & Gojobori 1986'):
            model.stats ['codonFreq'] = []
        if 'codonFreq' not in model.stats:
            continue
        ######################
        # start serious staff
        line = line.rstrip()
        # lnL and number of parameters
        if line.startswith ('lnL'):
            try:
                line = re.sub ('.* np: *(\d+)\): +(-\d+\.\d+).*',
                               '\\1 \\2', line)
                model.stats ['np' ] = int   (line.split()[0])
                model.stats ['lnL'] = float (line.split()[1])
            except ValueError:
                line = re.sub ('.* np: *(\d+)\): +(nan).*',
                               '\\1 \\2', line)
                model.stats ['np' ] = int   (line.split()[0])
                model.stats ['lnL'] = float ('-inf')
            continue
        # get labels of internal branches
        if line.count('..') >= 2:
            labels = re.findall ('\d+\.\.\d+', line + ' ')
            _check_paml_labels (model._tree, labels, pamout, model)
            continue
        # retrieve kappa
        if line.startswith ('kappa '):
            try:
                model.stats ['kappa'] = float (re.sub ('.*(\d+\.\d+).*',
                                                       '\\1', line))
            except ValueError:
                model.stats ['kappa'] = 'nan'
        # retrieve dS dN t w N S and if present, errors. from summary table
        if line.count('..') == 1 and line.startswith (' '):
            if not re.match (' +\d+\.\.\d+ +\d+\.\d+ ', line):
                if re.match (' +( +\d+\.\d+){8}', all_lines [i+1]):
                    _get_values (model, line.split ()[0]+'  '+all_lines [i+1])
                continue
            _get_values (model, line)
            continue

def _get_values(model, line):
    '''
    just to ligther main parser
    '''
    vals = line.split()
    # store values under paml_id
    paml_id = int (vals[0].split('..')[1])
    model.branches[paml_id].update({
        'bL'  : float (vals [1]),
        'N'   : float (vals [2]),
        'S'   : float (vals [3]),
        'w'   : float (vals [4]),
        'dN'  : float (vals [5]),
        'dS'  : float (vals [6]),
        'SEdN': float (vals[vals.index ('dN') + 4]) if 'dN' in line else None,
        'SEdS': float (vals[vals.index ('dS') + 4]) if 'dS' in line else None
        })

def _check_paml_labels (tree, paml_labels, pamout, model):
    '''
     * check paml labels
    Should not be necessary if all codeml is run through ETE.
    '''
    try:
        relations = sorted ([list(map( int, x.split('..'))) for x in paml_labels],
                            key=lambda x: x[1])
    except IndexError:
        return
    # check that labelling corresponds with paml...
    for rel in relations:
        try:
            node = tree.get_descendant_by_node_id(rel[1])
            if int (node.up.node_id) != int (rel[0]):
                warn('WARNING: labelling does not correspond (bad tree?)!!\n' + \
                     '         Getting them from ' + pamout)
                _get_labels_from_paml(tree, relations, pamout, model)
                break
        except IndexError:
            # if unable to find one node, relabel the whole tree
            print(rel)
            warn ('ERROR: labelling does not correspond!!\n' + \
                  '       Getting them from ' + pamout)
            _get_labels_from_paml(tree, relations, pamout, model)

def _get_labels_from_paml (tree, relations, pamout, model):
    '''
    in case problem in labelling... and of course it is not my fault...
    retrieve node_ids from outfile... from relations line.
    This may occur when loading a model that was run outside ETE.
    '''
    from copy import copy
    old2new = {}
    # label leaves
    for line in open (pamout, 'r').readlines():
        if re.search ('^#[0-9][0-9]*:', line):
            nam, paml_id = re.sub ('#([0-9]+): (.*)', '\\2 \\1',
                                   line.strip()).split()
            node = (tree & nam)
            old2new[node.node_id] = int(paml_id)
            node.add_feature ('node_id', int(paml_id))
        if line.startswith ('Sums of codon'):
            break
    # label the root
    tree.add_feature ('node_id', int (len (tree) + 1))
    # label other internal nodes
    for node in tree.traverse(strategy='postorder'):
        if node.is_root(): continue
        paml_id = next(filter(lambda x: x[1]==node.node_id, relations))[0]
        old2new[node.up.node_id] = paml_id
        node.up.node_id = paml_id
    ### change keys in branches dict of model
    branches = copy(model.branches)
    for b in model.branches:
        model.branches[b] = branches[old2new[b]]



