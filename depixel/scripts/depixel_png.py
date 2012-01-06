#!/usr/bin/env python

from optparse import OptionParser
import os.path

from depixel import io_data
from depixel.depixeler import PixelData


def parse_options():
    parser = OptionParser(usage="usage: %prog [options] file [file [...]]")
    parser.add_option('--no-pixgrid', help="Suppress pixel grid output.",
                      dest="draw_grid", action="store_false", default=True)
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
    if options.write_pixels:
        if options.to_png:
            print "    Writing pixels PNG..."
            writer = io_data.get_writer(data, base_filename, 'png')
            writer.export_pixels(outdir)
        if options.to_svg:
            print "    Writing pixels SVG..."
            writer = io_data.get_writer(data, base_filename, 'svg')
            writer.export_pixels(outdir)
    if options.draw_grid or options.draw_nodes:
        print "    Depixeling..."
        data.depixel()
        if options.to_png:
            print "    Writing depixeled PNG..."
            writer = io_data.get_writer(data, base_filename, 'png')
            writer.export_grid(outdir, options.draw_grid, options.draw_nodes)
        if options.to_svg:
            print "    Writing depixeled SVG..."
            writer = io_data.get_writer(data, base_filename, 'svg')
            writer.export_grid(outdir, options.draw_grid, options.draw_nodes)
    print "    Done."


def main():
    options, args = parse_options()
    for filename in args:
        process_file(options, filename)


if __name__ == '__main__':
    main()
