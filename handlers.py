import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue

from django.utils import simplejson as json
import os
from os import environ
from google.appengine.ext.webapp import template
import logging, time
import constants
from google.appengine.api import images

from scripts import fetch_foursquare_data
import oauth
from gheatae import color_scheme, tile, provider
from os import environ
from models import UserInfo, UserVenue, MapImage

from google.appengine.api import urlfetch
import urllib

class IndexHandler(webapp.RequestHandler):
  def get(self):
    page_data = {
      'key': constants.get_google_maps_apikey(),
      'user': '',
      'userinfo': '',
      'url': users.create_login_url(self.request.uri),
      'url_linktext': 'Login',
      'real_name': '',
      'photo_url': constants.default_photo,
    }
    user_data = {
      'color_scheme_dict': color_scheme.color_schemes,
      'color_scheme': constants.default_color,
    }
    map_data = {
      'centerlat': constants.default_lat,
      'centerlong': constants.default_lng,
      'zoom': 14,
      'width': 640,
      'height': 640,
    }

    user = users.get_current_user()
    if user:
      page_data['user'] = user
      page_data['url'] = users.create_logout_url(self.request.uri)
      page_data['url_linktext'] = 'Logout'
      userinfo = UserInfo.all().filter('user =', user).order('-created').get()
      if userinfo:
        fetch_foursquare_data.update_user_info(userinfo)
        page_data['userinfo'] = userinfo
        user_data['real_name'] = userinfo.real_name
        user_data['photo_url'] = userinfo.photo_url
        user_data['color_scheme'] = userinfo.color_scheme
        map_data['citylat'] = userinfo.citylat
        map_data['citylong'] = userinfo.citylng

    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/index_top.html'), page_data))
    if user and userinfo:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/map_controls.html'), user_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/map_all.html'), map_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/index_bottom.html'), None))

class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      auth_token = self.request.get("oauth_token")
      if auth_token:
        credentials= constants.client.get_credentials(auth_token)
        userinfo = UserInfo(user = user, token = credentials['token'], secret = credentials['secret'])
        userinfo.put()

        fetch_foursquare_data.fetch_and_store_checkins(userinfo)
        taskqueue.add(url='/fetch_foursquare_data/all_for_user/%s' % userinfo.key())#, queue_name='initial-checkin-fetching')

        self.redirect("/")
      else:
        self.redirect(constants.client.get_authorization_url())

    else:
      self.redirect(users.create_login_url(self.request.uri))

class StaticMapHandler(webapp.RequestHandler):
  def get(self):
    path = environ['PATH_INFO']
    if path.endswith('.png'):
      raw = path[:-4] # strip extension
      try:
        assert raw.count('/') == 2, "%d /'s" % raw.count('/')
        foo, bar, map_key = raw.split('/')
      except AssertionError, err:
        logging.error(err.args[0])
        return
    else:
      logging.error("Invalid path: " + path)
      return

    mapimage = db.get(map_key)
    if mapimage:
      self.response.headers['Content-Type'] = 'image/png'
      self.response.out.write(mapimage.img)
    else:
      logging.info("No mapimage with key " + map_key)

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
          foo, bar, layer, zoom, yx = raw.split('/') #tile is ignored, is just here to prevent caching
          # assert color_scheme in color_schemes, ("bad color_scheme: "
          #                                       + color_scheme
          #                                        )
          assert yx.count(',') == 1, "%d /'s" % yx.count(',')
          y, x = yx.split(',')
          assert zoom.isdigit() and x.isdigit() and y.isdigit(), "not digits"
          zoom = int(zoom)
          x = int(x)
          y = int(y)
          assert 0 <= zoom <= (constants.max_zoom - 1), "bad zoom: %d" % zoom
        except AssertionError, err:
          logging.error(err.args[0])
          self.respondError(err)
          return
      else:
        self.respondError("Invalid path")
        return

      # color_scheme = color_schemes[color_scheme]
      # try:
      new_tile = tile.GoogleTile(user, zoom, x, y)
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

class UserVenueWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      template_data = { 'uservenues': constants.provider.get_user_data(user=user)}
      os_path = os.path.dirname(__file__)
      self.response.out.write(template.render(os.path.join(os_path, 'templates/uservenue_list.html'), template_data))

class StaticMapHtmlWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      mapimage = MapImage.all().filter('user =', user).get()
      if mapimage:
        template_data = { 'map_relative_url': 'map/%s.png' % mapimage.key()}
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
                                        ('/view_uservenues', UserVenueWriter)],
                                      debug=True)

  constants.client = oauth.FoursquareClient(constants.consumer_key, constants.consumer_secret, constants.callback_url)
  constants.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()