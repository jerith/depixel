"""
Unified I/O module for reading and writing various formats.
"""

import os.path
from itertools import product


def gradient(p0, p1):
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    if dx == 0:
        return dy * 99999999999999
    return 1.0 * dy / dx


class PixelDataWriter(object):
    PIXEL_SCALE = 40
    GRID_COLOUR = (255, 127, 0)

    FILE_EXT = 'out'

    def __init__(self, pixel_data, name, scale=None, gridcolour=None):
        self.name = name
        self.pixel_data = pixel_data
        if scale:
            self.PIXEL_SCALE = scale
        if gridcolour:
            self.GRID_COLOUR = gridcolour

    def scale_pt(self, pt, offset=(0, 0)):
        return tuple(int((n + o) * self.PIXEL_SCALE)
                     for n, o in zip(pt, offset))

    def export_pixels(self, outdir):
        filename = self.mkfn(outdir, 'pixels')
        drawing = self.make_drawing('pixels', filename)
        for pt in product(range(self.pixel_data.size_x),
                          range(self.pixel_data.size_y)):
            self.draw_pixel(drawing, pt, self.pixel_data.pixel(*pt))
        self.save_drawing(drawing, filename)

    def export_grid(self, outdir, node_graph=True):
        filename = self.mkfn(outdir, 'grid')
        drawing = self.make_drawing('grid', filename)
        self.draw_pixgrid(drawing)
        if node_graph:
            self.draw_nodes(drawing)
        self.save_drawing(drawing, filename)

    def export_shapes(self, outdir, node_graph=True):
        filename = self.mkfn(outdir, 'shapes')
        drawing = self.make_drawing('shapes', filename)
        self.draw_shapes(drawing, 'splines')
        if node_graph:
            self.draw_nodes(drawing)
        self.save_drawing(drawing, filename)

    def export_smooth(self, outdir, node_graph=True):
        filename = self.mkfn(outdir, 'smooth')
        drawing = self.make_drawing('smooth', filename)
        self.draw_shapes(drawing, 'smooth_splines')
        if node_graph:
            self.draw_nodes(drawing)
        self.save_drawing(drawing, filename)

    def draw_pixgrid(self, drawing):
        for pixel, attrs in self.pixel_data.pixel_graph.nodes_iter(data=True):
            nodes = attrs['corners'].copy()
            path = [nodes.pop()]
            while nodes:
                for neighbor in self.pixel_data.grid_graph.neighbors(path[-1]):
                    if neighbor in nodes:
                        nodes.remove(neighbor)
                        path.append(neighbor)
                        break
            self.draw_polygon(drawing, [self.scale_pt(p) for p in path],
                              self.GRID_COLOUR, attrs['value'])

    def draw_shapes(self, drawing, element='smooth_splines'):
        for shape in self.pixel_data.shapes:
            paths = getattr(shape, element)
            self.draw_spline_shape(
                drawing, paths, self.GRID_COLOUR, shape.value)

    def draw_nodes(self, drawing):
        for edge in self.pixel_data.pixel_graph.edges_iter():
            self.draw_line(drawing,
                           self.scale_pt(edge[0], (0.5, 0.5)),
                           self.scale_pt(edge[1], (0.5, 0.5)),
                           self.edge_colour(edge[0]))

    def edge_colour(self, node):
        return {
            0: (0, 191, 0),
            0.5: (191, 0, 0),
            1: (0, 0, 255),
            (0, 0, 0): (0, 191, 0),
            (127, 127, 127): (191, 0, 0),
            (255, 255, 255): (0, 0, 255),
            }[self.pixel_data.pixel_graph.node[node]['value']]

    def mkfn(self, outdir, drawing_type):
        return os.path.join(
            outdir, "%s_%s.%s" % (drawing_type, self.name, self.FILE_EXT))

    def make_drawing(self, drawing_type, filename):
        raise NotImplementedError("This Writer cannot make a drawing.")

    def save_drawing(self, filename):
        raise NotImplementedError("This Writer cannot save a drawing.")

    def draw_pixel(self, drawing, pt, colour):
        raise NotImplementedError("This Writer cannot draw a pixel.")

    def draw_rect(self, drawing, p0, size, colour, fill):
        raise NotImplementedError("This Writer cannot draw a rect.")

    def draw_line(self, drawing, p0, p1, colour):
        raise NotImplementedError("This Writer cannot draw a line.")

    def draw_path_shape(self, drawing, paths, colour, fill):
        raise NotImplementedError("This Writer cannot draw a path shape.")

    def draw_spline_shape(self, drawing, paths, colour, fill):
        raise NotImplementedError("This Writer cannot draw a spline shape.")


def get_writer(data, basename, filetype):
    # Circular imports, but they're safe because they're in this function.
    if filetype == 'png':
        from depixel import io_png
        return io_png.PixelDataPngWriter(data, basename)

    if filetype == 'svg':
        from depixel import io_svg
        return io_svg.PixelDataSvgWriter(data, basename)

    raise NotImplementedError(
        "I don't recognise '%s' as a file type." % (filetype,))


def read_pixels(filename, filetype=None):
    if filetype is None:
        filetype = os.path.splitext(filename)[-1].lstrip('.')

    if filetype == 'png':
        from depixel.io_png import read_png
        return read_png(filename)
