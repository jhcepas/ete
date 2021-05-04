"""
Tests related to the nexus module. To run with pytest.
"""

# Here you can find more information on the nexus format and examples:
#   https://en.wikipedia.org/wiki/Nexus_file
#   http://wiki.christophchamp.com/index.php?title=NEXUS_file_format
#   http://hydrodictyon.eeb.uconn.edu/eebedia/index.php/Phylogenetics:_NEXUS_Format

import os
PATH = os.path.abspath(f'{os.path.dirname(__file__)}/../../..')

import sys
sys.path.insert(0, PATH)

from tempfile import TemporaryFile

import pytest

from ete4.smartview.ete import nexus


def test_loads():
    with TemporaryFile(mode='w+t') as fp:
        fp.write("""#NEXUS
BEGIN TAXA;
    TaxLabels Scarabaeus Drosophila Aranaeus;
END;

BEGIN TREES;
    Translate beetle Scarabaeus, fly Drosophila, spider Aranaeus;
    Tree tree1 = ((1,2),3);
    Tree tree2 = ((beetle,fly),spider);
    Tree tree3 = ((Scarabaeus,Drosophila),Aranaeus);
END;
        """)
        fp.seek(0)

        trees = nexus.load(fp)
        newicks = {name: t.write() for name, t in trees.items()}
        print(newicks)
        assert newicks == {
            'tree1': '((1[&&NHX:support=1.0],\
                        2[&&NHX:support=1.0])[&&NHX:support=1.0],\
                        3[&&NHX:support=1.0])\
                        [&&NHX:support=1.0];'.replace(' ', ''),
            'tree2': '((Scarabaeus[&&NHX:support=1.0],\
                        Drosophila[&&NHX:support=1.0])[&&NHX:support=1.0],\
                        Aranaeus[&&NHX:support=1.0])\
                        [&&NHX:support=1.0];'.replace(' ', ''),
            'tree3': '((Scarabaeus[&&NHX:support=1.0],\
                        Drosophila[&&NHX:support=1.0])[&&NHX:support=1.0],\
                        Aranaeus[&&NHX:support=1.0])\
                        [&&NHX:support=1.0];'.replace(' ', '')}


def test_loads_bad_file():
    with TemporaryFile(mode='w+t') as fp:
        fp.write("""not a nexus file

        anything.""")
        fp.seek(0)

        with pytest.raises(nexus.NexusError):
            nexus.load(fp)


def test_get_trees():
    text = """#nexus
begin trees;
  translate
    1 Ephedra,
    2 Gnetum,
    3 Welwitschia,
    4 Ginkgo,
    5 Pinus
  ;
  tree one = [&U] (1,2,(3,(4,5)));
  tree two = [&U] (1,3,(5,(2,4)));
end;
"""

    trees = nexus.get_trees(text)
    print(trees)
    assert trees == {
            'one': """(Ephedra[&&NHX:support=1.0],\
                    Gnetum[&&NHX:support=1.0],\
                    (Welwitschia[&&NHX:support=1.0],\
                    (Ginkgo[&&NHX:support=1.0],\
                    Pinus[&&NHX:support=1.0])\
                    [&&NHX:support=1.0])\
                    [&&NHX:support=1.0])\
                    [&&NHX:support=1.0];""".replace(' ', ''), 
            'two': """(Ephedra[&&NHX:support=1.0],\
                    Welwitschia[&&NHX:support=1.0],\
                    (Pinus[&&NHX:support=1.0],\
                    (Gnetum[&&NHX:support=1.0],\
                    Ginkgo[&&NHX:support=1.0])\
                    [&&NHX:support=1.0])\
                    [&&NHX:support=1.0])\
                    [&&NHX:support=1.0];""".replace(' ', '')}


def test_loads_without_trees():
    with TemporaryFile(mode='w+t') as fp:
        fp.write("""#NEXUS
BEGIN TAXA;
    TaxLabels Scarabaeus Drosophila Aranaeus;
END;

BEGIN TREES;
END;
        """)
        fp.seek(0)

        trees = nexus.load(fp)
        assert trees == {}


    with TemporaryFile(mode='w+t') as fp:
        fp.write("""#NEXUS
BEGIN TAXA;
    TaxLabels Scarabaeus Drosophila Aranaeus;
END;
        """)
        fp.seek(0)

        trees = nexus.load(fp)
        assert trees == {}
