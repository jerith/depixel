# -*- test-case-name: depixel.tests.test_depixeler -*-

"""
An implementation of the Depixelizing Pixel Art algorithm.

The paper can be found online at:
    http://research.microsoft.com/en-us/um/people/kopf/pixelart/
"""

from math import sqrt

import networkx as nx

from depixel import bspline


def gen_coords(size):
    for y in xrange(size[1]):
        for x in xrange(size[0]):
            yield (x, y)


def within_bounds(coord, size, offset=(0, 0)):
    x, y = map(sum, zip(coord, offset))
    size_x, size_y = size
    return (0 <= x < size_x and 0 <= y < size_y)


def cn_edge(edge):
    return tuple(sorted(edge[:2]))


def distance(p0, p1):
    return sqrt((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)


def gradient(p0, p1):
    # Assume the constant below is big enough. Bleh.
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    if dx == 0:
        return dy * 99999999999999
    return 1.0 * dy / dx


def remove_from_set(things, thing):
    things.add(thing)
    things.remove(thing)


class DiagonalResolutionHeuristics(object):
    SPARSE_WINDOW_SIZE = (8, 8)

    def __init__(self, pixel_graph):
        self.pixel_graph = pixel_graph

    def sparse_window_offset(self, edge):
        return (
            self.SPARSE_WINDOW_SIZE[0] / 2 - 1 - min((edge[0][0], edge[1][0])),
            self.SPARSE_WINDOW_SIZE[1] / 2 - 1 - min((edge[0][1], edge[1][1])))

    def apply(self, blocks):
        raise NotImplementedError()


class FullyConnectedHeuristics(DiagonalResolutionHeuristics):
    def apply(self, diagonal_pairs):
        """
        Iterate over the set of ambiguous diagonals and resolve them.
        """
        for edges in diagonal_pairs:
            self.weight_diagonals(*edges)

        for edges in diagonal_pairs:
            min_weight = min(e[2]['h_weight'] for e in edges)
            for edge in edges:
                if edge[2]['h_weight'] == min_weight:
                    self.pixel_graph.remove_edge(*edge[:2])
                else:
                    edge[2].pop('h_weight')

    def weight_diagonals(self, edge1, edge2):
        """
        Apply heuristics to ambiguous diagonals.
        """
        for edge in (edge1, edge2):
            self.weight_diagonal(edge)

    def weight_diagonal(self, edge):
        """
        Apply heuristics to an ambiguous diagonal.
        """
        weights = [
            self.weight_curve(edge),
            self.weight_sparse(edge),
            self.weight_island(edge),
            ]
        edge[2]['h_weight'] = sum(weights)

    def weight_curve(self, edge):
        """
        Weight diagonals based on curve length.

        Edges that are part of long single-pixel-wide features are
        more likely to be important.
        """
        seen_edges = set([cn_edge(edge)])
        nodes = list(edge[:2])

        while nodes:
            node = nodes.pop()
            edges = self.pixel_graph.edges(node, data=True)
            if len(edges) != 2:
                # This node is not part of a curve
                continue
            for edge in edges:
                edge = cn_edge(edge)
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    nodes.extend(n for n in edge if n != node)
        return len(seen_edges)

    def weight_sparse(self, edge):
        """
        Weight diagonals based on feature sparseness.

        Sparse features are more likely to be seen as "foreground"
        rather than "background", and are therefore likely to be more
        important.
        """

        nodes = list(edge[:2])
        seen_nodes = set(nodes)
        offset = self.sparse_window_offset(edge)

        while nodes:
            node = nodes.pop()
            for n in self.pixel_graph.neighbors(node):
                if n in seen_nodes:
                    continue
                if within_bounds(n, self.SPARSE_WINDOW_SIZE, offset=offset):
                    seen_nodes.add(n)
                    nodes.append(n)

        return -len(seen_nodes)

    def weight_island(self, edge):
        """
        Weight diagonals connected to "islands".

        Single pixels connected to nothing except the edge being
        examined are likely to be more important.
        """
        if (len(self.pixel_graph[edge[0]]) == 1
            or len(self.pixel_graph[edge[1]]) == 1):
            return 5
        return 0


class IterativeFinalShapeHeuristics(DiagonalResolutionHeuristics):
    def apply(self, diagonal_pairs):
        """
        Iterate over the set of ambiguous diagonals and resolve them.
        """
        new_pairs = []

        for edges in diagonal_pairs:
            for edge in edges:
                edge[2]['ambiguous'] = True

        for edges in diagonal_pairs:
            removals = self.weight_diagonals(*edges)
            if removals is None:
                # Nothing to remove, so we're still ambiguous.
                new_pairs.append(edges)
                continue

            for edge in edges:
                if edge in removals:
                    # Remove this edge
                    self.pixel_graph.remove_edge(edge[0], edge[1])
                else:
                    # Clean up other edges
                    edge[2].pop('h_weight')
                    edge[2].pop('ambiguous')

        # Reiterate if necessary.
        if not new_pairs:
            # Nothing more to do, let's go home.
            return
        elif new_pairs == diagonal_pairs:
            # No more unambiguous pairs.
            # TODO: Handle this gracefully.
            raise ValueError("No more unambiguous blocks.")
        else:
            # Try again.
            self.apply(new_pairs)

    def weight_diagonals(self, edge1, edge2):
        """
        Apply heuristics to ambiguous diagonals.
        """
        for edge in (edge1, edge2):
            self.weight_diagonal(edge)

        favour1 = edge1[2]['h_weight'][1] - edge2[2]['h_weight'][0]
        favour2 = edge1[2]['h_weight'][0] - edge2[2]['h_weight'][1]

        if favour1 == 0 and favour2 == 0:
            # Unambiguous, remove both.
            return (edge1, edge2)
        if favour1 >= 0 and favour2 >= 0:
            # Unambiguous, edge1 wins.
            return (edge2,)
        if favour1 <= 0 and favour2 <= 0:
            # Unambiguous, edge2 wins.
            return (edge1,)
        # We have an ambiguous result.
        return None

    def weight_diagonal(self, edge):
        """
        Apply heuristics to an ambiguous diagonal.
        """
        weights = [
            self.weight_curve(edge),
            self.weight_sparse(edge),
            self.weight_island(edge),
            ]
        edge[2]['h_weight'] = tuple(sum(w) for w in zip(*weights))

    def weight_curve(self, edge):
        """
        Weight diagonals based on curve length.

        Edges that are part of long single-pixel-wide features are
        more likely to be important.
        """
        seen_edges = set([cn_edge(edge)])
        nodes = list(edge[:2])

        values = list(self._weight_curve(nodes, seen_edges))
        retvals = (min(values), max(values))
        return retvals

    def _weight_curve(self, nodes, seen_edges):
        while nodes:
            node = nodes.pop()
            edges = self.pixel_graph.edges(node, data=True)
            if len(edges) != 2:
                # This node is not part of a curve
                continue
            for edge in edges:
                ambiguous = ('ambiguous' in edge[2])
                edge = cn_edge(edge)
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    if ambiguous:
                        for v in self._weight_curve(
                                nodes[:], seen_edges.copy()):
                            yield v
                    nodes.extend(n for n in edge if n != node)
        yield len(seen_edges)

    def weight_sparse(self, edge):
        """
        Weight diagonals based on feature sparseness.

        Sparse features are more likely to be seen as "foreground"
        rather than "background", and are therefore likely to be more
        important.
        """
        offset = self.sparse_window_offset(edge)
        nodes = list(edge[:2])
        seen_nodes = set(nodes)

        values = list(self._weight_sparse(offset, nodes, seen_nodes))
        retvals = (min(values), max(values))
        return retvals

    def _weight_sparse(self, offset, nodes, seen_nodes):
        while nodes:
            node = nodes.pop()
            for n in self.pixel_graph.neighbors(node):
                if n in seen_nodes:
                    continue
                if 'ambiguous' in self.pixel_graph[node][n]:
                    for v in self._weight_sparse(
                            offset, nodes[:], seen_nodes.copy()):
                        yield v
                if within_bounds(n, self.SPARSE_WINDOW_SIZE, offset):
                    seen_nodes.add(n)
                    nodes.append(n)

        yield -len(seen_nodes)

    def weight_island(self, edge):
        """
        Weight diagonals connected to "islands".

        Single pixels connected to nothing except the edge being
        examined are likely to be more important.
        """
        if (len(self.pixel_graph[edge[0]]) == 1
            or len(self.pixel_graph[edge[1]]) == 1):
            return (5, 5)
        return (0, 0)


class PixelData(object):
    """
    A representation of a pixel image that knows how to depixel it.

    :param data: A 2d array of pixel values. It is assumed to be rectangular.
    """

    HEURISTICS = FullyConnectedHeuristics
    # HEURISTICS = IterativeFinalShapeHeuristics

    def __init__(self, pixels):
        self.pixels = pixels
        self.size_x = len(pixels[0])
        self.size_y = len(pixels)
        self.size = (self.size_x, self.size_y)

    def depixel(self):
        """
        Depixel the image.

        TODO: document.
        """
        self.make_pixel_graph()
        self.remove_diagonals()
        self.make_grid_graph()
        self.deform_grid()
        self.make_shapes()
        self.isolate_outlines()
        self.add_shape_outlines()
        self.smooth_splines()

    def pixel(self, x, y):
        """
        Convenience method for getting a pixel value.
        """
        return self.pixels[y][x]

    def make_grid_graph(self):
        """
        Build a graph representing the pixel grid.
        """
        self.grid_graph = nx.grid_2d_graph(self.size_x + 1, self.size_y + 1)

    def make_pixel_graph(self):
        """
        Build a graph representing the pixel data.
        """
        self.pixel_graph = nx.Graph()

        for x, y in gen_coords(self.size):
            # While the nodes are created by adding edges, adding them
            # again is safe and lets us easily update metadata.
            corners = set([(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)])
            self.pixel_graph.add_node((x, y),
                                      value=self.pixel(x, y), corners=corners)
            # This gets called on each node, so we don't have to duplicate
            # edges.
            self._add_pixel_edge((x, y), (x + 1, y))
            self._add_pixel_edge((x, y), (x, y + 1))
            self._add_pixel_edge((x, y), (x + 1, y - 1))
            self._add_pixel_edge((x, y), (x + 1, y + 1))

    def _add_pixel_edge(self, pix0, pix1):
        """
        Add an edge to the pixel graph, checking bounds and tagging diagonals.
        """
        if within_bounds(pix1, self.size) and self.match(pix0, pix1):
            attrs = {'diagonal': pix0[0] != pix1[0] and pix0[1] != pix1[1]}
            self.pixel_graph.add_edge(pix0, pix1, **attrs)

    def match(self, pix0, pix1):
        """
        Check if two pixels match. By default, this tests equality.
        """
        return self.pixel(*pix0) == self.pixel(*pix1)

    def remove_diagonals(self):
        """
        Remove all unnecessary diagonals and resolve checkerboard features.

        We examine all 2x2 pixel blocks and check for overlapping diagonals.
        The only cases in which diagonals will overlap are fully-connected
        blocks (in which both diagonals can be removed) and checkerboard blocks
        (in which we need to apply heuristics to determine which diagonal to
        remove). See the paper for details.
        """
        ambiguous_diagonal_pairs = []

        for nodes in self.walk_pixel_blocks(2):
            edges = [e for e in self.pixel_graph.edges(nodes, data=True)
                     if e[0] in nodes and e[1] in nodes]

            diagonals = [e for e in edges if e[2]['diagonal']]
            if len(diagonals) == 2:
                if len(edges) == 6:
                    # We have a fully-connected block, so remove all diagonals.
                    for edge in diagonals:
                        self.pixel_graph.remove_edge(edge[0], edge[1])
                elif len(edges) == 2:
                    # We have an ambiguous pair to resolve.
                    ambiguous_diagonal_pairs.append(edges)
                else:
                    # If we get here, we have an invalid graph, possibly due to
                    # a faulty match function.
                    assert False, "Unexpected diagonal layout"

        self.apply_diagonal_heuristics(ambiguous_diagonal_pairs)

    def apply_diagonal_heuristics(self, ambiguous_diagonal_pairs):
        self.HEURISTICS(self.pixel_graph).apply(ambiguous_diagonal_pairs)

    def walk_pixel_blocks(self, size):
        """
        Walk the pixel graph in block of NxN pixels.

        This is useful for operating on a group of nodes at once.
        """
        for x, y in gen_coords((self.size_x - size + 1,
                                self.size_y - size + 1)):
            yield [(x + dx, y + dy)
                   for dx in range(size) for dy in range(size)]

    def deform_grid(self):
        """
        Deform the pixel grid based on the connections between similar pixels.
        """
        for node in self.pixel_graph.nodes_iter():
            self.deform_pixel(node)

        # Collapse all valence-2 nodes.
        removals = []
        for node in self.grid_graph.nodes_iter():
            if node in ((0, 0), (0, self.size[1]),
                        (self.size[0], 0), self.size):
                # Skip corner nodes.
                continue
            neighbors = self.grid_graph.neighbors(node)
            if len(neighbors) == 2:
                self.grid_graph.add_edge(*neighbors)
            if len(neighbors) <= 2:
                removals.append(node)

        # We can't do this above, because it would modify the dict
        # we're iterating.
        for node in removals:
            self.grid_graph.remove_node(node)

        # Update pixel corner sets.
        for node, attrs in self.pixel_graph.nodes_iter(data=True):
            corners = attrs['corners']
            for corner in corners.copy():
                if corner not in self.grid_graph:
                    corners.remove(corner)

    def deform_pixel(self, node):
        """
        Deform an individual pixel.
        """
        for neighbor in self.pixel_graph.neighbors(node):
            if node[0] == neighbor[0] or node[1] == neighbor[1]:
                # We only care about diagonals.
                continue
            px_x = max(neighbor[0], node[0])
            px_y = max(neighbor[1], node[1])
            pixnode = (px_x, px_y)
            offset_x = neighbor[0] - node[0]
            offset_y = neighbor[1] - node[1]
            # There's probably a better way to do this.
            adj_node = (neighbor[0], node[1])
            if not self.match(node, adj_node):
                pn = (px_x, px_y - offset_y)
                mpn = (px_x, px_y - 0.5 * offset_y)
                npn = (px_x + 0.25 * offset_x, px_y - 0.25 * offset_y)
                remove_from_set(self.pixel_corners(adj_node), pixnode)
                self.pixel_corners(adj_node).add(npn)
                self.pixel_corners(node).add(npn)
                self._deform(pixnode, pn, mpn, npn)
            adj_node = (node[0], neighbor[1])
            if not self.match(node, adj_node):
                pn = (px_x - offset_x, px_y)
                mpn = (px_x - 0.5 * offset_x, px_y)
                npn = (px_x - 0.25 * offset_x, px_y + 0.25 * offset_y)
                remove_from_set(self.pixel_corners(adj_node), pixnode)
                self.pixel_corners(adj_node).add(npn)
                self.pixel_corners(node).add(npn)
                self._deform(pixnode, pn, mpn, npn)

    def pixel_corners(self, pixel):
        return self.pixel_graph.node[pixel]['corners']

    def _deform(self, pixnode, pn, mpn, npn):
        # Do the node and edge shuffling.
        if mpn in self.grid_graph:
            self.grid_graph.remove_edge(mpn, pixnode)
        else:
            self.grid_graph.remove_edge(pn, pixnode)
            self.grid_graph.add_edge(pn, mpn)
        self.grid_graph.add_edge(mpn, npn)
        self.grid_graph.add_edge(npn, pixnode)

    def make_shapes(self):
        self.shapes = set()

        for pcg in nx.connected_component_subgraphs(self.pixel_graph):
            pixels = set()
            value = None
            corners = set()
            for pixel, attrs in pcg.nodes_iter(data=True):
                pixels.add(pixel)
                corners.update(attrs['corners'])
                value = attrs['value']
            self.shapes.add(Shape(pixels, value, corners))

    def isolate_outlines(self):
        # Remove internal edges from a copy of our pixgrid graph.
        self.outlines_graph = nx.Graph(self.grid_graph)
        for pixel, attrs in self.pixel_graph.nodes_iter(data=True):
            corners = attrs['corners']
            for neighbor in self.pixel_graph.neighbors(pixel):
                edge = corners & self.pixel_graph.node[neighbor]['corners']
                if len(edge) != 2:
                    print edge
                if self.outlines_graph.has_edge(*edge):
                    self.outlines_graph.remove_edge(*edge)
        for node in nx.isolates(self.outlines_graph):
            self.outlines_graph.remove_node(node)

    def make_path(self, graph):
        path = Path(graph)
        key = path.key()
        if key not in self.paths:
            self.paths[key] = path
            path.make_spline()
        return self.paths[key]

    def add_shape_outlines(self):
        self.paths = {}

        for shape in self.shapes:
            sg = self.outlines_graph.subgraph(shape.corners)
            for graph in nx.connected_component_subgraphs(sg):
                path = self.make_path(graph)
                if (min(graph.nodes()) == min(sg.nodes())):
                    shape.add_outline(path, True)
                else:
                    shape.add_outline(path)

    def smooth_splines(self):
        print "Smoothing splines..."
        for i, path in enumerate(self.paths.values()):
            print " * %s/%s (%s, %s)..." % (
                i + 1, len(self.paths), len(path.shapes), len(path.path))
            if len(path.shapes) == 1:
                path.smooth = path.spline.copy()
                continue
            path.smooth_spline()


class Shape(object):
    def __init__(self, pixels, value, corners):
        self.pixels = pixels
        self.value = value
        self.corners = corners
        self._outside_path = None
        self._inside_paths = []

    def _paths_attr(self, attr):
        paths = [list(reversed(getattr(self._outside_path, attr)))]
        paths.extend(getattr(path, attr) for path in self._inside_paths)

    @property
    def paths(self):
        paths = [list(reversed(self._outside_path.path))]
        paths.extend(path.path for path in self._inside_paths)
        return paths

    @property
    def splines(self):
        paths = [self._outside_path.spline.reversed()]
        paths.extend(path.spline for path in self._inside_paths)
        return paths

    @property
    def smooth_splines(self):
        paths = [self._outside_path.smooth.reversed()]
        paths.extend(path.smooth for path in self._inside_paths)
        return paths

    def add_outline(self, path, outside=False):
        if outside:
            self._outside_path = path
        else:
            self._inside_paths.append(path)
        path.shapes.add(self)


class Path(object):
    def __init__(self, shape_graph):
        self.path = self._make_path(shape_graph)
        self.shapes = set()

    def key(self):
        return tuple(self.path)

    def _make_path(self, shape_graph):
        # Find initial nodes.
        nodes = set(shape_graph.nodes())
        path = [min(nodes)]
        neighbors = sorted(shape_graph.neighbors(path[0]),
                           key=lambda p: gradient(path[0], p))
        path.append(neighbors[0])
        nodes.difference_update(path)

        # Walk rest of nodes.
        while nodes:
            for neighbor in shape_graph.neighbors(path[-1]):
                if neighbor in nodes:
                    nodes.remove(neighbor)
                    path.append(neighbor)
                    break
        return path

    def make_spline(self):
        self.spline = bspline.polyline_to_closed_bspline(self.path)

    def smooth_spline(self):
        self.smooth = bspline.smooth_spline(self.spline)
