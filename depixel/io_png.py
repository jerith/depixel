import png


class Bitmap(object):
    mode = 'RGB'
    bgcolour = (127, 127, 127)

    def __init__(self, size, bgcolour=None, mode=None):
        if bgcolour is not None:
            self.bgcolour = bgcolour
        if mode is not None:
            self.mode = mode
        self.size = size
        self.pixels = []
        for _ in range(self.size[1]):
            self.pixels.append([bgcolour] * self.size[0])

    def set_pixel(self, x, y, value):
        self.pixels[y][x] = value

    def set_data(self, data):
        assert len(data) == self.size[1]
        new_pixels = []
        for row in data:
            assert len(row) == self.size[0]
            new_pixels.append(row[:])
        self.pixels = new_pixels

    def set_block(self, x, y, data):
        assert 0 <= x <= (self.size[0] - len(data[0]))
        assert 0 <= y <= (self.size[1] - len(data))
        for dy, row in enumerate(data):
            for dx, value in enumerate(row):
                self.set_pixel(x + dx, y + dy, value)

    def flat_pixels(self):
        flat_pixels = []
        for row in self.pixels:
            frow = []
            for value in row:
                frow.extend(list(value))
            flat_pixels.append(frow)
        return flat_pixels

    def write_png(self, filename):
        png.from_array(self.flat_pixels(), mode=self.mode).save(filename)

    def draw_line(self, p0, p1, colour):
        """Bresenham's line algorithm."""

        x0, y0 = p0
        x1, y1 = p1
        dx = abs(x0 - x1)
        dy = abs(y0 - y1)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while (x0, y0) != (x1, y1):
            self.set_pixel(x0, y0, colour)
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += + sx
            if e2 < dx:
                err += dx
                y0 += sy
        self.set_pixel(x1, y1, colour)

    def fill(self, point, colour):
        start_colour = self.pixels[point[1]][point[0]]
        to_fill = [point]
        while to_fill:
            x, y = to_fill.pop()
            self.set_pixel(x, y, colour)
            for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                if 0 <= nx < self.size[0] and 0 <= ny < self.size[1]:
                    if self.pixels[ny][nx] == start_colour:
                        to_fill.append((nx, ny))


class PixelDataPngWriter(object):
    PIXEL_MULTIPLIER = 40
    GRID_COLOUR = (127, 127, 127)
    PIXGRID_COLOUR = (255, 127, 0)

    def __init__(self, pixel_data):
        self.pixel_data = pixel_data

    def translate_pixel(self, pixel):
        if pixel in [0, 1]:
            # Assume we have binary pixel values.
            return (255 * pixel) * 3
        return pixel

    def translate_pixels(self, pixels):
        return [[self.translate_pixel(p) for p in row] for row in pixels]

    def export_pixels_png(self, filename):
        bitmap = Bitmap(self.pixel_data.size)
        bitmap.set_data(self.translate_pixels(self.pixel_data.pixels))
        bitmap.write_png(filename)

    def node_centre(self, node):
        return (node[0] * self.PIXEL_MULTIPLIER + self.PIXEL_MULTIPLIER / 2,
                node[1] * self.PIXEL_MULTIPLIER + self.PIXEL_MULTIPLIER / 2)

    def export_nodes_png(self, filename, pixgrid=True, nodes=True):
        bitmap = self.make_big_bitmap()
        if pixgrid:
            self.draw_pixgrid(bitmap)
        if nodes:
            self.draw_nodes(bitmap)
        bitmap.write_png(filename)

    def make_big_bitmap(self):
        return Bitmap((self.pixel_data.size_x * self.PIXEL_MULTIPLIER + 1,
                       self.pixel_data.size_y * self.PIXEL_MULTIPLIER + 1),
                      bgcolour=self.GRID_COLOUR)

    def scale_pt(self, pt):
        return tuple(int(n * self.PIXEL_MULTIPLIER) for n in pt)

    def draw_pixgrid(self, bitmap):
        pg = self.pixel_data.grid_graph
        for edge in pg.edges_iter():
            bitmap.draw_line(self.scale_pt(edge[0]), self.scale_pt(edge[1]),
                             self.PIXGRID_COLOUR)
        for node, attrs in self.pixel_data.pixel_graph.nodes_iter(data=True):
            bitmap.fill(self.scale_pt((node[0] + 0.5, node[1] + 0.5)),
                        self.translate_pixel(attrs['value']))

    def draw_nodes(self, bitmap):
        for edge in self.pixel_data.pixel_graph.edges_iter():
            bitmap.draw_line(self.node_centre(edge[0]),
                             self.node_centre(edge[1]),
                             self.edge_colour(edge[0]))

    def edge_colour(self, node):
        return {
            0: (0, 127, 0),
            1: (0, 0, 255),
            (0, 0, 0): (0, 191, 0),
            (255, 255, 255): (0, 0, 255),
            }[self.pixel_data.pixel_graph.node[node]['value']]


def export_png(pixel_data, basename):
    fn = "pixels_%s.png" % (basename,)
    PixelDataPngWriter(pixel_data).export_pixels_png(fn)


def export_nodes_png(pixel_data, basename, pixel_grid=True, node_graph=True):
    fn = "nodes_%s.png" % (basename,)
    PixelDataPngWriter(pixel_data).export_nodes_png(fn, pixel_grid, node_graph)


def read_png(filename):
    _w, _h, pixels, _meta = png.Reader(filename=filename).asRGB8()
    data = []
    for row in pixels:
        d_row = []
        while row:
            d_row.append((row.pop(0), row.pop(0), row.pop(0)))
        data.append(d_row)
    return data
