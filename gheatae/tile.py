import globalvars
from gheatae import color_scheme, provider#, dot
#from gheatae.dot import dot
from pngcanvas import PNGCanvas
from random import random, Random
import logging
import gmerc
import math

from google.appengine.api import users
log = logging.getLogger('space_level')

rdm = Random()

LEVEL_MAX = 350
ZOOM_MAX = 20 # NOTE that this must also be in the static wdyg.js file
DOT_MULT = 3

cache_levels = []
for i in range(LEVEL_MAX - 1, -1, -1):
  cache_levels.append(int(((-(pow(float(i) - LEVEL_MAX, 2))/LEVEL_MAX) + LEVEL_MAX) / LEVEL_MAX * 255))

class BasicTile(object):

  def __init__(self, user, lat_north, lng_west, range_lat, range_lng):
    self.color_scheme = color_scheme.pgaitch

    if not globalvars.provider:
      globalvars.provider = provider.DBProvider()

    self.tile_img = self.plot_image(globalvars.provider.get_user_data(user, #self.layer,
                            lat_north, lng_west,range_lat, range_lng))

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

  def scale_value(self, value):
    #ret_float = math.log(max((value + 50) / 50, 1), 1.01) + 30
    #ret_float = math.log(max((value + 30) / 40, 1), 1.01) + 30
    #ret_float = math.log(max((value + 40) / 20, 1), 1.01)
    ret_float = math.log(max(value, 1), 1.1) * 4
    return int(ret_float)

  max = 0
  def convert_image(self, space_level):
    tile = PNGCanvas(len(space_level[0]), len(space_level), bgcolor=[0xff,0xff,0xff,0])
    color_scheme = []
    for i in range(LEVEL_MAX):
      color_scheme.append(self.color_scheme.canvas[cache_levels[i]][0])
    for y in xrange(len(space_level[0])):
      for x in xrange(len(space_level[0])):
        if self.scale_value(space_level[y][x]) > self.max:
          self.max = self.scale_value(space_level[y][x])
          logging.warning(self.max)
        tile.canvas[y][x] = color_scheme[min(len(color_scheme) - 1, self.scale_value(space_level[y][x]))]

    return tile

  def calc_point(self, rad, pt_rad, weight):
    max_alpha = 100
    fraction = (rad - pt_rad) / rad
    #return max_alpha * math.pow(fraction, math.pow(weight, fraction)) * weight
    return max_alpha * math.pow(fraction, math.pow(weight, 0.25)) * weight

  def get_dot(self, point):
    #cur_dot = dot[self.zoom]
    cur_dot = []
    rad = int(self.zoom * DOT_MULT)
    for i in range(int(rad * 2)):
      cur_dot.append([0.] * int(rad * 2))
    for y in range(0, int(rad * 2)):
      for x in range(0, int(rad * 2)):
        y_adj = math.pow((y - rad), 2) # * len(point.checkin_list)
        x_adj = math.pow((x - rad), 2) # * len(point.checkin_list)
        pt_rad = math.sqrt(y_adj + x_adj)
        temp_rad = rad  #* len(point.checkin_list)
        if pt_rad > temp_rad:
          cur_dot[y][x] = 0.
          continue
        cur_dot[y][x] = self.calc_point(rad, pt_rad, len(point.checkin_list))
    y_off = int(math.ceil((-1 * self.northwest_ll[0] + point.location.lat) / self.latlong_diff[0] * 256. - len(cur_dot) / 2))
    x_off = int(math.ceil((-1 * self.northwest_ll[1] + point.location.lon) / self.latlong_diff[1] * 256. - len(cur_dot[0]) / 2))
    return cur_dot, x_off, y_off

  def __create_empty_space(self):
    space = []
    for i in range(256):
      space.append( [0.] * 256 )
    return space

  def image_out(self):
    if self.tile_img:
      self.tile_dump = self.tile_img.dump()

    if self.tile_dump:
      return self.tile_dump
    else:
      raise Exception("Failure in generation of image.")

class CustomTile(BasicTile):
  def __init__(self, user, zoom, lat_north, lng_west, offset_x_px, offset_y_px):
    self.zoom = zoom
    self.decay = 0.5
    #dot_radius = int(math.ceil(len(dot[self.zoom]) / 2))
    dot_radius = int(math.ceil((self.zoom + 1) * DOT_MULT)) #TODO double check that this is + 1 - because range started from 1 in old dot array?!

    # convert to pixel first so we can factor in the dot radius and get the tile bounds
    northwest_px = gmerc.ll2px(lat_north, lng_west, zoom)

    self.northwest_ll_buffered = gmerc.px2ll(northwest_px[0] + offset_x_px       - dot_radius, northwest_px[1] + offset_y_px       - dot_radius, zoom)
    self.northwest_ll          = gmerc.px2ll(northwest_px[0] + offset_x_px                   , northwest_px[1] + offset_y_px                   , zoom)

    self.southeast_ll_buffered = gmerc.px2ll(northwest_px[0] + offset_x_px + 256 + dot_radius, northwest_px[1] + offset_y_px + 256 + dot_radius, zoom)
    self.southeast_ll          = gmerc.px2ll(northwest_px[0] + offset_x_px + 256             , northwest_px[1] + offset_y_px + 256             , zoom) # THIS IS IMPORTANT TO PROPERLY CALC latlong_diff

    self.latlong_diff_buffered = [ self.southeast_ll_buffered[0] - self.northwest_ll_buffered[0], self.southeast_ll_buffered[1] - self.northwest_ll_buffered[1]]
    self.latlong_diff          = [ self.southeast_ll[0]          - self.northwest_ll[0]         , self.southeast_ll[1]          - self.northwest_ll[1]]

    BasicTile.__init__(self, user, self.northwest_ll_buffered[0], self.northwest_ll_buffered[1], self.latlong_diff_buffered[0], self.latlong_diff_buffered[1])


class GoogleTile(BasicTile):
  def __init__(self, user, layer, zoom, x_tile, y_tile):
    self.layer = layer
    self.zoom = zoom
    self.decay = 0.5
    #dot_radius = int(math.ceil(len(dot[self.zoom]) / 2))
    dot_radius = int(math.ceil((self.zoom + 1) * DOT_MULT))

    self.northwest_ll_buffered = gmerc.px2ll((x_tile    ) * 256 - dot_radius, (y_tile    ) * 256 - dot_radius, zoom)
    self.northwest_ll          = gmerc.px2ll((x_tile    ) * 256             , (y_tile    ) * 256             , zoom)

    self.southeast_ll_buffered = gmerc.px2ll((x_tile + 1) * 256 + dot_radius, (y_tile + 1) * 256 + dot_radius, zoom) #TODO fix this in case we're at the edge of the map!
    self.southeast_ll          = gmerc.px2ll((x_tile + 1) * 256             , (y_tile + 1) * 256             , zoom)

    # calculate the real values for these without the offsets, otherwise it messes up the get_dot calculations
    self.latlong_diff_buffered = [ self.southeast_ll_buffered[0] - self.northwest_ll_buffered[0], self.southeast_ll_buffered[1] - self.northwest_ll_buffered[1]]
    self.latlong_diff          = [ self.southeast_ll[0]          - self.northwest_ll[0]         , self.southeast_ll[1]          - self.northwest_ll[1]]

    BasicTile.__init__(self, user, self.northwest_ll_buffered[0], self.northwest_ll_buffered[1], self.latlong_diff_buffered[0], self.latlong_diff_buffered[1])



























