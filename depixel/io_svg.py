from svgwrite import Drawing

from depixel.io_data import PixelDataWriter


def rgb(rgb):
    return "rgb(%s,%s,%s)" % rgb


class PixelDataSvgWriter(PixelDataWriter):
    FILE_EXT = 'svg'

    def make_drawing(self, _drawing_type, filename):
        return Drawing(filename)

    def save_drawing(self, drawing, _drawing_type):
        drawing.save()

    def draw_pixel(self, drawing, pt, colour):
        drawing.add(drawing.rect(self.scale_pt(pt), self.scale_pt((1, 1)),
                                 stroke=rgb(colour), fill=rgb(colour)))

    def draw_line(self, drawing, pt0, pt1, colour):
        drawing.add(drawing.line(pt0, pt1, stroke=rgb(colour)))

    def draw_polygon(self, drawing, path, colour, fill):
        drawing.add(drawing.polygon(path, stroke=rgb(colour), fill=rgb(fill)))

    def draw_path_shape(self, drawing, paths, colour, fill):
        dpath = []
        for path in paths:
            dpath.append('M')
            dpath.extend(path)
            dpath.append('Z')
        drawing.add(drawing.path(dpath, stroke=rgb(colour), fill=rgb(fill)))
