import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError
from google.appengine.runtime import DeadlineExceededError
from django.utils import simplejson as json
import os
from os import environ
import urllib
import logging
import time
import oauth
import foursquare
import constants
import time
from datetime import datetime
from scripts import fetch_foursquare_data
from gheatae import color_scheme, tile, provider
from models import UserInfo, UserVenue, MapImage, AppToken

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
    foursquare_is_happy = True
    user = users.get_current_user()
    if user:
      welcome_data['user'] = user
      welcome_data['url'] = users.create_logout_url(self.request.uri)
      userinfo = UserInfo.all().filter('user =', user).order('-created').get()
      if userinfo:
        if userinfo.is_authorized:
          try:
            fetch_foursquare_data.update_user_info(userinfo)
          except foursquare.FoursquareRemoteException, err:
            if str(err).find('403 Forbidden') >= 0:
              foursquare_is_happy = False
            else:
              pass # raise err  #TODO keep this error, but removing it now so that you can log in
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
    if not foursquare_is_happy:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/private_forbidden.html'), None))
    elif user and userinfo:
      if userinfo.is_authorized:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/private_sidebar.html'), sidebar_data))
      else:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/private_unauthorized.html'), None))
    else:
        self.response.out.write(template.render(os.path.join(os_path, 'templates/information.html'), {'user': user }))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/private_map.html'), map_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/all_footer.html'), None))

class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      oauth_token = self.request.get("oauth_token")

      def get_new_fs_and_credentials():
        oauth_token, oauth_secret = constants.get_oauth_strings()
        credentials = foursquare.OAuthCredentials(oauth_token, oauth_secret)
        fs = foursquare.Foursquare(credentials)
        return fs, credentials

      if oauth_token:
        old_userinfos = UserInfo.all().filter('user =', user).fetch(500)
        db.delete(old_userinfos)
        fs, credentials = get_new_fs_and_credentials()
        apptoken = AppToken.all().filter('token =', oauth_token).get()
        
        try:
          user_token = fs.access_token(oauth.OAuthToken(apptoken.token, apptoken.secret))
          credentials.set_access_token(user_token)
          userinfo = UserInfo(user = user, token = credentials.access_token.key, secret = credentials.access_token.secret, is_ready=False, is_authorized=True, last_checkin=0, last_updated=datetime.now(), color_scheme='fire', level_max=int(constants.level_const), checkin_count=0, venue_count=0)
        except DownloadError, err:
          if str(err).find('ApplicationError: 5') >= 0:
            pass # if something bad happens on OAuth, then it currently just redirects to the signup page
                 #TODO find a better way to handle this case, but it's not clear there is a simple way to do it without messing up a bunch of code
          else:
            raise err
        try:
          fetch_foursquare_data.update_user_info(userinfo)
          fetch_foursquare_data.fetch_and_store_checkins(userinfo, limit=10)
          taskqueue.add(url='/fetch_foursquare_data/all_for_user/%s' % userinfo.key())
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
        fs, credentials = get_new_fs_and_credentials()
        app_token = fs.request_token()
        auth_url = fs.authorize(app_token)
        new_apptoken = AppToken(token = app_token.key, secret = app_token.secret)
        new_apptoken.put()
        self.redirect(auth_url)
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
        'static_url': mapimage.static_url,
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
      usevenues = constants.provider.get_user_data(user=user)
      if not uservenue.checkin_guid_list or len(uservenue.checkin_guid_list) is 0:
        uservenue.checkin_guid_list = [str(checkin_id) for checkin_id in uservenue.checkin_list]
        usevenue.put()
      template_data = { 'uservenues': usevenues}
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
          'static_url': mapimage.static_url,
          'mapimage_url': 'map/%s.png' % mapimage.key(),
          'public_url': 'public/%s.html' % mapimage.key(),
          'timestamp': str(time.time())
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
  constants.provider = provider.DBProvider()
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()