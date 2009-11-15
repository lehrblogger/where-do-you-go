from gheatae import color_scheme
from gheatae.dot import dot
from pngcanvas import PNGCanvas
from random import random, Random
import logging
import gmerc
import math

log = logging.getLogger('space_level')

# This is the provider of data and interfaced to data interface
provider = None
cache = None

rdm = Random()

LEVEL_MAX = 300

cache_levels = []

for i in range(LEVEL_MAX):
  cache_levels.append(int(((-(pow(float(i) - LEVEL_MAX, 2))/LEVEL_MAX) + LEVEL_MAX) / LEVEL_MAX * 255))

class Tile(object):
  
  def __init__(self, layer, zoom, x, y):
    self.layer = layer
    self.zoom = zoom
    self.x = x
    self.y = y
    self.color_scheme = color_scheme.cyan_red
    self.decay = 0.5

    # attempt to get a cached object
    self.tile_dump = self.__get_cached_image()
    if not self.tile_dump:
      # Get the bounds of this tile
      self.width, self.height = gmerc.ll2px(-90, 180, self.zoom)
      self.numcols = int(math.ceil(self.width / 256.0))
      self.numrows = int(math.ceil(self.height / 256.0))
      self.zoom_step = [ 180. / self.numrows, 360. / self.numcols ]
      self.georange = ( min(90, max(-90, 180. / self.numrows * y - 90)), min(180, max(-180, 360. / self.numcols * x - 180 )))

      # Get the points and start plotting data
      self.tile_img = self.plot_image(
          provider.get_data(self.zoom, self.layer, 
                            self.georange[0], self.georange[1], 
                            self.zoom_step[0], self.zoom_step[1]))
  
  def plot_image(self, points):
    space_level = self.__create_empty_space()
    for point in points:
      self.__merge_point_in_space(space_level, point) 
    return self.convert_image(space_level)
  
  def __merge_point_in_space(self, space_level, point):
    # By default, multiply per color point
    dot_levels, x_off, y_off = self.get_dot(point)
    
    for y in range(y_off, y_off + len(dot_levels)):
      if y < 0 or y >= len(space_level):
        continue
      for x in range(x_off, x_off + len(dot_levels[0])):
        if x < 0 or x >= len(space_level[0]):
          continue
        dot_level = dot_levels[y_off - y][x_off - x]
        if dot_level <= 0.:
          continue
        space_level[y][x] += dot_level

  def convert_image(self, space_level):
    tile = PNGCanvas(len(space_level[0]), len(space_level), bgcolor=[0xff,0xff,0xff,0])
    color_scheme = []
    for i in range(LEVEL_MAX):
      color_scheme.append(self.color_scheme.canvas[cache_levels[i]][0])
    for y in xrange(len(space_level[0])):
      for x in xrange(len(space_level[0])):
        tile.canvas[y][x] = color_scheme[int(space_level[y][x])]
    return tile

  def get_dot(self, point):
    #return dot[20], rdm.randint(-20, 260), rdm.randint(-20, 260)
    cur_dot = dot[self.zoom]
    y_off = int(math.ceil((-1 * self.georange[0] + point.location.lat) / self.zoom_step[0] * 256. - len(cur_dot) / 2))
    x_off = int(math.ceil((-1 * self.georange[1] + point.location.lon) / self.zoom_step[1] * 256. - len(cur_dot[0]) / 2))
    log.info("lat, lng  dist_lng, dist_lng  Y_off, X_off: (%6.4f, %6.4f) (%6.4f, %6.4f) (%4d, %4d)" % (point.location.lat, point.location.lon,
                                                                                        (-1 * self.georange[0] + point.location.lat) / self.zoom_step[0] * 256, (-1 * self.georange[1] + point.location.lon) / self.zoom_step[1] * 256,
                                                                                        y_off, x_off))
    return cur_dot, x_off, y_off

  def __create_empty_space(self):
    space = []
    for i in range(256):
      space.append( [0.] * 256 )
    return space

  def __get_cached_image(self):
    if cache.is_available(self.layer, self.x, self.y):
      return cache.get_image(self.layer, self.x, self.y)
    return None
  
  def __cache_image(self, tile_dump):
    return cache.store_image(self.layer, self.x, self.y, tile_dump)

  def image_out(self):
    if self.tile_img:
      self.tile_dump = self.tile_img.dump()
      # attempt to cache this
      self.__cache_image(self.tile_dump)

    if self.tile_dump:
      return self.tile_dump
    else:
      raise Exception("Failure in generation of image.")