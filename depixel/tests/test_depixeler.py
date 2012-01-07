from unittest import TestCase

import networkx as nx

from depixel.depixeler import PixelData


EAR = """
......
..XX..
.X..X.
.X..X.
....X.
....X.
......
"""

CIRCLE = """
......
..XX..
.X..X.
.X..X.
..XX..
......
"""

PLUS = """
..X..
..X..
XXXXX
..X..
..X..
"""

ISLAND = """
....
.X..
..XX
"""


def mkpixels(txt_data):
    pixels = []
    for line in txt_data.splitlines():
        line = line.strip()
        if line:
            pixels.append([{'.': 0, 'X': 1}[c] for c in line])
    return pixels


def sort_edges(edges):
    return sorted(tuple(sorted(e[:2])) + e[2:] for e in edges)


class TestUtils(TestCase):
    def test_mkpixels(self):
        ear_pixels = [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 0, 0],
            [0, 1, 0, 0, 1, 0],
            [0, 1, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0],
            ]
        self.assertEqual(ear_pixels, mkpixels(EAR))


class TestPixelData(TestCase):
    def test_size(self):
        pd = PixelData([[1, 1], [1, 1], [1, 1]])
        self.assertEqual((2, 3), pd.size)
        self.assertEqual((pd.size_x, pd.size_y), pd.size)

        pd = PixelData([[1, 1, 1], [1, 1, 1]])
        self.assertEqual((3, 2), pd.size)
        self.assertEqual((pd.size_x, pd.size_y), pd.size)

        pd = PixelData(mkpixels(EAR))
        self.assertEqual((6, 7), pd.size)
        self.assertEqual((pd.size_x, pd.size_y), pd.size)

    def test_pixel_graph(self):
        tg = nx.Graph()
        tg.add_nodes_from([
                ((0, 0), {'value': 0,
                          'corners': set([(0, 0), (0, 1), (1, 0), (1, 1)])}),
                ((0, 1), {'value': 0,
                          'corners': set([(0, 1), (0, 2), (1, 1), (1, 2)])}),
                ((0, 2), {'value': 0,
                          'corners': set([(0, 2), (0, 3), (1, 2), (1, 3)])}),
                ((1, 0), {'value': 0,
                          'corners': set([(1, 0), (1, 1), (2, 0), (2, 1)])}),
                ((1, 1), {'value': 1,
                          'corners': set([(1, 1), (1, 2), (2, 1), (2, 2)])}),
                ((1, 2), {'value': 0,
                          'corners': set([(1, 2), (1, 3), (2, 2), (2, 3)])}),
                ((2, 0), {'value': 0,
                          'corners': set([(2, 0), (2, 1), (3, 0), (3, 1)])}),
                ((2, 1), {'value': 0,
                          'corners': set([(2, 1), (2, 2), (3, 1), (3, 2)])}),
                ((2, 2), {'value': 1,
                          'corners': set([(2, 2), (2, 3), (3, 2), (3, 3)])}),
                ((3, 0), {'value': 0,
                          'corners': set([(3, 0), (3, 1), (4, 0), (4, 1)])}),
                ((3, 1), {'value': 0,
                          'corners': set([(3, 1), (3, 2), (4, 1), (4, 2)])}),
                ((3, 2), {'value': 1,
                          'corners': set([(3, 2), (3, 3), (4, 2), (4, 3)])}),
                ])
        tg.add_edges_from([
                ((0, 0), (1, 0), {'diagonal': False}),
                ((0, 1), (0, 0), {'diagonal': False}),
                ((0, 1), (0, 2), {'diagonal': False}),
                ((0, 1), (1, 0), {'diagonal': True}),
                ((0, 1), (1, 2), {'diagonal': True}),
                ((1, 1), (2, 2), {'diagonal': True}),
                ((1, 2), (0, 2), {'diagonal': False}),
                ((1, 2), (2, 1), {'diagonal': True}),
                ((2, 0), (1, 0), {'diagonal': False}),
                ((2, 1), (1, 0), {'diagonal': True}),
                ((2, 1), (2, 0), {'diagonal': False}),
                ((3, 0), (2, 0), {'diagonal': False}),
                ((3, 0), (2, 1), {'diagonal': True}),
                ((3, 0), (3, 1), {'diagonal': False}),
                ((3, 1), (2, 0), {'diagonal': True}),
                ((3, 1), (2, 1), {'diagonal': False}),
                ((3, 2), (2, 2), {'diagonal': False}),
                ])

        pd = PixelData(mkpixels(ISLAND))
        pd.make_pixel_graph()
        self.assertEqual(sorted(tg.nodes(data=True)),
                         sorted(pd.pixel_graph.nodes(data=True)))
        self.assertEqual(sort_edges(tg.edges(data=True)),
                         sort_edges(pd.pixel_graph.edges(data=True)))

    def test_weight_curve(self):
        pd = PixelData(mkpixels(EAR))
        pd.make_pixel_graph()
        self.assertEqual(1, pd.weight_curve(((0, 0), (1, 1))))
        self.assertEqual(1, pd.weight_curve(((1, 1), (2, 2))))
        self.assertEqual(7, pd.weight_curve(((1, 2), (2, 1))))

        pd = PixelData(mkpixels(CIRCLE))
        pd.make_pixel_graph()
        self.assertEqual(1, pd.weight_curve(((0, 0), (1, 1))))
        self.assertEqual(1, pd.weight_curve(((1, 1), (2, 2))))
        self.assertEqual(8, pd.weight_curve(((1, 2), (2, 1))))

    def test_weight_sparse(self):
        pd = PixelData(mkpixels(EAR))
        pd.make_pixel_graph()
        self.assertEqual(-18, pd.weight_sparse(((0, 0), (1, 1))))
        self.assertEqual(-28, pd.weight_sparse(((1, 1), (2, 2))))
        self.assertEqual(-8, pd.weight_sparse(((1, 2), (2, 1))))

        pd = PixelData(mkpixels(PLUS))
        pd.make_pixel_graph()
        self.assertEqual(-4, pd.weight_sparse(((0, 0), (1, 1))))
        self.assertEqual(-4, pd.weight_sparse(((1, 1), (2, 2))))
        self.assertEqual(-9, pd.weight_sparse(((1, 2), (2, 1))))

    def test_weight_island(self):
        pd = PixelData(mkpixels(ISLAND))
        pd.make_pixel_graph()
        self.assertEqual(5, pd.weight_island(((1, 1), (2, 2))))
        self.assertEqual(0, pd.weight_island(((1, 2), (2, 1))))

    def test_remove_diagonals(self):
        tg = nx.Graph()
        tg.add_nodes_from([
                ((0, 0), {'value': 0,
                          'corners': set([(0, 0), (0, 1), (1, 0), (1, 1)])}),
                ((0, 1), {'value': 0,
                          'corners': set([(0, 1), (0, 2), (1, 1), (1, 2)])}),
                ((0, 2), {'value': 0,
                          'corners': set([(0, 2), (0, 3), (1, 2), (1, 3)])}),
                ((1, 0), {'value': 0,
                          'corners': set([(1, 0), (1, 1), (2, 0), (2, 1)])}),
                ((1, 1), {'value': 1,
                          'corners': set([(1, 1), (1, 2), (2, 1), (2, 2)])}),
                ((1, 2), {'value': 0,
                          'corners': set([(1, 2), (1, 3), (2, 2), (2, 3)])}),
                ((2, 0), {'value': 0,
                          'corners': set([(2, 0), (2, 1), (3, 0), (3, 1)])}),
                ((2, 1), {'value': 0,
                          'corners': set([(2, 1), (2, 2), (3, 1), (3, 2)])}),
                ((2, 2), {'value': 1,
                          'corners': set([(2, 2), (2, 3), (3, 2), (3, 3)])}),
                ((3, 0), {'value': 0,
                          'corners': set([(3, 0), (3, 1), (4, 0), (4, 1)])}),
                ((3, 1), {'value': 0,
                          'corners': set([(3, 1), (3, 2), (4, 1), (4, 2)])}),
                ((3, 2), {'value': 1,
                          'corners': set([(3, 2), (3, 3), (4, 2), (4, 3)])}),
                ])
        tg.add_edges_from([
                ((0, 0), (1, 0), {'diagonal': False}),
                ((0, 1), (0, 0), {'diagonal': False}),
                ((0, 1), (0, 2), {'diagonal': False}),
                ((0, 1), (1, 0), {'diagonal': True}),
                ((0, 1), (1, 2), {'diagonal': True}),
                ((1, 1), (2, 2), {'diagonal': True}),
                ((1, 2), (0, 2), {'diagonal': False}),
                # ((1, 2), (2, 1), {'diagonal': True}),
                ((2, 0), (1, 0), {'diagonal': False}),
                ((2, 1), (1, 0), {'diagonal': True}),
                ((2, 1), (2, 0), {'diagonal': False}),
                ((3, 0), (2, 0), {'diagonal': False}),
                # ((3, 0), (2, 1), {'diagonal': True}),
                ((3, 0), (3, 1), {'diagonal': False}),
                # ((3, 1), (2, 0), {'diagonal': True}),
                ((3, 1), (2, 1), {'diagonal': False}),
                ((3, 2), (2, 2), {'diagonal': False}),
                ])

        pd = PixelData(mkpixels(ISLAND))
        pd.make_pixel_graph()
        pd.remove_diagonals()
        self.assertEqual(sorted(tg.nodes(data=True)),
                         sorted(pd.pixel_graph.nodes(data=True)))
        self.assertEqual(sort_edges(tg.edges(data=True)),
                         sort_edges(pd.pixel_graph.edges(data=True)))

    def test_deform_grid(self):
        tg = nx.Graph()
        tg.add_nodes_from([
                (0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3),
                (1.25, 1.25), (1.25, 1.75), (1.75, 1.25), (1.75, 2.25), (2, 0),
                (2, 1), (2, 3), (2.25, 1.75), (3, 0), (3, 1), (3, 2), (3, 3),
                (4, 0), (4, 1), (4, 2), (4, 3),
                ])
        tg.add_edges_from([
                ((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 3), (0, 2)),
                ((1, 0), (0, 0)), ((1, 0), (1, 1)), ((1, 0), (2, 0)),
                ((1, 1), (0, 1)), ((1, 2), (0, 2)), ((1, 3), (0, 3)),
                ((1, 3), (1, 2)), ((1, 3), (2, 3)), ((1.25, 1.25), (1, 1)),
                ((1.25, 1.25), (1.75, 1.25)), ((1.25, 1.75), (1, 2)),
                ((1.25, 1.75), (1.25, 1.25)), ((1.25, 1.75), (1.75, 2.25)),
                ((2, 1), (1.75, 1.25)), ((2, 1), (2, 0)), ((2, 1), (3, 1)),
                ((2, 3), (1.75, 2.25)), ((2.25, 1.75), (1.75, 1.25)),
                ((2.25, 1.75), (1.75, 2.25)), ((2.25, 1.75), (3, 2)),
                ((3, 0), (2, 0)), ((3, 0), (3, 1)), ((3, 0), (4, 0)),
                ((3, 2), (3, 1)), ((3, 2), (4, 2)), ((3, 3), (2, 3)),
                ((3, 3), (3, 2)), ((3, 3), (4, 3)), ((4, 0), (4, 1)),
                ((4, 1), (3, 1)), ((4, 1), (4, 2)), ((4, 2), (4, 3)),
                ])

        pd = PixelData(mkpixels(ISLAND))
        pd.depixel()

        self.assertEqual(sorted(tg.nodes()), sorted(pd.grid_graph.nodes()))
        self.assertEqual(sort_edges(tg.edges()),
                         sort_edges(pd.grid_graph.edges()))
