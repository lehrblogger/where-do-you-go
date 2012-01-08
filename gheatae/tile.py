import constants
from gheatae import color_scheme, provider
from pngcanvas import PNGCanvas
from random import random, Random
import logging
import gmerc
import math
from models import UserInfo
from datetime import datetime

from google.appengine.api import users
log = logging.getLogger('space_level')

rdm = Random()

DOT_MULT = 3
SIZE = 256
MAX_ALPHA = 100

class BasicTile(object):
  def __init__(self, user, lat_north, lng_west, range_lat, range_lng):
    userinfo = UserInfo.all().filter('user =', user).order('-created').get()
    if userinfo:
      self.level_max = userinfo.level_max
      self.color_scheme = color_scheme.color_schemes[userinfo.color_scheme]
    else:
      self.level_max = int(constants.level_const)
      self.color_scheme = color_scheme.color_schemes[constants.default_color]

    self.cache_levels = []
    for i in range(self.level_max - 1, -1, -1):
      self.cache_levels.append(int(((-(pow(float(i) - self.level_max, 2))/self.level_max) + self.level_max) / self.level_max * 255))

    if not constants.provider:
      constants.provider = provider.DBProvider()
    uservenues = constants.provider.get_user_data(user, lat_north, lng_west, range_lat, range_lng)
    if uservenues and len(uservenues):
      self.tile_img = self.plot_image(uservenues)
    else: # don't do any more math if we don't have any venues
      self.tile_img = PNGCanvas(SIZE, SIZE, bgcolor=self.color_scheme.canvas[self.cache_levels[0]][0])

  def plot_image(self, points):
    space_level = self.__create_empty_space()
    rad = int(self.zoom * DOT_MULT)
    lat_diff =  self.latlng_diff[0] * 256.
    lng_diff = self.latlng_diff[1] * 256.
    start = datetime.now()
    for i, point in enumerate(points):
      self.__merge_point_in_space(space_level, point, rad, lat_diff, lng_diff)
      logging.warning('   point %d of %d, start at %s, done at %s' % (i, len(points), start, datetime.now()))
    return self.convert_image(space_level)

  def __merge_point_in_space(self, space_level, point, rad, lat_diff, lng_diff):
    weight = len(point.checkin_guid_list)
    rad_exp = math.pow(weight, 0.25)
    alpha_weight = MAX_ALPHA * weight
    twice_rad = rad * 2
    y_off = int(math.ceil((-1 * self.northwest_ll[0] + point.location.lat) / lat_diff - rad))
    x_off = int(math.ceil((-1 * self.northwest_ll[1] + point.location.lon) / lng_diff - rad))
    for y in range(y_off, y_off + twice_rad):
      if y < 0 or y >= SIZE:
        continue
      y_adj = math.pow((y - rad - y_off), 2)
      for x in range(x_off, x_off + twice_rad):
        if x < 0 or x >= SIZE:
          continue
        x_adj = math.pow((x - rad - x_off), 2)
        pt_rad = math.sqrt(y_adj + x_adj)
        if pt_rad > rad:
          continue
        space_level[y][x] += (math.pow((rad - pt_rad) / rad, rad_exp) * alpha_weight)
        
  def scale_value(self, value):
    #ret_float = math.log(max((value + 50) / 50, 1), 1.01) + 30
    #ret_float = math.log(max((value + 30) / 40, 1), 1.01) + 30
    #ret_float = math.log(max((value + 40) / 20, 1), 1.01)
    ret_float = math.log(max(value, 1), 1.1) * 4
    return int(ret_float)

  def convert_image(self, space_level):
    tile = PNGCanvas(SIZE, SIZE, bgcolor=[0xff,0xff,0xff,0])
    temp_color_scheme = []
    for i in range(self.level_max):
      temp_color_scheme.append(self.color_scheme.canvas[self.cache_levels[i]][0])
    for y in xrange(SIZE):
      for x in xrange(SIZE):
        if len(temp_color_scheme) > 0:
          tile.canvas[y][x] = [int(e) for e in temp_color_scheme[max(0, min(len(temp_color_scheme) - 1, self.scale_value(space_level[y][x])))]]
        else:
          tile.canvas[y][x] = [0,0,0,0]
    return tile

  def __create_empty_space(self):
    space = []
    for i in range(SIZE):
      space.append( [0.] * SIZE )
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
    logging.info("drawing new custom tile")
    self.zoom = zoom
    self.decay = 0.5
    #dot_radius = int(math.ceil(len(dot[self.zoom]) / 2))
    dot_radius = int(math.ceil((self.zoom + 1) * DOT_MULT)) #TODO double check that this is + 1 - because range started from 1 in old dot array?!

    # convert to pixel first so we can factor in the dot radius and get the tile bounds
    northwest_px = gmerc.ll2px(lat_north, lng_west, zoom)

    self.northwest_ll_buffered = gmerc.px2ll(northwest_px[0] + offset_x_px       - dot_radius, northwest_px[1] + offset_y_px       - dot_radius, zoom)
    self.northwest_ll          = gmerc.px2ll(northwest_px[0] + offset_x_px                   , northwest_px[1] + offset_y_px                   , zoom)

    self.southeast_ll_buffered = gmerc.px2ll(northwest_px[0] + offset_x_px + 256 + dot_radius, northwest_px[1] + offset_y_px + 256 + dot_radius, zoom)
    self.southeast_ll          = gmerc.px2ll(northwest_px[0] + offset_x_px + 256             , northwest_px[1] + offset_y_px + 256             , zoom) # THIS IS IMPORTANT TO PROPERLY CALC latlng_diff

    self.latlng_diff_buffered = [ self.southeast_ll_buffered[0] - self.northwest_ll_buffered[0], self.southeast_ll_buffered[1] - self.northwest_ll_buffered[1]]
    self.latlng_diff          = [ self.southeast_ll[0]          - self.northwest_ll[0]         , self.southeast_ll[1]          - self.northwest_ll[1]]

    BasicTile.__init__(self, user, self.northwest_ll_buffered[0], self.northwest_ll_buffered[1], self.latlng_diff_buffered[0], self.latlng_diff_buffered[1])


class GoogleTile(BasicTile):
  def __init__(self, user, zoom, x_tile, y_tile):
    self.zoom = zoom
    self.decay = 0.5
    #dot_radius = int(math.ceil(len(dot[self.zoom]) / 2))
    dot_radius = int(math.ceil((self.zoom + 1) * DOT_MULT))

    self.northwest_ll_buffered = gmerc.px2ll((x_tile    ) * 256 - dot_radius, (y_tile    ) * 256 - dot_radius, zoom)
    self.northwest_ll          = gmerc.px2ll((x_tile    ) * 256             , (y_tile    ) * 256             , zoom)

    self.southeast_ll_buffered = gmerc.px2ll((x_tile + 1) * 256 + dot_radius, (y_tile + 1) * 256 + dot_radius, zoom) #TODO fix this in case we're at the edge of the map!
    self.southeast_ll          = gmerc.px2ll((x_tile + 1) * 256             , (y_tile + 1) * 256             , zoom)

    # calculate the real values for these without the offsets, otherwise it messes up the __merge_point_in_space calculations
    self.latlng_diff_buffered = [ self.southeast_ll_buffered[0] - self.northwest_ll_buffered[0], self.southeast_ll_buffered[1] - self.northwest_ll_buffered[1]]
    self.latlng_diff          = [ self.southeast_ll[0]          - self.northwest_ll[0]         , self.southeast_ll[1]          - self.northwest_ll[1]]

    BasicTile.__init__(self, user, self.northwest_ll_buffered[0], self.northwest_ll_buffered[1], self.latlng_diff_buffered[0], self.latlng_diff_buffered[1])