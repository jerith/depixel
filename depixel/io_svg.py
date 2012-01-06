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

    def draw_pixgrid(self, drawing):
        pg = self.pixel_data.grid_graph
        for edge in pg.edges_iter():
            self.draw_line(drawing,
                           self.scale_pt(edge[0]),
                           self.scale_pt(edge[1]),
                           self.GRID_COLOUR)
        # for node, attrs in self.pixel_data.pixel_graph.nodes_iter(data=True):
        #     bitmap.fill(self.scale_pt((node[0] + 0.5, node[1] + 0.5)),
        #                 self.translate_pixel(attrs['value']))
