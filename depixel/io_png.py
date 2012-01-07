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


class PixelDataPngWriter(PixelDataWriter):
    FILE_EXT = 'png'

    def translate_pixel(self, pixel):
        if pixel in [0, 1]:
            # Assume we have binary pixel values.
            return (255 * pixel) * 3
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


def read_png(filename):
    _w, _h, pixels, _meta = png.Reader(filename=filename).asRGB8()
    data = []
    for row in pixels:
        d_row = []
        while row:
            d_row.append((row.pop(0), row.pop(0), row.pop(0)))
        data.append(d_row)
    return data
