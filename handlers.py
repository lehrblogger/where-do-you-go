import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError
from google.appengine.api.datastore_errors import BadRequestError
from google.appengine.runtime import DeadlineExceededError
from os import environ
import json
import urllib
import urlparse
import logging
import time
import constants
import time
from datetime import datetime
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
      'static_url': 'http://maps.google.com/maps/api/staticmap?center=40.738152838822934%2C-73.9822769165039&format=png&zoom=13&key=AIzaSyAYBD8ThpvGz1biNHjH00lI-zuiNxdQLX4&sensor=false&size=640x640',
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
    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/all_header.html'), {'key': constants.google_maps_apikey}))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/private_welcome.html'), welcome_data))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/information.html'), {'user': user}))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/all_footer.html'), None))

class InformationWriter(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/information.html'), {'user': user}))

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
        'static_url': update_api_key_in_static_url(mapimage.static_url),
        'mapimage_url': 'map/%s.png' % mapimage.key(),
      }
      userinfo = UserInfo.all().filter('user =', mapimage.user).get()
      if userinfo:
        welcome_data['real_name'] = userinfo.real_name
        welcome_data['photo_url'] = userinfo.photo_url
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
          'static_url': update_api_key_in_static_url(mapimage.static_url),
          'mapimage_url': 'map/%s.png' % mapimage.key(),
          'public_url': 'public/%s.html' % mapimage.key(),
          'timestamp': str(time.time())
        }
        os_path = os.path.dirname(__file__)
        self.response.out.write(template.render(os.path.join(os_path, 'templates/static_map.html'), template_data))
      else:
        self.response.out.write("")

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

# Sigh this is terrible. I'm not sure why I decided to write a Google Maps API Key to the database
# as part of these URLs, but that's what I did. The correct thing to do would be to script something
# to fix all of the existing entries (which, mind you, don't all have the same old key), or maybe
# I could brush up on enough Python to put this in the MapImage model class. But alas, it's not worth
# the time to do either given the remaining life expectancy for this project, so this will have to do.
#
# Note that if I need to use signed URLs, it would be easy to hack that in here.
# https://developers.google.com/maps/documentation/maps-static/get-api-key?hl=en_US#dig-sig-key
def update_api_key_in_static_url(url):
  domain, param_string = url.split('?')
  param_dict = dict(urlparse.parse_qsl(param_string))
  param_dict['key'] = constants.google_maps_apikey
  return domain + '?' + urllib.urlencode(param_dict)

def main():
  application = webapp.WSGIApplication([('/', IndexHandler),
                                        ('/map/.*', StaticMapHandler),
                                        ('/public/.*', PublicPageHandler),
                                        ('/information', InformationWriter),
                                        ('/static_map_html', StaticMapHtmlWriter)],
                                      debug=True)
  constants.provider = provider.DBProvider()
  run_wsgi_app(application)

if __name__ == '__main__':
  main()