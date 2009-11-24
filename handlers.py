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




class IndexHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      auth_ready = AccessToken.all().filter('owner =', user).count() > 0
      data_ready = (Checkin.all().filter('user =', user).count() > 0) and auth_ready
      map_ready = (MapImage.all().filter('userid =', user.user_id()).count() > 0) and auth_ready
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      data_ready = False
      map_ready = False
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'user': user,
      'data_ready': data_ready,
      'map_ready': map_ready,
      'map_relative_url': 'map/' + user.user_id() + '.png',
      'url': url,
      'url_linktext': url_linktext,
      }

    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), None))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/index.html')  , template_values))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/footer.html'), None))

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

        self.redirect("/js_map")
      else:
        self.redirect(globalvars.client.get_authorization_url())

    else:
      self.redirect(users.create_login_url(self.request.uri))

class MapHandler(webapp.RequestHandler):
  def get_map_data(self):
    user = users.get_current_user()

    if user:
      retreived_token = AccessToken.all().filter('owner =', user).order('-created').get()
      checkins = globalvars.provider.get_user_data(user=user)
      user_latlong = data.fetch_user_latlong(user, retreived_token)
    else:
      user_latlong = (40.7778, -73.8732)

    template_values = {
      'key': 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBQO7aMTgd18mR6eRdj9blrVCeGU7BS14EnkGH_2LpNpZ8DJW0u7G5ocLQ',
      'user': user,
      'checkins': checkins,
      'centerlat': user_latlong[0],
      'centerlong': user_latlong[1],
      'zoom': 14,
      'width': 500,
      'height': 500,
    }
    return template_values


class JsMapHandler(MapHandler):
  def get(self):
    template_values = self.get_map_data()
    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), None))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/map.html')   , template_values))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/footer.html'), None))

class GenerateMapHandler(MapHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      data = self.get_map_data()
      google_data = {
        'key': data['key'],
        'zoom': data['zoom'],
        'center': str(data['centerlat']) + "," + str(data['centerlong']),
        'size': str(data['width']) + "x" + str(data['height']),
        'sensor':'false',
        'format':'png',
      }
      result = urlfetch.fetch(url="http://maps.google.com/maps/api/staticmap?" + urllib.urlencode(google_data),
                              method=urlfetch.GET)
      input_tuples = []
      input_tuples.append((result.content, 0, 0, 1.0, images.TOP_LEFT))

      result = urlfetch.fetch(url="http://where-do-you-go.appspot.com/tile/classic/13/3079,2412.png",
                              method=urlfetch.GET)
      input_tuples.append((result.content, 0, 0, 1.0, images.CENTER_CENTER))

      img = images.composite(inputs=input_tuples, width=data['width'], height=data['height'], color=0, output_encoding=images.PNG)

      mapimages = MapImage.all().filter('userid =', user.user_id()).fetch(1000)
      db.delete(mapimages)

      mapimage = MapImage()
      mapimage.userid = user.user_id()
      mapimage.centerlat = data['centerlat']
      mapimage.centerlong = data['centerlong']
      mapimage.zoom = data['zoom']
      mapimage.height = data['height']
      mapimage.width = data['width']
      mapimage.img = db.Blob(img)
      mapimage.put()

    self.redirect('/')

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
    new_tile = tile.Tile(layer, zoom, x, y)
    logging.info("Start-B1: %2.2f" % (time.clock() - st))
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
                                        ('/js_map', JsMapHandler),
                                        ('/map/.*', StaticMapHandler),
                                        ('/generate_static_map', GenerateMapHandler)],
                                      debug=True)

  globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)
  globalvars.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()