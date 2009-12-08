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

from scripts import fetch_foursquare_data
import oauth
from gheatae import consts, color_scheme, dot, tile, cache, provider
from os import environ
from models import AccessToken, Venue, Checkin, MapImage

from google.appengine.api import urlfetch
import urllib

class IndexHandler(webapp.RequestHandler):
  def get(self):

    retrieved_token = None
    url = users.create_login_url(self.request.uri)
    url_linktext = 'Login'
    num_checkins = 0;

    user = users.get_current_user()
    if user:
      retrieved_token = AccessToken.all().filter('owner =', user).order('-created').get()
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
      while (len(Checkin.all().fetch(1000, num_checkins)) > 0):
        num_checkins = num_checkins + len(Checkin.all().fetch(1000, num_checkins))
      
    page_data = {
      'key': globalvars.google_maps_apikey,
      'user': user,
      'auth_ready': retrieved_token,
      'num_checkins': num_checkins,
      'url': url,
      'url_linktext': url_linktext,
      }
    
    if retrieved_token:
      user_latlong = fetch_foursquare_data.fetch_user_latlong(user, retrieved_token)
    else:
      user_latlong = (40.728397037445006, -73.99429321289062)
    map_data = {
      'user': user,
      'centerlat': user_latlong[0],
      'centerlong': user_latlong[1],
      'zoom': 14,
      'width': 640,
      'height': 640,
    }

    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/index_header.html'), page_data))
    if user and retrieved_token:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/map_user.html'), map_data))
    else:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/map_none.html'), map_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/index_footer.html'), None))


class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      auth_token = self.request.get("oauth_token")
      if auth_token:
        credentials= globalvars.client.get_credentials(auth_token)
        new_token = AccessToken(owner = user, token = credentials['token'], secret = credentials['secret'])
        new_token.put()

        fetch_foursquare_data.fetch_and_store_n_recent_checkins_for_token(new_token, 250)

        self.redirect("/")
      else:
        self.redirect(globalvars.client.get_authorization_url())

    else:
      self.redirect(users.create_login_url(self.request.uri))

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

class TileHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      st = time.clock()
      path = environ['PATH_INFO']

      # logging.debug("Path:" + path)
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
      new_tile = tile.GoogleTile(user, layer, zoom, x, y)
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

class CheckinWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      template_data = { 'checkins': globalvars.provider.get_user_data(user=user)}
      os_path = os.path.dirname(__file__)
      self.response.out.write(template.render(os.path.join(os_path, 'templates/checkin_list.html'), template_data))

class StaticMapHtmlWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      if MapImage.all().filter('user =', user).count() > 0:
        template_data = { 'map_relative_url': 'map/' + user.user_id() + '.png'}
        os_path = os.path.dirname(__file__)
        self.response.out.write(template.render(os.path.join(os_path, 'templates/static_map.html'), template_data))
      else:
        self.response.out.write("")

def main():
  application = webapp.WSGIApplication([('/', IndexHandler),
                                        ('/go_to_foursquare', AuthHandler),
                                        ('/authenticated', AuthHandler),
                                        ('/tile/.*', TileHandler),
                                        ('/map/.*', StaticMapHandler),
                                        ('/static_map_html', StaticMapHtmlWriter),
                                        ('/view_checkins', CheckinWriter)],
                                      debug=True)

  globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)
  globalvars.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()