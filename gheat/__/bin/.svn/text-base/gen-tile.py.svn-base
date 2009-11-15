#!/usr/bin/env python
"""Generate gheat tiles.
"""
import math
import os
import sys
from os.path import join

import aspen
root = aspen.find_root()
aspen.configure(['--root', root])

from gmerc import ll2px
from gheat import pil_ as backend


color_schemes = dict()          # this is used below
_color_schemes_dir = os.path.join(aspen.paths.__, 'etc', 'color-schemes')
for fname in os.listdir(_color_schemes_dir):
    if not fname.endswith('.png'):
        continue
    name = os.path.splitext(fname)[0]
    fspath = os.path.join(_color_schemes_dir, fname)
    color_schemes[name] = backend.ColorScheme(name, fspath)


def load_dots(backend):
    """Given a backend module, return a mapping of zoom level to Dot object.
    """
    return dict([(zoom, backend.Dot(zoom)) for zoom in range(20)])
dots = load_dots(backend) # factored for easier use from scripts


for zoom in [0,1,2,3,4]:
    width, height = ll2px(-90, 180, zoom)
    numcols = int(math.ceil(width / 256.0))
    numrows = int(math.ceil(height / 256.0))
    cs_name = 'classic'
    color_scheme = color_schemes[cs_name]
    for x in range(numcols):
        for y in range(numrows):
            fspath = join( aspen.paths.root
                         , cs_name
                         , str(zoom)
                         , "%d,%d" % (x, y)
                          ) + '.png'
            tile = backend.Tile(color_scheme, dots, zoom, x, y, fspath)
            sys.stdout.write('tile %s\n' % fspath); sys.stdout.flush()
            if tile.is_empty():
                sys.stdout.write('skipping empty tile %s\n' % fspath)
                sys.stdout.flush()
            elif tile.is_stale():
                sys.stdout.write('rebuilding tile %s\n' % fspath)
                sys.stdout.flush()
                tile.rebuild()
                tile.save()
            else:
                sys.stdout.write('skipping cached tile %s\n' % fspath)
                sys.stdout.flush()
