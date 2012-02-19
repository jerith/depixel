#!/usr/bin/env python

from optparse import OptionParser
import os.path

from depixel import io_data
from depixel.depixeler import PixelData


def parse_options():
    parser = OptionParser(usage="usage: %prog [options] file [file [...]]")
    parser.add_option('--write-grid', help="Write pixel grid file.",
                      dest="write_grid", action="store_true", default=False)
    parser.add_option('--write-shapes', help="Write object shapes file.",
                      dest="write_shapes", action="store_true", default=False)
    parser.add_option('--write-smooth', help="Write smooth shapes file.",
                      dest="write_smooth", action="store_true", default=False)
    parser.add_option('--no-nodes', help="Suppress pixel node graph output.",
                      dest="draw_nodes", action="store_false", default=True)
    parser.add_option('--write-pixels', help="Write pixel file.",
                      dest="write_pixels", action="store_true", default=False)
    parser.add_option('--to-png', help="Write PNG output.",
                      dest="to_png", action="store_true", default=False)
    parser.add_option('--to-svg', help="Write SVG output.",
                      dest="to_svg", action="store_true", default=False)
    parser.add_option('--output-dir', metavar='DIR', default=".",
                      help="Directory for output files. [%default]",
                      dest="output_dir", action="store")

    options, args = parser.parse_args()
    if not args:
        parser.error("You must provide at least one input file.")

    return options, args


def process_file(options, filename):
    print "Processing %s..." % (filename,)
    data = PixelData(io_data.read_pixels(filename, 'png'))
    base_filename = os.path.splitext(os.path.split(filename)[-1])[0]
    outdir = options.output_dir

    filetypes = []
    if options.to_png:
        filetypes.append('PNG')
    if options.to_svg:
        filetypes.append('SVG')

    if options.write_pixels:
        for ft in filetypes:
            print "    Writing pixels %s..." % (ft,)
            writer = io_data.get_writer(data, base_filename, ft.lower())
            writer.export_pixels(outdir)

    data.depixel()

    if options.write_grid:
        for ft in filetypes:
            print "    Writing grid %s..." % (ft,)
            writer = io_data.get_writer(data, base_filename, ft.lower())
            writer.export_grid(outdir, options.draw_nodes)

    if options.write_shapes:
        for ft in filetypes:
            print "    Writing shapes %s..." % (ft,)
            writer = io_data.get_writer(data, base_filename, ft.lower())
            writer.export_shapes(outdir, options.draw_nodes)

    if options.write_smooth:
        for ft in filetypes:
            print "    Writing smooth shapes %s..." % (ft,)
            writer = io_data.get_writer(data, base_filename, ft.lower())
            writer.export_smooth(outdir, options.draw_nodes)


def main():
    options, args = parse_options()
    for filename in args:
        process_file(options, filename)


if __name__ == '__main__':
    main()
