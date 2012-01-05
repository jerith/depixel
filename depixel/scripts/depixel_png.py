#!/usr/bin/env python

from optparse import OptionParser
import os.path

from depixel import io_png
from depixel.depixel import PixelData


def parse_options():
    parser = OptionParser(usage="usage: %prog [options] file [file [...]]")
    parser.add_option('--no-pixgrid', help="Suppress pixel grid output.",
                      dest="draw_pixgrid", action="store_false", default=True)
    parser.add_option('--no-nodes', help="Suppress pixel node graph output.",
                      dest="draw_nodes", action="store_false", default=True)
    parser.add_option('--write-pixels', help="Write pixel file.",
                      dest="write_pixels", action="store_true", default=False)

    options, args = parser.parse_args()
    if not args:
        parser.error("You must provide at least one input file.")

    return options, args


def process_file(options, filename):
    print "Processing %s..." % (filename,)
    data = PixelData(io_png.read_png(filename))
    base_filename = os.path.splitext(os.path.split(filename)[-1])[0]
    if options.write_pixels:
        print "    Writing pixels..."
        io_png.export_png(data, base_filename)
    if options.draw_pixgrid or options.draw_nodes:
        print "    Depixeling..."
        data.depixel()
        print "    Writing depixeled data..."
        io_png.export_nodes_png(data, base_filename,
                                options.draw_pixgrid, options.draw_nodes)
    print "    Done."


def main():
    options, args = parse_options()
    for filename in args:
        process_file(options, filename)


if __name__ == '__main__':
    main()
