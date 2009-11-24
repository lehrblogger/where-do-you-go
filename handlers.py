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


class IndexHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      data_ready = (Checkin.all().filter('user =', user).count() > 0) and (AccessToken.all().filter('owner =', user).count() > 0)
      map_ready = (MapImage.all().filter('user =', user).count() > 0) and (AccessToken.all().filter('owner =', user).count() > 0)
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
      'apikey': 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBQO7aMTgd18mR6eRdj9blrVCeGU7BS14EnkGH_2LpNpZ8DJW0u7G5ocLQ',
      'user': user,
      'checkins': checkins,
      'centerlat': user_latlong[0],
      'centerlong': user_latlong[1],
      'zoomlevel': 14,
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
    data = self.get_map_data()

    "http://maps.google.com/maps/api/staticmap?center=" + data['centerlat'] + "," + data['centerlong'] + "&zoom=1&size=500x500&key=" + data['apikey'] + "&sensor=false&format=png"

    input_tuples = []
    # input_tuples.append()

    img = images.composite(inputs=input_tuples, width=500, height=500, color=0, output_encoding=PNG)

    map_image = MapImage()
    map_image.user = data['user']
    map_image.img = db.Blob(img)
    map_image.put()

    self.redirect('/')

class StaticMapHandler(webapp.RequestHandler):
  def get(self):
    logging.debug('return .png file here')


class DeleteHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      tokens = AccessToken.all().filter('owner =', user).fetch(1000)
      db.delete(tokens)

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
                                        ('/js_map', JsMapHandler),
                                        ('/generate_static_map', GenerateMapHandler),
                                        ('/tile/.*', TileHandler)],
                                       debug=True)

  globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)
  globalvars.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()





