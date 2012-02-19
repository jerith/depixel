This is an implementation of the "Depixelizing Pixel Art" algorithm:

  http://research.microsoft.com/en-us/um/people/kopf/pixelart/

This code is provided under the MIT license, the full text of which is in the
LICENSE file. As far as I know, the algorithm is not covered by any patents or
restrictive copyright.

This is very much a work in progress at present. My primary aim is to build a
tool to generate outline fonts from low-resolution bitmap fonts, but that isn't
ready yet.

So far I have the basic pixel grid deformation, shape outline extraction and
somewhat wonky curve smoothing implemented and I can write representations of
the intermediate steps to PNG and SVG. (The curve smoothing is pretty
experimental, and probably full of exciting bugs. It also operates on each
shape individually, so there's weirdness along the edges.)

There is a handy script to depixel PNGs in the `depixel/scripts` directory, and
there are unit tests covering some of the code.

I like to keep dependencies small and light, but there are some useful bits
I've pulled in (or will pull in) to make life easier:

 * I use `networkx` to do the graph stuff, because implementing it myself was
   getting messy. Switching to a more special-purpose graph library might give
   some performance benefits, but that's fairly low down my priority list at
   present.

 * I use `pypng` to do the PNG reading and writing, but that's isolated in the
   things that need it and the actual depixeling code works fine without it.

 * I use `svgwrite` to do the SVG writing, but that's isolated in the things
   that need it and the actual depixeling code works fine without it.

 * I'm probably going to need `bdflib` once I start working with fonts. Like
   the PNG stuff, I'll restrict its use to the places that need it. Since BDF
   is a fairly simple format and this library doesn't play nice with pip, I may
   rewrite the bits I need here as well.

 * I use Twisted's trial testrunner to run the tests, but that isn't required
   as long as you're happy to figure out how to discover and run the test cases
   yourself. (I think nose or something should work as well. I just like
   Twisted, and I had some editor hooks set up to use trial for other
   projects.)
