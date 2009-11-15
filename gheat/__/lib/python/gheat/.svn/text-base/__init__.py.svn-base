import logging
import os
try:
    from pysqlite2 import dbapi2 as sqlite3 # custom or OS-packaged version
except ImportError:
    import sqlite3                          # stock Python 2.5+ stdlib version
import stat

import aspen
if not aspen.CONFIGURED: # for tests
    aspen.configure()
from aspen import ConfigurationError
from aspen.handlers.static import wsgi as static_handler
from aspen.utils import translate


# Logging config
# ==============

if aspen.mode.DEVDEB:
    level = logging.INFO
else:
    level = logging.WARNING
logging.basicConfig(level=level) # Ack! This should be in Aspen. :^(
log = logging.getLogger('gheat')


# Configuration
# =============
# Set some things that backends will need.

conf = aspen.conf.gheat

ALWAYS_BUILD = ('true', 'yes', '1')
ALWAYS_BUILD = conf.get('_always_build', '').lower() in ALWAYS_BUILD

BUILD_EMPTIES = ('true', 'yes', '1')
BUILD_EMPTIES = conf.get('_build_empties', 'true').lower() in BUILD_EMPTIES

DIRMODE = conf.get('dirmode', '0755')
try:
    DIRMODE = int(eval(DIRMODE))
except (NameError, SyntaxError, ValueError):
    raise ConfigurationError("dirmode (%s) must be an integer." % dirmode)

SIZE = 256 # size of (square) tile; NB: changing this will break gmerc calls!
MAX_ZOOM = 31 # this depends on Google API; 0 is furthest out as of recent ver.


# Database
# ========

def get_cursor():
    """Return a database cursor.
    """
    db = sqlite3.connect(os.path.join(aspen.paths.__, 'var', 'points.db'))
    db.row_factory = sqlite3.Row
    return db.cursor()


# Try to find an image library.
# =============================

BACKEND = None 
BACKEND_PIL = False 
BACKEND_PYGAME = False

_want = conf.get('backend', '').lower()
if _want not in ('pil', 'pygame', ''):
    raise ConfigurationError( "The %s backend is not supported, only PIL and "
                            + "Pygame (assuming those libraries are installed)."
                             )

if _want:
    if _want == 'pygame':
        from gheat import pygame_ as backend
    elif _want == 'pil':
        from gheat import pil_ as backend
    BACKEND = _want
else:
    try:
        from gheat import pygame_ as backend
        BACKEND = 'pygame'
    except ImportError:
        try:
            from gheat import pil_ as backend
            BACKEND = 'pil'
        except ImportError:
            pass
    
    if BACKEND is None:
        raise ImportError("Neither Pygame nor PIL could be imported.")

BACKEND_PYGAME = BACKEND == 'pygame'
BACKEND_PIL = BACKEND == 'pil'

log.info("Using the %s library" % BACKEND)


# Set up color schemes and dots.
# ==============================

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
    return dict([(zoom, backend.Dot(zoom)) for zoom in range(MAX_ZOOM)])
dots = load_dots(backend) # factored for easier use from scripts


# Main WSGI callable 
# ==================

ROOT = aspen.paths.root

def wsgi(environ, start_response):
    path = environ['PATH_INFO']
    fspath = translate(ROOT, path)

    if path.endswith('.png') and 'empties' not in path: 
                        # let people hit empties directly if they want; why not?


        # Parse and validate input.
        # =========================
        # URL paths are of the form:
        #
        #   /<color_scheme>/<zoom>/<x>,<y>.png
        #
        # E.g.:
        #
        #   /classic/3/0,1.png

        raw = path[:-4] # strip extension
        try:
            assert raw.count('/') == 3, "%d /'s" % raw.count('/')
            foo, color_scheme, zoom, xy = raw.split('/')
            assert color_scheme in color_schemes, ( "bad color_scheme: "
                                                  + color_scheme
                                                   )
            assert xy.count(',') == 1, "%d /'s" % xy.count(',')
            x, y = xy.split(',')
            assert zoom.isdigit() and x.isdigit() and y.isdigit(), "not digits"
            zoom = int(zoom)
            x = int(x)
            y = int(y)
            assert 0 <= zoom <= 30, "bad zoom: %d" % zoom
        except AssertionError, err:
            log.warn(err.args[0])
            start_response('400 Bad Request', [('CONTENT-TYPE','text/plain')])
            return ['Bad request.']


        # Build and save the file.
        # ========================
        # The tile that is built here will be served by the static handler.

        color_scheme = color_schemes[color_scheme]
        tile = backend.Tile(color_scheme, dots, zoom, x, y, fspath)
        if tile.is_empty():
            log.info('serving empty tile %s' % path)
            fspath = color_scheme.get_empty_fspath(zoom)
        elif tile.is_stale() or ALWAYS_BUILD:
            log.info('rebuilding %s' % path)
            tile.rebuild()
            tile.save()
        else:
            log.info('serving cached tile %s' % path)


    environ['PATH_TRANSLATED'] = fspath
    return static_handler(environ, start_response)


