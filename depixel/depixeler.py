# -*- test-case-name: depixel.tests.test_depixeler -*-

"""
An implementation of the Depixelizing Pixel Art algorithm.

The paper can be found online at:
    http://research.microsoft.com/en-us/um/people/kopf/pixelart/
"""

from math import sqrt

import networkx as nx


def gen_coords(size):
    for y in xrange(size[1]):
        for x in xrange(size[0]):
            yield (x, y)


def within_bounds(coord, size):
    x, y = coord
    size_x, size_y = size
    return (0 <= x < size_x and 0 <= y < size_y)


def cn_edge(edge):
    return tuple(sorted(edge[:2]))


def distance(p0, p1):
    return sqrt((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)


class PixelData(object):
    """
    A representation of a pixel image that knows how to depixel it.

    :param data: A 2d array of pixel values. It is assumed to be rectangular.
    """
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
            self.pixel_graph.add_node((x, y), value=self.pixel(x, y))
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
            self.pixel_graph.add_edge(pix0, pix1, diagonal=(
                    pix0[0] != pix1[0] and pix0[1] != pix1[1]))

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
                    # We have a checkerboard, so apply heuristics.
                    self.handle_checkerboard_diagonals(edges)
                else:
                    # If we get here, we have an invalid graph, possibly due to
                    # a faulty match function.
                    assert False, "Unexpected diagonal layout"

    def handle_checkerboard_diagonals(self, edges):
        """
        Apply heuristicts and remove less important diagonal.
        """
        for edge in edges:
            weights = [
                    self.weight_curve(edge),
                    self.weight_sparse(edge),
                    self.weight_island(edge),
                    ]
            edge[2]['h_weight'] = sum(weights)
        min_weight = min(e[2]['h_weight'] for e in edges)
        for edge in edges:
            if edge[2]['h_weight'] == min_weight:
                self.pixel_graph.remove_edge(edge[0], edge[1])
            else:
                # Clean up after ourselves.
                edge[2].pop('h_weight')

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
            edges = self.pixel_graph.edges(node)
            if len(edges) != 2:
                # This node is not part of a curve
                continue
            for e in edges:
                e = cn_edge(e)
                if e not in seen_edges:
                    seen_edges.add(e)
                    nodes.extend(n for n in e if n != node)

        return len(seen_edges)

    def weight_sparse(self, edge):
        """
        Weight diagonals based on feature sparseness.

        Sparse features are more likely to be seen as "foreground"
        rather than "background", and are therefore likely to be more
        important.
        """
        window_size = (8, 8)
        offset_x = 3 - min(edge[0][0], edge[1][0])
        offset_y = 3 - min(edge[0][1], edge[1][1])

        nodes = [edge[0]]
        seen_nodes = set(nodes)

        while nodes:
            node = nodes.pop()
            for x, y in self.pixel_graph.neighbors(node):
                if (x, y) in seen_nodes:
                    continue
                if within_bounds((x + offset_x, y + offset_y), window_size):
                    seen_nodes.add((x, y))
                    nodes.append((x, y))

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
            if not self.match(node, (neighbor[0], node[1])):
                pn = (px_x, px_y - offset_y)
                mpn = (px_x, px_y - 0.5 * offset_y)
                npn = (px_x + 0.25 * offset_x, px_y - 0.25 * offset_y)
                self._deform(pixnode, pn, mpn, npn)
            if not self.match(node, (node[0], neighbor[1])):
                pn = (px_x - offset_x, px_y)
                mpn = (px_x - 0.5 * offset_x, px_y)
                npn = (px_x - 0.25 * offset_x, px_y + 0.25 * offset_y)
                self._deform(pixnode, pn, mpn, npn)

    def _deform(self, pixnode, pn, mpn, npn):
        # Do the node and edge shuffling.
        if mpn in self.grid_graph:
            self.grid_graph.remove_edge(mpn, pixnode)
        else:
            self.grid_graph.remove_edge(pn, pixnode)
            self.grid_graph.add_edge(pn, mpn)
        self.grid_graph.add_edge(mpn, npn)
        self.grid_graph.add_edge(npn, pixnode)
