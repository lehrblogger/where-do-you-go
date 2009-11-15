import os

from PIL import Image, ImageChops
from gheat import SIZE, base
from gheat.opacity import OPAQUE


class ColorScheme(base.ColorScheme):

    def hook_set(self, fspath):
        self.colors = Image.open(fspath).load()

    def hook_build_empty(self, opacity, fspath):
        color = self.colors[0, 255]
        if len(color) == 4: # color map has per-pixel alpha
            (conf, pixel) = opacity, color[3] 
            opacity = int(( (conf/255.0)    # from configuration
                          * (pixel/255.0)   # from per-pixel alpha
                           ) * 255)
        color = color[:3] + (opacity,)
        tile = Image.new('RGBA', (SIZE, SIZE), color)
        tile.save(fspath, 'PNG')


class Dot(base.Dot):
    def hook_get(self, fspath):
        img = Image.open(fspath)
        half_size = img.size[0] / 2
        return img, half_size 


class Tile(base.Tile):
    """Represent a tile; use the PIL backend.
    """

    def hook_rebuild(self, points):
        """Given a list of points and an opacity, save a tile.
    
        This uses the PIL backend.
    
        """
        tile = self._start()
        tile = self._add_points(tile, points)
        tile = self._trim(tile)
        foo  = self._colorize(tile) # returns None
        return tile


    def _start(self):
        return Image.new('RGBA', self.expanded_size, 'white')


    def _add_points(self, tile, points):
        for x,y in points:
            dot_placed = Image.new('RGBA', self.expanded_size, 'white')
            dot_placed.paste(self.dot, (x, y))
            tile = ImageChops.multiply(tile, dot_placed)
        return tile
  

    def _trim(self, tile):
        tile = tile.crop((self.pad, self.pad, SIZE+self.pad, SIZE+self.pad))
        tile = ImageChops.duplicate(tile) # converts ImageCrop => Image
        return tile


    def _colorize(self, tile):
        _computed_opacities = dict()
        pix = tile.load() # Image => PixelAccess
        for x in range(SIZE):
            for y in range(SIZE):

                # Get color for this intensity
                # ============================
                # is a value 
                
                val = self.color_scheme.colors[0, pix[x,y][0]]
                try:
                    pix_alpha = val[3] # the color image has transparency
                except IndexError:
                    pix_alpha = OPAQUE # it doesn't
                

                # Blend the opacities
                # ===================

                conf, pixel = self.opacity, pix_alpha
                if (conf, pixel) not in _computed_opacities:
                    opacity = int(( (conf/255.0)    # from configuration
                                  * (pixel/255.0)   # from per-pixel alpha
                                   ) * 255)
                    _computed_opacities[(conf, pixel)] = opacity
                
                pix[x,y] = val[:3] + (_computed_opacities[(conf, pixel)],)

    
    def save(self):
        self.img.save(self.fspath, 'PNG')


