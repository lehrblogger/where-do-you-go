import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db

from django.utils import simplejson as json
import os
from os import environ
from google.appengine.ext.webapp import template
import logging, time
import globalvars
from google.appengine.api import images

import data
import oauth
from gheatae import consts, color_scheme, dot, tile, cache, provider
from os import environ
from models import AccessToken, Venue, Checkin, MapImage

from google.appengine.api import urlfetch
import urllib

class MapHandler(webapp.RequestHandler):
  def get_map_data(self):
    user = users.get_current_user()

    self.width = self.height = 500

    if user:
      retreived_token = AccessToken.all().filter('owner =', user).order('-created').get()
      #checkins = globalvars.provider.get_user_data(user=user)
      user_latlong = data.fetch_user_latlong(user, retreived_token)
    else:
      user_latlong = (40.7778, -73.8732)
      #checkins = []

    template_values = {
      'user': user,
      #'checkins': checkins,
      'centerlat': user_latlong[0],
      'centerlong': user_latlong[1],
      'zoom': 14,
      'width': self.width,
      'height': self.height,
    }
    return template_values

class IndexHandler(MapHandler):
  def get(self):
    data_ready = False
    map_ready = False
    url = users.create_login_url(self.request.uri)
    url_linktext = 'Login'
    map_relative_url = ''

    user = users.get_current_user()
    if user:
      auth_ready = AccessToken.all().filter('owner =', user).count() > 0
      data_ready = (Checkin.all().filter('user =', user).count() > 0) and auth_ready
      map_ready = (MapImage.all().filter('userid =', user.user_id()).count() > 0) and auth_ready
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
      map_relative_url = 'map/' + user.user_id() + '.png'

    template_values = {
      'key': globalvars.google_maps_apikey,
      'user': user,
      'data_ready': data_ready,
      'map_ready': map_ready,
      'map_relative_url': map_relative_url,
      'url': url,
      'url_linktext': url_linktext,
      }

    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/index_header.html'), template_values))
    if user and auth_ready and data_ready and map_ready:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/map_user.html'), self.get_map_data()))
    else:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/map_none.html'), self.get_map_data()))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/index_footer.html'), template_values))


class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      auth_token = self.request.get("oauth_token")
      if auth_token:
        credentials= globalvars.client.get_credentials(auth_token)
        new_token = AccessToken(owner = user, token = credentials['token'], secret = credentials['secret'])
        new_token.put()

        data.fetch_and_store_n_recent_checkins_for_token(new_token, 250)

        self.redirect("/")
      else:
        self.redirect(globalvars.client.get_authorization_url())

    else:
      self.redirect(users.create_login_url(self.request.uri))


class GenerateMapHandler(MapHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      raw = environ['PATH_INFO']
      try:
        assert raw.count('/') == 4, "%d /'s" % raw.count('/')
        foo, bar, zoom, centerpoint, northwest, = raw.split('/')
        assert zoom.isdigit(), "not digits"
        zoom = int(zoom)
        assert centerpoint.count(',') == 1, "%d /'s" % centerpoint.count(',')
        center_lat, center_long = centerpoint.split(',')
        assert northwest.count(',') == 1, "%d /'s" % northeast.count(',')
        north, west = northwest.split(',')
      except AssertionError, err:
        logging.error(err.args[0])
        return

      data = self.get_map_data()
      google_data = {
        'key': data['key'],
        'zoom': data['zoom'],
        'center': str(center_lat) + "," + str(center_long),
        'size': str(data['width']) + "x" + str(data['height']),
        'sensor':'false',
        'format':'png',
      }
      result = urlfetch.fetch(url="http://maps.google.com/maps/api/staticmap?" + urllib.urlencode(google_data),
                              method=urlfetch.GET)
      input_tuples = []
      input_tuples.append((result.content, 0, 0, 1.0, images.TOP_LEFT))

      for offset_x_px in range (0, self.width, 256):
        for offset_y_px in range (0, self.height, 256):
          logging.warning(str(offset_x_px) + ", " + str(offset_y_px))
          new_tile = tile.CustomTile(int(zoom), float(north), float(west), offset_x_px, offset_y_px)
          input_tuples.append((new_tile.image_out(), offset_x_px, offset_y_px, 1.0, images.TOP_LEFT))
          # http://code.google.com/appengine/docs/python/images/functions.html

      img = images.composite(inputs=input_tuples, width=data['width'], height=data['height'], color=0, output_encoding=images.PNG)

      mapimages = MapImage.all().filter('userid =', user.user_id()).fetch(1000)
      db.delete(mapimages)

      mapimage = MapImage()
      mapimage.userid = user.user_id()
      mapimage.cityid = 42 #TODO fix this to be real
      mapimage.centerlat = data['centerlat']
      mapimage.centerlong = data['centerlong']
      mapimage.zoom = data['zoom']
      mapimage.height = data['height']
      mapimage.width = data['width']
      mapimage.img = db.Blob(img)
      mapimage.put()

class StaticMapHandler(webapp.RequestHandler):
  def get(self):
    path = environ['PATH_INFO']
    if path.endswith('.png'):
      raw = path[:-4] # strip extension
      try:
        assert raw.count('/') == 2, "%d /'s" % raw.count('/')
        foo, bar, userid = raw.split('/')
      except AssertionError, err:
        logging.error(err.args[0])
        return
    else:
      logging.error("Invalid path: " + path)
      return

    mapimage = MapImage.all().filter('userid =', userid).get()
    if mapimage:
      self.response.headers['Content-Type'] = 'image/png'
      self.response.out.write(mapimage.img)
    else:
      logging.info("No image for " + userid)


class DeleteHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      tokens = AccessToken.all().filter('owner =', user).fetch(1000)
      db.delete(tokens)

      mapimages = MapImage.all().filter('userid =', user.user_id()).fetch(1000)
      db.delete(mapimages)

      checkins = globalvars.provider.get_user_data(user=user)
      db.delete(checkins)

    self.redirect('/')

class TileHandler(webapp.RequestHandler):
  def get(self):
    logging.info("Running GetTile:GET...")
    st = time.clock()
    path = environ['PATH_INFO']

    logging.debug("Path:" + path)
    if path.endswith('.png'):
      raw = path[:-4] # strip extension
      try:
        assert raw.count('/') == 4, "%d /'s" % raw.count('/')
        foo, bar, layer, zoom, yx = raw.split('/')
        # assert color_scheme in color_schemes, ("bad color_scheme: "
        #                                       + color_scheme
        #                                        )
        assert yx.count(',') == 1, "%d /'s" % yx.count(',')
        y, x = yx.split(',')
        assert zoom.isdigit() and x.isdigit() and y.isdigit(), "not digits"
        zoom = int(zoom)
        x = int(x)
        y = int(y)
        assert 0 <= zoom <= (consts.MAX_ZOOM - 1), "bad zoom: %d" % zoom
      except AssertionError, err:
        logging.error(err.args[0])
        self.respondError(err)
        return
    else:
      self.respondError("Invalid path")
      return

    # color_scheme = color_schemes[color_scheme]
    # try:
    new_tile = tile.GoogleTile(layer, zoom, x, y)
    #logging.info("Start-B1: %2.2f" % (time.clock() - st))
    # except Exception, err:
    #   self.respondError(err)
    #   raise err
    #   return

    self.response.headers['Content-Type'] = "image/png"
    # logging.info("Building image...")
    img_data = new_tile.image_out()
    # logging.info("Start-B2: %2.2f" % (time.clock() - st))
    # logging.info("Writing out image...")
    self.response.out.write(img_data)
    # logging.info("Start-End: %2.2f" % (time.clock() - st))

def main():
  application = webapp.WSGIApplication([('/', IndexHandler),
                                        ('/go_to_foursquare', AuthHandler),
                                        ('/authenticated', AuthHandler),
                                        ('/delete_all_my_data', DeleteHandler),
                                        ('/tile/.*', TileHandler),
                                        ('/map/.*', StaticMapHandler),
                                        ('/generate_static_map/.*', GenerateMapHandler)],
                                      debug=True)

  globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)
  globalvars.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()