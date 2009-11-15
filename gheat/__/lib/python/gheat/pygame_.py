import os

import numpy
import pygame
from gheat import SIZE, base


WHITE = (255, 255, 255)


# Needed for colors
# =================
# 
#   http://www.pygame.org/wiki/HeadlessNoWindowsNeeded 
# 
# Beyond what is said there, also set the color depth to 32 bits.

os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.display.init()
pygame.display.set_mode((1,1), 0, 32)


class ColorScheme(base.ColorScheme):

    def hook_set(self, fspath):
        colors = pygame.image.load(fspath)
        self.colors = colors = colors.convert_alpha()
        self.color_map = pygame.surfarray.pixels3d(colors)[0] 
        self.alpha_map = pygame.surfarray.pixels_alpha(colors)[0]

    def hook_build_empty(self, opacity, fspath):
        tile = pygame.Surface((SIZE,SIZE), pygame.SRCALPHA, 32)
        tile.fill(self.color_map[255])
        tile.convert_alpha()

        (conf, pixel) = opacity, self.alpha_map[255]
        opacity = int(( (conf/255.0)    # from configuration
                      * (pixel/255.0)   # from per-pixel alpha
                       ) * 255)

        pygame.surfarray.pixels_alpha(tile)[:,:] = opacity 
        pygame.image.save(tile, fspath)


class Dot(base.Dot):
    def hook_get(self, fspath):
        img = pygame.image.load(fspath)
        half_size = img.get_size()[0] / 2
        return img, half_size


class Tile(base.Tile):

    def hook_rebuild(self, points):
        """Given a list of points, save a tile.
    
        This uses the Pygame backend.
   
        Good surfarray tutorial (old but still applies):

            http://www.pygame.org/docs/tut/surfarray/SurfarrayIntro.html

        Split out to give us better profiling granularity.

        """
        tile = self._start()
        tile = self._add_points(tile, points)
        tile = self._trim(tile)
        tile = self._colorize(tile)
        return tile


    def _start(self):
        tile = pygame.Surface(self.expanded_size, 0, 32)
        tile.fill(WHITE)
        return tile
        #@ why do we get green after this step?
 
       
    def _add_points(self, tile, points):
        for dest in points:
            tile.blit(self.dot, dest, None, pygame.BLEND_MULT)
        return tile


    def _trim(self, tile):
        tile = tile.subsurface(self.pad, self.pad, SIZE, SIZE).copy()
        #@ pygame.transform.chop says this or blit; this is plenty fast 
        return tile


    def _colorize(self, tile):

        # Invert/colorize
        # ===============
        # The way this works is that we loop through all pixels in the image,
        # and set their color and their transparency based on an index image.
        # The index image can be as wide as we want; we only look at the first
        # column of pixels. This first column is considered a mapping of 256
        # gray-scale intensity values to color/alpha.

        # Optimized: I had the alpha computation in a separate function because 
        # I'm also using it above in ColorScheme (cause I couldn't get set_alpha
        # working). The inner loop runs 65536 times, and just moving the 
        # computation out of a function and inline into the loop sped things up 
        # about 50%. It sped it up another 50% to cache the values, since each
        # of the 65536 variables only ever takes one of 256 values. Not super
        # fast still, but more reasonable (1.5 seconds instead of 12).
        #
        # I would expect that precomputing the dictionary at start-up time 
        # should give us another boost, but it slowed us down again. Maybe 
        # since with precomputation we have to calculate more than we use, the 
        # size of the dictionary made a difference? Worth exploring ...

        _computed_opacities = dict()

        tile = tile.convert_alpha(self.color_scheme.colors)
        tile.lock()
        pix = pygame.surfarray.pixels3d(tile)
        alp = pygame.surfarray.pixels_alpha(tile)
        for x in range(SIZE):
            for y in range(SIZE):
                key = pix[x,y,0]

                conf, pixel = self.opacity, self.color_scheme.alpha_map[key]
                if (conf, pixel) not in _computed_opacities:
                    opacity = int(( (conf/255.0)    # from configuration
                                  * (pixel/255.0)   # from per-pixel alpha
                                   ) * 255)
                    _computed_opacities[(conf, pixel)] = opacity

                pix[x,y] = self.color_scheme.color_map[key]
                alp[x,y] = _computed_opacities[(conf, pixel)]

        tile.unlock()
   
        return tile


    def save(self):
        pygame.image.save(self.img, self.fspath)


