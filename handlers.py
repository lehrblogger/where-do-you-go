import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.runtime import DeadlineExceededError
from django.utils import simplejson as json
import os
from os import environ
import urllib
import logging
import time
import oauth
import constants
from datetime import datetime
from scripts import fetch_foursquare_data
from gheatae import color_scheme, tile, provider
from models import UserInfo, UserVenue, MapImage

class IndexHandler(webapp.RequestHandler):
  def get(self):
    welcome_data = {
      'user': '',
      'userinfo': '',
      'url': users.create_login_url(self.request.uri),
      'real_name': '',
      'photo_url': constants.default_photo,
      'is_ready': False
    }
    sidebar_data = {
      'color_scheme_dict': color_scheme.color_schemes,
      'color_scheme': constants.default_color,
    }
    map_data = {
      'citylat': constants.default_lat,
      'citylng': constants.default_lng,
      'zoom': constants.default_zoom,
      'width': constants.default_dimension,
      'height': constants.default_dimension,
    }
    user = users.get_current_user()
    if user:
      welcome_data['user'] = user
      welcome_data['url'] = users.create_logout_url(self.request.uri)
      userinfo = UserInfo.all().filter('user =', user).order('-created').get()
      if userinfo:
        fetch_foursquare_data.update_user_info(userinfo)
        welcome_data['userinfo'] = userinfo
        welcome_data['real_name'] = userinfo.real_name
        welcome_data['photo_url'] = userinfo.photo_url
        welcome_data['is_ready'] = userinfo.is_ready
        sidebar_data['color_scheme'] = userinfo.color_scheme
        map_data['citylat'] = userinfo.citylat
        map_data['citylng'] = userinfo.citylng
    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), {'key': constants.get_google_maps_apikey()}))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/private_welcome.html'), welcome_data))
    if user and userinfo:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/private_sidebar.html'), sidebar_data))
    else:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/information.html'), None))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/private_map.html'), map_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/all_footer.html'), None))

class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      auth_token = self.request.get("oauth_token")
      if auth_token:
        credentials= constants.client.get_credentials(auth_token)
        old_userinfos = UserInfo.all().filter('user =', user).fetch(500)
        db.delete(old_userinfos)
        userinfo = UserInfo(user = user, token = credentials['token'], secret = credentials['secret'], is_ready=False, last_checkin=0, last_updated=datetime.now(), color_scheme='fire', level_max=int(constants.level_const), checkin_count=0, venue_count=0)
        fetch_foursquare_data.update_user_info(userinfo)
        fetch_foursquare_data.fetch_and_store_checkins(userinfo, limit=10)
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
      self.redirect("/")

class TileHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      path = environ['PATH_INFO']
      if path.endswith('.png'):
        raw = path[:-4] # strip extension
        try:
          assert raw.count('/') == 4, "%d /'s" % raw.count('/')
          foo, bar, layer, zoom, yx = raw.split('/') #tile is ignored, is just here to prevent caching
          assert yx.count(',') == 1, "%d /'s" % yx.count(',')
          y, x = yx.split(',')
          assert zoom.isdigit() and x.isdigit() and y.isdigit(), "not digits"
          zoom = int(zoom)
          x = int(x)
          y = int(y)
          assert constants.min_zoom <= zoom <= constants.max_zoom, "bad zoom: %d" % zoom
        except AssertionError, err:
          logging.error(err.args[0])
          self.respondError(err)
          return
      else:
        self.respondError("Invalid path")
        return

      try:
        new_tile = tile.GoogleTile(user, zoom, x, y)
        img_data = new_tile.image_out()
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write(img_data)
      except DeadlineExceededError, err:
        logging.warning(err.args[0])
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write('')

class PublicPageHandler(webapp.RequestHandler):
  def get(self):
    path = environ['PATH_INFO']
    if path.endswith('.html'):
      raw = path[:-5] # strip extension
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
      welcome_data = {
        'real_name': '',
        'photo_url': constants.default_photo,
      }
      sidebar_data = {
        'domain': environ['HTTP_HOST'],
        'public_url': 'public/%s.html' % mapimage.key(),
      }
      map_data = {
        'domain': environ['HTTP_HOST'],
        'mapimage_url': 'map/%s.png' % mapimage.key(),
      }
      userinfo = UserInfo.all().filter('user =', mapimage.user).order('-created').get()
      if userinfo:
        welcome_data['real_name'] = userinfo.real_name
        welcome_data['photo_url'] = userinfo.photo_url
        #welcome_data['checkin_count'] = userinfo.checkin_count
      os_path = os.path.dirname(__file__)
      self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), None))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/public_welcome.html'), welcome_data))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/public_sidebar.html'), sidebar_data))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/public_map.html'), map_data))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/all_footer.html'), None))
    else:
      self.redirect("/")

class UserVenueWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      userinfo = UserInfo.all().filter('user =', user).order('-created').get()
      if userinfo:
          self.response.out.write(str(userinfo))
      template_data = { 'uservenues': constants.provider.get_user_data(user=user)}
      os_path = os.path.dirname(__file__)
      self.response.out.write(template.render(os.path.join(os_path, 'templates/uservenue_list.html'), template_data))

class StaticMapHtmlWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      mapimage = MapImage.all().filter('user =', user).get()
      if mapimage:
        template_data = {
          'domain': environ['HTTP_HOST'],
          'mapimage_url': 'map/%s.png' % mapimage.key(),
          'public_url': 'public/%s.html' % mapimage.key(),
        }
        os_path = os.path.dirname(__file__)
        self.response.out.write(template.render(os.path.join(os_path, 'templates/static_map.html'), template_data))
      else:
        self.response.out.write("")

class ReadyInfoWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      userinfo = UserInfo.all().filter('user =', user).get() #.order('-created')
      if userinfo:
          self.response.out.write(str(userinfo.is_ready) + ',' + str(userinfo.checkin_count))
          return
    self.response.out.write("")

def main():
  application = webapp.WSGIApplication([('/', IndexHandler),
                                        ('/go_to_foursquare', AuthHandler),
                                        ('/authenticated', AuthHandler),
                                        ('/tile/.*', TileHandler),
                                        ('/map/.*', StaticMapHandler),
                                        ('/public/.*', PublicPageHandler),
                                        ('/static_map_html', StaticMapHtmlWriter),
                                        ('/user_is_ready', ReadyInfoWriter),
                                        ('/view_uservenues', UserVenueWriter)],
                                      debug=True)
  oauth_strings = constants.get_oauth_strings()
  constants.client = oauth.FoursquareClient(oauth_strings[0], oauth_strings[1], oauth_strings[2])
  constants.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()