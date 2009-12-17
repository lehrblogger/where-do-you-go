import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from django.utils import simplejson as json
import os
from os import environ
import urllib
import logging
import time
import oauth
import constants
from scripts import fetch_foursquare_data
from gheatae import color_scheme, tile, provider
from models import UserInfo, UserVenue, MapImage

class IndexHandler(webapp.RequestHandler):
  def get(self):
    page_data = {
      'user': '',
      'userinfo': '',
      'url': users.create_login_url(self.request.uri),
      'real_name': '',
      'photo_url': constants.default_photo,
    }
    user_data = {
      'color_scheme_dict': color_scheme.color_schemes,
      'color_scheme': constants.default_color,
    }
    map_data = {
      'centerlat': constants.default_lat,
      'centerlng': constants.default_lng,
      'zoom': 14,
      'width': 640,
      'height': 640,
    }
    user = users.get_current_user()
    if user:
      page_data['user'] = user
      page_data['url'] = users.create_logout_url(self.request.uri)
      userinfo = UserInfo.all().filter('user =', user).order('-created').get()
      if userinfo:
        fetch_foursquare_data.update_user_info(userinfo)
        page_data['userinfo'] = userinfo
        page_data['real_name'] = userinfo.real_name
        page_data['photo_url'] = userinfo.photo_url
        user_data['color_scheme'] = userinfo.color_scheme
        map_data['citylat'] = userinfo.citylat
        map_data['citylng'] = userinfo.citylng
    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), {'key': constants.get_google_maps_apikey()}))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/welcome.html'), page_data))
    if user and userinfo:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/map_controls.html'), user_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/map_all.html'), map_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/footer.html'), None))

class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      auth_token = self.request.get("oauth_token")
      if auth_token:
        credentials= constants.client.get_credentials(auth_token)
        old_userinfos = UserInfo.all().filter('user =', user).fetch(500)
        db.delete(old_userinfos)
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
      new_tile = tile.GoogleTile(user, zoom, x, y)
      self.response.headers['Content-Type'] = "image/png"
      img_data = new_tile.image_out()
      self.response.out.write(img_data)

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
      template_data = {
        'mapimage_url': 'mapimage/%s.png' % mapimage.key(),
        'publicpage_url': 'publicpage/%s.html' % mapimage.key(),
      }
      os_path = os.path.dirname(__file__)
      self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), {'key': constants.get_google_maps_apikey()}))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/public_map.html'), template_data))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/footer.html'), None))
    else:
      self.redirect("/")

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
        template_data = {
          'domain': environ['HTTP_HOST'],
          'mapimage_url': 'mapimage/%s.png' % mapimage.key(),
          'publicpage_url': 'publicpage/%s.html' % mapimage.key(),
        }
        os_path = os.path.dirname(__file__)
        self.response.out.write(template.render(os.path.join(os_path, 'templates/static_map.html'), template_data))
      else:
        self.response.out.write("")

def main():
  application = webapp.WSGIApplication([('/', IndexHandler),
                                        ('/go_to_foursquare', AuthHandler),
                                        ('/authenticated', AuthHandler),
                                        ('/tile/.*', TileHandler),
                                        ('/mapimage/.*', StaticMapHandler),
                                        ('/publicpage/.*', PublicPageHandler),
                                        ('/static_map_html', StaticMapHtmlWriter),
                                        ('/view_uservenues', UserVenueWriter)],
                                      debug=True)
  oauth_strings = constants.get_oauth_strings()
  constants.client = oauth.FoursquareClient(oauth_strings[0], oauth_strings[1], oauth_strings[2])
  constants.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()