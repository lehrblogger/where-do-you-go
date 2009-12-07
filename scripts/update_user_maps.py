import logging
from google.appengine.api import users
from google.appengine.ext import db

import os
from os import environ
import globalvars
from google.appengine.api import images

from gheatae import tile
from models import MapImage

from google.appengine.api import urlfetch
import urllib


def update_map_image(user, google_data, width, height, northlat, westlong):
  logging.warning("Here inside update_map_image")
  result = urlfetch.fetch(url="http://maps.google.com/maps/api/staticmap?" + urllib.urlencode(google_data),
                          method=urlfetch.GET)
  input_tuples = []
  input_tuples.append((result.content, 0, 0, 1.0, images.TOP_LEFT))

  for offset_x_px in range (0, width, 256):
    for offset_y_px in range (0, height, 256):
      new_tile = tile.CustomTile(user, int(google_data['zoom']), northlat, westlong, offset_x_px, offset_y_px)
      input_tuples.append((new_tile.image_out(), offset_x_px, offset_y_px, 1.0, images.TOP_LEFT))
      # http://code.google.com/appengine/docs/python/images/functions.html

  logging.warning("  almost done")
  img =  images.composite(inputs=input_tuples, width=height, height=height, color=0, output_encoding=images.PNG)
  logging.warning("w00t done")
  return img

def create_map_file(user, path=''):
  try:
    assert raw.count('/') == 5, "%d /'s" % raw.count('/')
    foo, bar, widthxheight, zoom, centerpoint, northwest, = raw.split('/')
    assert widthxheight.count('x') == 1, "%d x's" % centerpoint.count('x')
    width, height = widthxheight.split('x')
    assert zoom.isdigit(), "not digits"

    assert centerpoint.count(',') == 1, "%d ,'s" % centerpoint.count(',')
    centerlat, centerlong = centerpoint.split(',')
    assert northwest.count(',') == 1, "%d ,'s" % northwest.count(',')
    northlat, westlong = northwest.split(',')
  except AssertionError, err:
    logging.error(err.args[0])
    return

  google_data = {
    'key': globalvars.google_maps_apikey,
    'zoom': zoom,
    'center': centerpoint,
    'size': widthxheight,
    'sensor':'false',
    'format':'png',
  }

  mapimages = MapImage.all().filter('user =', user).fetch(1000)
  db.delete(mapimages)

  img = update_map_image(user, google_data, int(width), int(height), float(northlat), float(westlong))

  mapimage            = MapImage()
  mapimage.user       = user
  mapimage.userid     = user.user_id()
  mapimage.cityid     = 42 # Hard coded to NYC for now
  mapimage.centerlat  = float(centerlat)
  mapimage.centerlong = float(centerlong)
  mapimage.northlat   = float(northlat)
  mapimage.westlong   = float(westlong)
  mapimage.zoom       = int(zoom)
  mapimage.height     = int(height)
  mapimage.width      = int(width)
  mapimage.img        = db.Blob(img)
  mapimage.put()


if __name__ == '__main__':
  raw = environ['PATH_INFO']
  if raw.count('/') == 2:
    foo, bar, rest, = raw.split('/')
    try:
      assert rest == 'all', "rest is: %s " % rest
      mapimages = MapImage.all().fetch(1000)
      for mapimage in mapimages:
        google_data = {
          'key': globalvars.google_maps_apikey,
          'zoom': mapimage.zoom,
          'center': str(mapimage.centerlat) + "," + str(mapimage.centerlong),
          'size': str(mapimage.width) + "x" + str(mapimage.height),
          'sensor':'false',
          'format':'png',
        }
        img = update_map_image(mapimage.user, google_data, mapimage.width, mapimage.height, mapimage.northlat, mapimage.westlong)
        mapimage.img = db.Blob(img)
        mapimage.put()
        logging.warning("yay it got put!")
    except AssertionError, err:
      logging.error(err.args[0])
  else:
    user = users.get_current_user()
    if user:
      create_map_file(user, raw)
