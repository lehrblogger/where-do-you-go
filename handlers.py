import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.0')

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError
from google.appengine.api.datastore_errors import BadRequestError
from google.appengine.runtime import DeadlineExceededError
from django.utils import simplejson as json
from os import environ
import urllib
import logging
import time
import foursquarev2 as foursquare
import constants
import time
from datetime import datetime
from scripts import manage_foursquare_data
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
      'domain': environ['HTTP_HOST'],
      'static_url': 'http://maps.google.com/maps/api/staticmap?center=40.738152838822934%2C-73.9822769165039&format=png&zoom=13&key=ABQIAAAAwA6oEsCLgzz6I150wm3ELBSujOi3smKLcjzph36ZE8UXngM_5BTs-xHblsuwK8V9g8bZ_PTfOWR1Fg&sensor=false&size=640x640',
      'mapimage_url': 'map/%s.png' % 'ag93aGVyZS1kby15b3UtZ29yEQsSCE1hcEltYWdlGNL0_wIM',
    }
    user = users.get_current_user()
    if user:
      welcome_data['user'] = user
      welcome_data['url'] = users.create_logout_url(self.request.uri)
      userinfo = UserInfo.all().filter('user =', user).get()
      if userinfo:
        welcome_data['userinfo'] = userinfo
        welcome_data['real_name'] = userinfo.real_name
        welcome_data['photo_url'] = userinfo.photo_url
        welcome_data['is_ready'] = userinfo.is_ready
        sidebar_data['color_scheme'] = userinfo.color_scheme
        map_data['citylat'] = userinfo.citylat
        map_data['citylng'] = userinfo.citylng
    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/all_header.html'), {'key': constants.google_maps_apikey}))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/private_welcome.html'), welcome_data))
    if user and userinfo:
      if userinfo.has_been_cleared:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/information.html'), {'user': user, 'has_been_cleared': userinfo.has_been_cleared}))
      elif userinfo.is_authorized:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/private_sidebar.html'), sidebar_data))
      else:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/private_unauthorized.html'), None))
    else:
      self.response.out.write(template.render(os.path.join(os_path, 'templates/information.html'), {'user': user, 'has_been_cleared': False}))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/private_map.html'), map_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/all_footer.html'), None))

class InformationWriter(webapp.RequestHandler): #NOTE this defaults to the has_been_cleared case for now, since that's the only one that's used
  def get(self):
    user = users.get_current_user()
    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/information.html'), {'user': user, 'has_been_cleared': True}))

class AuthHandler(webapp.RequestHandler):
  def _get_new_fs_and_credentials(self):
    consumer_key, oauth_secret, url = constants.get_oauth_strings()
    fs = foursquare.FoursquareAuthHelper(key=consumer_key, secret=oauth_secret, redirect_uri=url)
    return fs, None
    
  def get(self):
    user = users.get_current_user()
    if user:
      code = self.request.get("code")
      if code:
        old_userinfos = UserInfo.all().filter('user =', user).fetch(500)
        db.delete(old_userinfos)
        fs, credentials = self._get_new_fs_and_credentials()
        try:
          user_token = fs.get_access_token(code)
          userinfo = UserInfo(user = user, token = user_token, secret = None, is_ready=False, is_authorized=True, level_max=int(3 * constants.level_const))
        except DownloadError, err:
          if str(err).find('ApplicationError: 5') >= 0:
            pass # if something bad happens on OAuth, then it currently just redirects to the signup page
                 #TODO find a better way to handle this case, but it's not clear there is a simple way to do it without messing up a bunch of code
          else:
            raise err
        try:
          manage_foursquare_data.update_user_info(userinfo)
          manage_foursquare_data.fetch_and_store_checkins_next(userinfo, limit=50)
        except foursquare.FoursquareRemoteException, err:
          if str(err).find('403 Forbidden') >= 0:
            pass # if a user tries to sign up while my app is blocked, then it currently just redirects to the signup page
                 #TODO find a better way to handle this case, but it's not clear there is a simple way to do it without messing up a bunch of code
          else:
            raise err
        except DownloadError:
          pass #TODO make this better, but I'd rather throw the user back to the main page to try again than show the user an error.
        self.redirect("/")
      else:
        fs, credentials = self._get_new_fs_and_credentials()
        self.redirect(fs.get_authentication_url())
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
    mapimage = convert_map_key(map_key)
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
      start = datetime.now()
      try:
        new_tile = tile.GoogleTile(user, zoom, x, y)
        img_data = new_tile.image_out()
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write(img_data)
      except DeadlineExceededError, err:
        logging.warning('%s error - started at %s, failed at %s' % (str(err), start, datetime.now()))
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
    mapimage = convert_map_key(map_key)
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
        'static_url': mapimage.static_url,
        'mapimage_url': 'map/%s.png' % mapimage.key(),
      }
      userinfo = UserInfo.all().filter('user =', mapimage.user).get()
      if userinfo:
        welcome_data['real_name'] = userinfo.real_name
        welcome_data['photo_url'] = userinfo.photo_url
        #welcome_data['checkin_count'] = userinfo.checkin_count
      os_path = os.path.dirname(__file__)
      self.response.out.write(template.render(os.path.join(os_path, 'templates/all_header.html'), None))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/public_welcome.html'), welcome_data))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/public_sidebar.html'), sidebar_data))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/public_map.html'), map_data))
      self.response.out.write(template.render(os.path.join(os_path, 'templates/all_footer.html'), None))
    else:
      self.redirect("/")

class StaticMapHtmlWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      mapimage = MapImage.all().filter('user =', user).get()
      if mapimage:
        template_data = {
          'domain': environ['HTTP_HOST'],
          'static_url': mapimage.static_url,
          'mapimage_url': 'map/%s.png' % mapimage.key(),
          'public_url': 'public/%s.html' % mapimage.key(),
          'timestamp': str(time.time())
        }
        os_path = os.path.dirname(__file__)
        self.response.out.write(template.render(os.path.join(os_path, 'templates/static_map.html'), template_data))
      else:
        self.response.out.write("")

class UserReadyEndpoint(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      userinfo = UserInfo.all().filter('user =', user).get()
      if userinfo:
        self.response.out.write(str(userinfo.has_been_cleared) + ',' + str(userinfo.is_ready) + ',' + str(userinfo.checkin_count))
        return
    self.response.out.write('error')

class MapDoneEndpoint(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      mapimage = MapImage.all().filter('user =', user).get()
      if mapimage:
        self.response.out.write(str(mapimage.tiles_remaining == 0))
        return
    self.response.out.write('error')

def convert_map_key(map_key):
  try:
    return db.get(map_key)
  except BadRequestError, err:
    if err.message == 'app s~where-do-you-go-hrd cannot access app where-do-you-go\'s data':
      old_key = db.Key(map_key)
      new_key = db.Key.from_path(old_key.kind(), old_key.id())
      return db.get(new_key)
    else:
      raise BadRequestError, err

def main():
  application = webapp.WSGIApplication([('/', IndexHandler),
                                        ('/go_to_foursquare', AuthHandler),
                                        ('/authenticated', AuthHandler),
                                        ('/tile/.*', TileHandler),
                                        ('/map/.*', StaticMapHandler),
                                        ('/public/.*', PublicPageHandler),
                                        ('/information', InformationWriter),
                                        ('/static_map_html', StaticMapHtmlWriter),
                                        ('/user_is_ready/.*', UserReadyEndpoint),
                                        ('/map_is_done/', MapDoneEndpoint)],
                                      debug=True)
  constants.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()