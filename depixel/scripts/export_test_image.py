#!/usr/bin/env python

from optparse import OptionParser

from depixel import io_data
from depixel.depixeler import PixelData
from depixel.tests import test_depixeler


def parse_options():
    parser = OptionParser(usage="usage: %prog [options] name")
    parser.add_option('--output-dir', metavar='DIR', default=".",
                      help="Directory for output files. [%default]",
                      dest="output_dir", action="store")

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error("You must provide exactly one test image name.")

    return options, args


def export_image(options, name):
    name = name.upper()
    print "Processing %s..." % (name,)
    data = PixelData(test_depixeler.mkpixels(getattr(test_depixeler, name)))
    base_filename = name.lower()
    outdir = options.output_dir

    print "    Writing pixels PNG..."
    writer = io_data.get_writer(data, base_filename, 'png')
    writer.export_pixels(outdir)


def main():
    options, args = parse_options()
    export_image(options, args[0])


if __name__ == '__main__':
    main()
