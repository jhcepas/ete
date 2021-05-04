"""
Tests for drawing trees. To run with pytest.
"""

import sys
from os.path import abspath, dirname
sys.path.insert(0, f'{abspath(dirname(__file__))}/../../..')

from math import pi, sqrt

from ete4 import Tree
from ete4.smartview.ete import draw, gardening as gdn
Size, Box, SBox = draw.Size, draw.Box, draw.SBox


# Helper functions to avoid rounding problems when comparing graphic elements.

def assert_equal(elements1, elements2):
    assert type(elements1) == type(elements2) == list
    assert len(elements1) == len(elements2)
    for e1, e2 in zip(elements1, elements2):
        assert_equal_elements(e1, e2)


def assert_equal_elements(element1, element2):
    "Assert that the graphic elements are equal within rounding"
    TOLERANCE = 1e-10

    assert type(element1) == type(element2) == list
    assert len(element1) == len(element2)

    for p1, p2 in zip(element1, element2):
        c1, c2 = type(p1), type(p2)
        assert c1 == c2 or isinstance(p1, c2) or isinstance(p2, c1)
        if c1 in [str, int, dict, list]:
            assert p1 == p2
        elif issubclass(c1, tuple):
            assert len(p1) == len(p2)
            for x1, x2 in zip(p1, p2):
                assert abs(x1 - x2) < TOLERANCE
        else:
            raise AssertionError(f'unrecognized type {c1}')


# The tests.

def test_draw_elements():
    assert draw.draw_nodebox((1, 2, 3, 4)) == \
        ['nodebox', (1, 2, 3, 4), '', {}, [], []]
    assert draw.draw_line((1, 2), (3, 4)) == \
        ['line', (1, 2), (3, 4), '', []]
    assert draw.draw_arc((1, 2), (3, 4), True) == \
        ['arc', (1, 2), (3, 4), 1, '']
    assert draw.draw_circle((1, 2), 3) == \
        ['circle', (1, 2), 3, '']
    assert draw.draw_text('hello', (1, 2, 3, 4), (5, 6)) == \
        ['text', 'hello', (1, 2, 3, 4), (5, 6), '']
    assert draw.draw_text('world', (1, 2, 3, 4), (5, 6), 'node') == \
        ['text', 'world', (1, 2, 3, 4), (5, 6), 'node']


def test_draw_node():
    t = Tree('A:10')
    gdn.update_all_sizes(t)

    drawer1 = draw.DrawerRectLeafNames(t, zoom=(20, 20))
    assert_equal(list(drawer1.draw_node(t, (0, 0), 0.5)), [
        ['text', (10.0, 0, 0.6666666666666, 1.0), (0, 0.5), 'A', 'name']])

    drawer1 = draw.DrawerRectLeafNames(t, zoom=(20, 20))
    assert_equal(list(drawer1.draw_node(t, (0, 0), 0.5)), [
        ['text', (10.0, 0, 0.6666666666666, 1.0), (0, 0.5), 'A', 'name']])

    drawer2 = draw.DrawerRectLeafNames(t, zoom=(0.1, 0.1))
    assert_equal(list(drawer2.draw_node(t, (0, 0), 0.5)), [
        ['text', (10.0, 0, 0.66666666666666, 1.0), (0, 0.5), 'A', 'name']])


def test_draw_collapsed():
    tree_text = '((B:200,(C:250,D:300)E:350)A:100)F;'
    t = Tree(tree_text)
    gdn.update_all_sizes(t)

    drawer_z10 = draw.DrawerRectLeafNames(t, zoom=(10, 10))
    assert not any(e[0] == 'outline' for e in drawer_z10.draw())

    drawer_z2 = draw.DrawerRectLeafNames(t, zoom=(2, 2))
    elements_z2 = list(drawer_z2.draw())
    print(elements_z2)
    assert_equal(elements_z2, [
        ['outline', (101.0, 0, 200, 650.0, 3.0)],
        ['text', (751.0, 0, 1.0, 1.5), (0, 0.5), 'B', 'name'],
        ['text', (751.0, 1.5, 1.0, 1.5), (0, 0.5), 'E', 'name'],
        ['line', (1.0, 1.5), (101.0, 1.5), 'lengthline', []],
        ['circle', (101.0, 1.5), 1, 'nodedot'],
        ['line', (0.0, 1.5), (1.0, 1.5), 'lengthline', []],
        ['circle', (1.0, 1.5), 1, 'nodedot'],
        ['nodebox', (0.0, 0.0, 752.0, 3.0), 'F', {'support': 1}, [], []],
        ['nodebox', (1.0, 0.0, 751.0, 3.0), 'A', {'support': 1}, (0,), []],
        ['nodebox', (101.0, 0, 651.0, 3.0), '(collapsed)', {}, [], []]])

    drawer_z1 = draw.DrawerRectLeafNames(t)
    elements_z1 = list(drawer_z1.draw())
    assert_equal(elements_z1, [
        ['outline', (0, 0, 751.0, 751.0, 3.0)],
        ['text', (751.0, 0, 2.0, 3.0), (0, 0.5), 'F', 'name'],
        ['nodebox', (0, 0, 753.0, 3.0), '(collapsed)', {}, [], []]])


def test_draw_tree_rect():
    tree_text = '((A:200,(B:250,C:300)D:350)E:100)F;'
    t = Tree(tree_text)
    gdn.update_all_sizes(t)

    drawer = draw.DrawerRectLeafNames(t, zoom=(10, 10))
    elements = list(drawer.draw())
    assert_equal(elements, [
        ['line', (101.0, 0.5), (301.0, 0.5), 'lengthline', []],
        ['circle', (301.0, 0.5), 1, 'nodedot'],
        ['text', (301.0, 0.0, 0.66666666666666, 1.0), (0, 0.5), 'A', 'name'],
        ['line', (451.0, 1.5), (701.0, 1.5), 'lengthline', []],
        ['circle', (701.0, 1.5), 1, 'nodedot'],
        ['text', (701.0, 1.0, 0.66666666666666, 1.0), (0, 0.5), 'B', 'name'],
        ['line', (451.0, 2.5), (751.0, 2.5), 'lengthline', []],
        ['circle', (751.0, 2.5), 1, 'nodedot'],
        ['text', (751.0, 2.0, 0.66666666666666, 1.0), (0, 0.5), 'C', 'name'],
        ['line', (101.0, 2.0), (451.0, 2.0), 'lengthline', []],
        ['circle', (451.0, 2.0), 1, 'nodedot'],
        ['line', (451.0, 1.5), (451.0, 2.5), 'childrenline', []],
        ['line', (1.0, 1.25), (101.0, 1.25), 'lengthline', []],
        ['circle', (101.0, 1.25), 1, 'nodedot'],
        ['line', (101.0, 0.5), (101.0, 2.0), 'childrenline', []],
        ['line', (0.0, 1.25), (1.0, 1.25), 'lengthline', []],
        ['circle', (1.0, 1.25), 1, 'nodedot'],
        ['nodebox', (0.0, 0.0, 751.66666666666666, 3.0), 'F', {'support': 1}, [], []],
        ['nodebox', (1.0, 0.0, 750.66666666666666, 3.0), 'E', {'support': 1}, (0,), []],
        ['nodebox', (101.0, 1.0, 650.66666666666666, 2.0), 'D', {'support': 1}, (0, 1), []],
        ['nodebox', (451.0, 2.0, 300.66666666666666, 1.0), 'C', {'support': 1}, (0, 1, 1), []],
        ['nodebox', (451.0, 1.0, 250.66666666666666, 1.0), 'B', {'support': 1}, (0, 1, 0), []],
        ['nodebox', (101.0, 0.0, 200.66666666666666, 1.0), 'A', {'support': 1}, (0, 0), []]])


def test_draw_tree_circ():
    tree_text = '((A:200,(B:250,C:300)D:350)E:100)F;'
    t = Tree(tree_text)
    gdn.update_all_sizes(t)

    drawer_circ = draw.DrawerCircLeafNames(t, zoom=(10, 10))
    elements_circ = list(drawer_circ.draw())
    assert_equal(elements_circ, [
        ['line', (-50.50000000000002, -87.46856578222828), (-150.50000000000006, -260.67364653911596), 'lengthline', []],
        ['circle', (-150.50000000000006, -260.67364653911596), 1, 'nodedot'],
        ['text', (301.0, -3.141592653589793, 420.27528388023455, 2.0943951023931953), (0, 0.5), 'A', 'name'],
        ['line', (451.0, -1.0014211682118912e-13), (701.0, -1.5565326805244695e-13), 'lengthline', []],
        ['circle', (701.0, -1.5565326805244695e-13), 1, 'nodedot'],
        ['text', (701.0, -1.0471975511965979, 978.78064451842, 2.0943951023931953), (0, 0.5), 'B', 'name'],
        ['line', (-225.49999999999972, 390.57745710678194), (-375.49999999999955, 650.3850782421137), 'lengthline', []],
        ['circle', (-375.49999999999955, 650.3850782421137), 1, 'nodedot'],
        ['text', (751.0, 1.0471975511965974, 1048.5938145981931, 2.0943951023931953), (0, 0.5), 'C', 'name'],
        ['line', (50.500000000000036, 87.46856578222828), (225.50000000000014, 390.57745710678176), 'lengthline', []],
        ['circle', (225.50000000000014, 390.57745710678176), 1, 'nodedot'],
        ['arc', (451.0, -1.0014211682118912e-13), (-225.4999999999999, 390.5774571067819), 0, 'childrenline'],
        ['line', (0.8660254037844383, -0.5000000000000007), (87.46856578222827, -50.500000000000064), 'lengthline', []],
        ['circle', (87.46856578222827, -50.500000000000064), 1, 'nodedot'],
        ['arc', (-50.50000000000002, -87.46856578222828), (50.500000000000064, 87.46856578222827), 0, 'childrenline'],
        ['line', (0.0, -0.0), (0.8660254037844383, -0.5000000000000007), 'lengthline', []],
        ['circle', (0.8660254037844383, -0.5000000000000007), 1, 'nodedot'],
        ['nodebox', (0.0, -3.141592643589793, 1799.5938145981931, 6.283185287179586), 'F', {'support': 1}, [], []],
        ['nodebox', (1.0, -3.141592643589793, 1798.5938145981931, 6.283185287179586), 'E', {'support': 1}, (0,), []],
        ['nodebox', (101.0, -1.0471975511965979, 1698.5938145981931, 4.188790194786391), 'D', {'support': 1}, (0, 1), []],
        ['nodebox', (451.0, 1.0471975511965974, 1348.5938145981931, 2.0943950923931958), 'C', {'support': 1}, (0, 1, 1), []],
        ['nodebox', (451.0, -1.0471975511965979, 1228.78064451842, 2.0943951023931953), 'B', {'support': 1}, (0, 1, 0), []],
        ['nodebox', (101.0, -3.141592643589793, 620.2752838802346, 2.0943950923931953), 'A', {'support': 1}, (0, 0), []]])


def test_intersects():
    # Simple intersection test.
    r1 = Box(0, 0, 10, 20)
    r2 = Box(-5, 0, 10, 20)
    assert draw.intersects_box(r1, r2)

    # Create several rectangles that start at their visual position and
    # have the size (width and height) as they appear in numbers.
    rects_text = """
  10,4
      5,2

                  2,3
 20,1
"""
    rects = []
    for y, line in enumerate(rects_text.splitlines()):
        for x, c in enumerate(line):
            if c != ' ':
                w, h = [int(v) for v in line.split(',')]
                rects.append(Box(x, y, w, h))
                break

    assert draw.intersects_box(rects[0], rects[1])
    assert not draw.intersects_box(rects[1], rects[2])
    assert draw.intersects_box(rects[2], rects[3])


def test_size():
    t = Tree('(a:2,b:3,c:4)d;')
    gdn.update_all_sizes(t)

    drawer = draw.DrawerRectLeafNames(t, zoom=(10, 10))
    assert drawer.node_size(t) == Size(5, 3)
    assert drawer.content_size(t) == Size(1, 3)
    assert drawer.children_size(t) == Size(4, 3)


def test_stack():
    b1 = Box(x=0, y= 0, dx=10, dy=5)
    sb1 = draw.stack(None, b1)

    b2 = Box(x=0, y= 5, dx=20, dy=10)
    sb2 = draw.stack(None, b2)

    b3 = Box(x=0, y=15, dx= 5, dy=3)
    sb3 = draw.stack(None, b3)

    b4 = Box(x=5, y=15, dx= 5, dy=3)
    sb4 = draw.stack(None, b4)

    assert draw.stack(sb1, b2) == SBox(0, 0, 10, 20, 15)
    assert draw.stack(sb2, b3) == SBox(0, 5, 5, 20, 13)
    assert draw.stack(draw.stack(sb1, b2), b3) == SBox(0, 0, 5, 20, 18)
    assert draw.stack(draw.stack(sb2, b3), b4) == SBox(0, 5, 5, 20, 16)


def test_circumshapes():
    # Make sure that the rectangles or annular sectors that represent the full
    # plane stay representing the full plane.
    assert draw.circumrect(None) is None
    assert draw.circumasec(None) is None

    # Rectangles surrounding annular sectors.
    assert draw.circumrect(Box(0, 0, 1, pi/2)) == Box(0, 0, 1, 1)
    assert draw.circumrect(Box(0, 0, 2, -pi/2)) == Box(0, -2, 2, 2)
    assert draw.circumrect(Box(0, 0, 1, pi/4)) == Box(0, 0, 1, 1/sqrt(2))

    # Annular sectors surrounding rectangles.
    assert draw.circumasec(Box(0, -2, 1, 1)) == Box(1, -pi/2, sqrt(5) - 1, pi/4)


def test_in_viewport():
    t = Tree('(a:2,b:3,c:4)d;')
    viewport = Box(-1, -2, 10, 20)
    drawer = draw.DrawerRectLeafNames(t, viewport, zoom=(10, 10))
    assert drawer.in_viewport(Box(0, 0, 1, 1))
    assert not drawer.in_viewport(Box(30, 20, 5, 5))
