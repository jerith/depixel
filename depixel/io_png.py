import png

from depixel.io_data import PixelDataWriter


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

    def pixel(self, x, y):
        return self.pixels[y][x]

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
                frow.extend(value)
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
        old_colour = self.pixels[point[1]][point[0]]
        if old_colour == colour:
            return
        self.fill_scan(point, old_colour, colour)

    def fill_pix(self, point, old_colour, colour):
        """
        Pixel flood-fill. Reliable, but slow.
        """
        to_fill = [point]
        while to_fill:
            x, y = to_fill.pop()
            self.set_pixel(x, y, colour)
            for nx, ny in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                if 0 <= nx < self.size[0] and 0 <= ny < self.size[1]:
                    if self.pixels[ny][nx] == old_colour:
                        to_fill.append((nx, ny))

    def fill_scan(self, point, old_colour, colour):
        """
        Scanline flood-fill. Fast, but I'm not entirely sure what it's doing.
        """
        to_fill = [point]
        while to_fill:
            x, y = to_fill.pop()
            while y > 0 and self.pixel(x, y - 1) == old_colour:
                y -= 1
            lspan = False
            rspan = False
            while y < self.size[1] and self.pixel(x, y) == old_colour:
                self.set_pixel(x, y, colour)

                if not lspan and x > 0 and self.pixel(x - 1, y) == old_colour:
                    to_fill.append((x - 1, y))
                    lspan = True
                elif lspan and x > 0 and self.pixel(x - 1, y) == old_colour:
                    lspan = False

                if (not rspan and x < self.size[0] - 1
                      and self.pixel(x + 1, y) == old_colour):
                    to_fill.append((x + 1, y))
                    rspan = True
                elif (rspan and x < self.size[0] - 1
                      and self.pixel(x + 1, y) == old_colour):
                    rspan = False

                y += 1


class PixelDataPngWriter(PixelDataWriter):
    FILE_EXT = 'png'

    def translate_pixel(self, pixel):
        if not isinstance(pixel, (list, tuple)):
            # Assume monochrome values normalised to [0, 1].
            return (int(255 * pixel),) * 3
        return pixel

    def make_drawing(self, drawing_type, _filename):
        if drawing_type == 'pixels':
            return Bitmap(self.pixel_data.size)
        return Bitmap((self.pixel_data.size_x * self.PIXEL_SCALE + 1,
                       self.pixel_data.size_y * self.PIXEL_SCALE + 1),
                      bgcolour=(127, 127, 127))

    def save_drawing(self, drawing, filename):
        drawing.write_png(filename)

    def draw_pixel(self, drawing, pt, colour):
        drawing.set_pixel(pt[0], pt[1], self.translate_pixel(colour))

    def draw_line(self, drawing, pt0, pt1, colour):
        drawing.draw_line(pt0, pt1, self.translate_pixel(colour))

    def draw_polygon(self, drawing, path, colour, fill):
        pt0 = path[-1]
        for pt1 in path:
            self.draw_line(drawing, pt0, pt1, colour)
            pt0 = pt1
        middle = (sum([p[0] for p in path]) / len(path),
                  sum([p[1] for p in path]) / len(path))
        drawing.fill(middle, fill)

    def draw_path_shape(self, drawing, paths, colour, fill):
        for path in paths:
            pt0 = path[-1]
            for pt1 in path:
                self.draw_line(drawing, pt0, pt1, colour)
                pt0 = pt1
        drawing.fill(self.find_point_within(paths, fill), fill)

    def find_point_within(self, paths, colour):
        for node, attrs in self.pixel_data.pixel_graph.nodes_iter(data=True):
            if colour == attrs['value']:
                pt = self.scale_pt(node, (0.5, 0.5))
                if self.is_inside(pt, paths):
                    return pt

    def is_inside(self, pt, paths):
        if not self._is_inside(pt, paths[0]):
            # Must be inside the "outside" path.
            return False
        for path in paths[1:]:
            if self._is_inside(pt, path):
                # Must be outside the "inside" paths.
                return False
        return True

    def _is_inside(self, pt, path):
        inside = False
        x, y = pt
        x0, y0 = path[-1]
        for x1, y1 in path:
            if (y0 <= y < y1 or y1 <= y < y0) and (x0 <= x or x1 <= x):
                # This crosses our ray.
                if (x1 + float(y - y1) / (y0 - y1) * (x0 - x1)) < x:
                    inside = not inside
            x0, y0 = x1, y1
        return inside

    def draw_shapes(self, drawing, element=None):
        for shape in self.pixel_data.shapes:
            paths = [[self.scale_pt(p) for p in path]
                     for path in shape['paths']]
            self.draw_path_shape(
                drawing, paths, self.GRID_COLOUR, shape['value'])


def read_png(filename):
    _w, _h, pixels, _meta = png.Reader(filename=filename).asRGB8()
    data = []
    for row in pixels:
        d_row = []
        while row:
            d_row.append((row.pop(0), row.pop(0), row.pop(0)))
        data.append(d_row)
    return data
