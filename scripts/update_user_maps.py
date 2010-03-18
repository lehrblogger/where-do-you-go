from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api import urlfetch
from google.appengine.ext import db
from google.appengine.runtime import DeadlineExceededError
from google.appengine.runtime.apiproxy_errors import CancelledError
import os
from os import environ
import urllib
import constants
import logging
from datetime import datetime
from gheatae import tile
from models import MapImage

def update_map_image(user, google_data, width, height, northlat, westlng):
  result = urlfetch.fetch(url="http://maps.google.com/maps/api/staticmap?" + urllib.urlencode(google_data),
                          method=urlfetch.GET)
  input_tuples = []
  input_tuples.append((result.content, 0, 0, 1.0, images.TOP_LEFT))
  for offset_x_px in range (0, width, 256):
    for offset_y_px in range (0, height, 256):
      new_tile = tile.CustomTile(user, int(google_data['zoom']), northlat, westlng, offset_x_px, offset_y_px)
      input_tuples.append((new_tile.image_out(), offset_x_px, offset_y_px, 1.0, images.TOP_LEFT)) # http://code.google.com/appengine/docs/python/images/functions.html
  img = images.composite(inputs=input_tuples, width=width, height=height, color=0, output_encoding=images.PNG)
  return img

def create_map_file(user, path=''):
  try:
    assert raw.count('/') == 5, "%d /'s" % raw.count('/')
    foo, bar, widthxheight, zoom, centerpoint, northwest, = raw.split('/')
    assert widthxheight.count('x') == 1, "%d x's" % centerpoint.count('x')
    width, height = widthxheight.split('x')
    assert zoom.isdigit(), "not digits"
    assert centerpoint.count(',') == 1, "%d ,'s" % centerpoint.count(',')
    centerlat, centerlng = centerpoint.split(',')
    assert northwest.count(',') == 1, "%d ,'s" % northwest.count(',')
    northlat, westlng = northwest.split(',')
  except AssertionError, err:
    logging.error(err.args[0])
    return
  google_data = {
    'key': constants.get_google_maps_apikey(),
    'zoom': zoom,
    'center': centerpoint,
    'size': widthxheight,
    'sensor':'false',
    'format':'png',
  }
  mapimage = MapImage.all().filter('user =', user).get()
  if not mapimage:
    mapimage            = MapImage()
    mapimage.user       = user
    mapimage.centerlat  = float(centerlat)
    mapimage.centerlng  = float(centerlng)
    mapimage.northlat   = float(northlat)
    mapimage.westlng    = float(westlng)
    mapimage.zoom       = int(zoom)
    mapimage.height     = int(height)
    mapimage.width      = int(width)
  img = update_map_image(user, google_data, int(width), int(height), float(northlat), float(westlng))
  mapimage.img          = db.Blob(img)
  mapimage.last_updated = datetime.now()
  mapimage.put()

if __name__ == '__main__':
  raw = environ['PATH_INFO']
  if raw.count('/') == 2:
    foo, bar, rest, = raw.split('/')
    try:
      assert rest == 'one', "rest is: %s " % rest
      mapimage = MapImage.all().order('last_updated').get()
      try: 
        google_data = {
          'key': constants.get_google_maps_apikey(),
          'zoom': mapimage.zoom,
          'center': str(mapimage.centerlat) + "," + str(mapimage.centerlng),
          'size': str(mapimage.width) + "x" + str(mapimage.height),
          'sensor':'false',
          'format':'png',
        }
        img = update_map_image(mapimage.user, google_data, mapimage.width, mapimage.height, mapimage.northlat, mapimage.westlng)
        mapimage.img = db.Blob(img)
        mapimage.last_updated = datetime.now()
        mapimage.put()
        logging.info("Updated user map for %s" % mapimage.user)
      except DeadlineExceededError, err:    
        logging.error("Ran out of time before updating a map! %s" % err)
        mapimage.last_updated = datetime.now() # put it at the end of the queue anyway, in case we always fail on this map for some reason
        mapimage.put()
    except AssertionError, err:
      logging.error(err.args[0])
  else:
    user = users.get_current_user()
    if user:
      create_map_file(user, raw)
