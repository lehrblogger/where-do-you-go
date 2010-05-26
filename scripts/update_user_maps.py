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
from models import MapImage, UserInfo

def update_map_image(user, zoom, width, height, northlat, westlng):
  input_tuples = []
  for offset_x_px in range (0, width, 256):
    for offset_y_px in range (0, height, 256):
      new_tile = tile.CustomTile(user, int(zoom), northlat, westlng, offset_x_px, offset_y_px)
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
    
  try:
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
      mapimage              = MapImage()
      mapimage.user         = user
      mapimage.update_count = 0
    mapimage.centerlat  = float(centerlat)
    mapimage.centerlng  = float(centerlng)
    mapimage.northlat   = float(northlat)
    mapimage.westlng    = float(westlng)
    mapimage.zoom       = int(zoom)
    mapimage.height     = int(height)
    mapimage.width      = int(width)
    img = update_map_image(user, int(zoom), int(width), int(height), float(northlat), float(westlng))
    mapimage.img          = db.Blob(img)
    mapimage.last_updated = datetime.now()
    mapimage.static_url = "http://maps.google.com/maps/api/staticmap?" + urllib.urlencode(google_data)
    mapimage.put()
  except DeadlineExceededError, err:    
    logging.error("Ran out of time before creating a map! %s" % err)

def update_map_file(): # really there should be a flag in the user object to indicate the map needs updating, but for that to be reliable that needs to put with each new checkin, so these need to have the user as the parent so the transaction works, and that's just a nightmare.
  mapimages = MapImage.all().order('last_updated').fetch(10)
  for mapimage in mapimages:
    if not mapimage.update_count:
      mapimage.update_count = 0
      mapimage.put()
    userinfo = UserInfo.all().filter('user = ', mapimage.user).get()
    if not userinfo:
      #TODO consider deleting these maps?
      mapimage.last_updated = datetime.now()
      mapimage.update_count = -1 # flag for now to indicate that there's no userinfo
      mapimage.put()
      logging.warning("No userinfo found for mapimage with user %s" % mapimage.user)
      continue
    try:
      if userinfo.last_updated > mapimage.last_updated or mapimage.update_count == 0:
        google_data = {
          'key': constants.get_google_maps_apikey(),
          'zoom': mapimage.zoom,
          'center': str(mapimage.centerlat) + "," + str(mapimage.centerlng),
          'size': str(mapimage.width) + "x" + str(mapimage.height),
          'sensor':'false',
          'format':'png',
        }
        img = update_map_image(mapimage.user, mapimage.zoom, mapimage.width, mapimage.height, mapimage.northlat, mapimage.westlng)
        mapimage.img = db.Blob(img)
        mapimage.last_updated = datetime.now()
        mapimage.static_url = "http://maps.google.com/maps/api/staticmap?" + urllib.urlencode(google_data)
        mapimage.update_count += 1
        mapimage.put()
        logging.info("Updated user map for %s" % mapimage.user)
        return # only update one map
      else: # so that we don't get stuck on the same maps forever
        mapimage.last_updated = datetime.now()
        mapimage.put()
        logging.debug("Did not need to update map for %s" % mapimage.user)
    except DeadlineExceededError, err:    
      logging.error("Ran out of time before updating a map! %s" % err)
      mapimage.last_updated = datetime.now() # put it at the end of the queue anyway, in case we always fail on this map for some reason
      mapimage.put()

if __name__ == '__main__':
  raw = environ['PATH_INFO']
  if raw.count('/') == 2:
    foo, bar, rest, = raw.split('/')
    try:
      assert rest == 'one', "rest is: %s " % rest
      update_map_file()
    except AssertionError, err:
      logging.error(err.args[0])
  else:
    user = users.get_current_user()
    if user:
      create_map_file(user, raw)
