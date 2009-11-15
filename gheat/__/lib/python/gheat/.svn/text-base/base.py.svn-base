import datetime
import os
import stat

import aspen
try:
    from aspen import restarter     # v0.8
except ImportError:
    from aspen.ipc import restarter # trunk (v0.9?)
import gheat
import gheat.opacity
import gmerc
from gheat import BUILD_EMPTIES, DIRMODE, SIZE, log


class ColorScheme(object):
    """Base class for color scheme representations.
    """

    def __init__(self, name, fspath):
        """Takes the name and filesystem path of the defining PNG.
        """
        if aspen.mode.DEVDEB:
            restarter.track(fspath)
        self.hook_set(fspath)
        self.empties_dir = os.path.join(aspen.paths.root, name, 'empties')
        self.build_empties()


    def build_empties(self):
        """Build empty tiles for this color scheme.
        """
        empties_dir = self.empties_dir

        if not BUILD_EMPTIES:
            log.info("not building empty tiles for %s" % name)
        else:    
            if not os.path.isdir(empties_dir):
                os.makedirs(empties_dir, DIRMODE)
            if not os.access(empties_dir, os.R_OK|os.W_OK|os.X_OK):
                raise ConfigurationError( "Permissions too restrictive on "
                                        + "empties directory "
                                        + "(%s)." % empties_dir
                                         )
            for fname in os.listdir(empties_dir):
                if fname.endswith('.png'):
                    os.remove(os.path.join(empties_dir, fname))
            for zoom, opacity in gheat.opacity.zoom_to_opacity.items():
                fspath = os.path.join(empties_dir, str(zoom)+'.png')
                self.hook_build_empty(opacity, fspath)
            
            log.info("building empty tiles in %s" % empties_dir)


    def get_empty_fspath(self, zoom):
        fspath = os.path.join(self.empties_dir, str(zoom)+'.png')
        if not os.path.isfile(fspath):
            self.build_empties() # so we can rebuild empties on the fly
        return fspath


    def hook_set(self):
        """Set things that your backend will want later.
        """
        raise NotImplementedError


    def hook_build_empty(self, opacity, fspath):
        """Given an opacity and a path, save an empty tile.
        """
        raise NotImplementedError


class Dot(object):
    """Base class for dot representations.

    Unlike color scheme, the same basic external API works for both backends. 
    How we compute that API is different, though.

    """

    def __init__(self, zoom):
        """Takes a zoom level.
        """
        name = 'dot%d.png' % zoom
        fspath = os.path.join(aspen.paths.__, 'etc', 'dots', name)
        self.img, self.half_size = self.hook_get(fspath)
        
    def hook_get(self, fspath):
        """Given a filesystem path, return two items.
        """
        raise NotImplementedError


class Tile(object):
    """Base class for tile representations.
    """

    img = None

    def __init__(self, color_scheme, dots, zoom, x, y, fspath):
        """x and y are tile coords per Google Maps.
        """

        # Calculate some things.
        # ======================

        dot = dots[zoom]


        # Translate tile to pixel coords.
        # -------------------------------

        x1 = x * SIZE
        x2 = x1 + 255
        y1 = y * SIZE
        y2 = y1 + 255
    
    
        # Expand bounds by one-half dot width.
        # ------------------------------------
    
        x1 = x1 - dot.half_size
        x2 = x2 + dot.half_size
        y1 = y1 - dot.half_size
        y2 = y2 + dot.half_size
        expanded_size = (x2-x1, y2-y1)
    
    
        # Translate new pixel bounds to lat/lng.
        # --------------------------------------
    
        n, w = gmerc.px2ll(x1, y1, zoom)
        s, e = gmerc.px2ll(x2, y2, zoom)


        # Save
        # ====

        self.dot = dot.img
        self.pad = dot.half_size

        self.x = x
        self.y = y

        self.x1 = x1
        self.y1 = y1

        self.x2 = x2
        self.y2 = y2

        self.expanded_size = expanded_size
        self.llbound = (n,s,e,w)
        self.zoom = zoom
        self.fspath = fspath
        self.opacity = gheat.opacity.zoom_to_opacity[zoom]
        self.color_scheme = color_scheme
  

    def is_empty(self):
        """With attributes set on self, return a boolean.

        Calc lat/lng bounds of this tile (include half-dot-width of padding)
        SELECT count(uid) FROM points

        """
        points = gheat.get_cursor() 
        points = points.execute("""
    
            SELECT count(uid)
              FROM points
             WHERE lat <= ?
               AND lat >= ?
               AND lng <= ?
               AND lng >= ?
    
            """, self.llbound)
    
        numpoints = points.fetchone()[0] # this is guaranteed to exist, right?
        return numpoints == 0


    def is_stale(self):
        """With attributes set on self, return a boolean.

        Calc lat/lng bounds of this tile (include half-dot-width of padding)
        SELECT count(uid) FROM points WHERE modtime < modtime_tile

        """
        if not os.path.isfile(self.fspath):
            return True
   
        timestamp = os.stat(self.fspath)[stat.ST_MTIME]
        modtime = datetime.datetime.fromtimestamp(timestamp)
    
        points = gheat.get_cursor() 
        points = points.execute("""
    
            SELECT count(uid)
              FROM points
             WHERE lat <= ?
               AND lat >= ?
               AND lng <= ?
               AND lng >= ?
    
             AND modtime > ?
    
            """, self.llbound + (modtime,))
    
        numpoints = points.fetchone()[0] # this is guaranteed to exist, right?
        return numpoints > 0


    def rebuild(self):
        """Rebuild the image at self.img. Real work delegated to subclasses.
        """

        # Calculate points.
        # =================
        # Build a closure that gives us the x,y pixel coords of the points
        # to be included on this tile, relative to the top-left of the tile.

        _points = gheat.get_cursor()
        _points.execute("""

            SELECT *
              FROM points
             WHERE lat <= ?
               AND lat >= ?
               AND lng <= ?
               AND lng >= ?

        """, self.llbound)
   
        def points():
            """Yield x,y pixel coords within this tile, top-left of dot.
            """
            for point in _points:
                x, y = gmerc.ll2px(point['lat'], point['lng'], self.zoom)
                x = x - self.x1 # account for tile offset relative to 
                y = y - self.y1 #  overall map
                yield x-self.pad,y-self.pad


        # Main logic
        # ==========
        # Hand off to the subclass to actually build the image, then come back 
        # here to maybe create a directory before handing back to the backend
        # to actually write to disk.

        self.img = self.hook_rebuild(points())

        dirpath = os.path.dirname(self.fspath)
        if dirpath and not os.path.isdir(dirpath):
            os.makedirs(dirpath, DIRMODE)


    def hook_rebuild(self, points, opacity):
        """Rebuild and save the file using the current library.

        The algorithm runs something like this:

            o start a tile canvas/image that is a dots-worth oversized
            o loop through points and multiply dots on the tile
            o trim back down to straight tile size
            o invert/colorize the image
            o make it transparent

        Return the img object; it will be sent back to hook_save after a
        directory is made if needed.

        Trim after looping because we multiply is the only step that needs the
        extra information.

        The coloring and inverting can happen in the same pixel manipulation 
        because you can invert colors.png. That is a 1px by 256px PNG that maps
        grayscale values to color values. You can customize that file to change
        the coloration.

        """
        raise NotImplementedError


    def save(self):
        """Write the image at self.img to disk.
        """
        raise NotImplementedError


