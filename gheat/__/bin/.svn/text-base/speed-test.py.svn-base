#!/usr/bin/env python
"""Set up and run a profiling scenario for gheat.

Usage:

    speed-test.py <backend> [<iterations>]

The output will be a cProfile report. <iterations> defaults to 1. The expensive
part is tile rebuilding, so we isolate that here.

"""
import cProfile
import os
import pstats
import sys

import aspen; aspen.configure()
import gheat


# Parse and validate command line arguments.
# ==========================================

USAGE = "Usage: speed-test.py <backend> [<iterations>]"

if len(sys.argv) < 2:
    print >> sys.stderr, USAGE
    raise SystemExit
image_library = sys.argv[1].lower()
assert image_library in ('pygame', 'pil'), "bad image library"
if image_library == 'pygame':
    from gheat import pygame_ as backend
elif image_library == 'pil':
    from gheat import pil_ as backend

try:
    iterations = int(sys.argv[2])
except IndexError:
    iterations = 1 


# Set up the test.
# ================
# This depends on our default data set for a juicy tile.

color_path = os.path.join(aspen.paths.__, 'etc', 'color-schemes', 'classic.png')
color_scheme = backend.ColorScheme('classic', color_path)
dots = gheat.load_dots(backend)
tile = backend.Tile(color_scheme, dots, 4, 4, 6, 'foo.png')

def test():
    for i in range(iterations):
        tile.rebuild()


# Run it.
# =======

cProfile.run('test()', 'stats.txt')
p = pstats.Stats('stats.txt')
p.strip_dirs().sort_stats('time').print_stats()
os.remove('stats.txt')

