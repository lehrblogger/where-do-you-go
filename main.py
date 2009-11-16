#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import wsgiref.handlers
import oauth
from get_recent_checkins import fetch_and_store_n_recent_checkins_for_token
from models import Token, Venue, Checkin
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson as json
import os
from google.appengine.ext.webapp import template
import logging
import tile

class MainHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      url = users.create_logout_url(self.request.uri)
      map_ready = Checkin.all().filter('user =', user).count() > 0
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      map_ready = False
      url_linktext = 'Login'

    template_values = {
      'user': user,
      'map_ready': map_ready,
      'url': url,
      'url_linktext': url_linktext,
      }

    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), None))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/main.html')  , template_values))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/footer.html'), None))

class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      auth_token = self.request.get("oauth_token")
      if auth_token:
        credentials= client.get_credentials(auth_token)
        new_token = Token(owner = user, token = credentials['token'], secret = credentials['secret'])
        new_token.put()

        fetch_and_store_n_recent_checkins_for_token(new_token, 50, client)

        self.redirect("/map")
      else:
        self.redirect(client.get_authorization_url())

    else:
      self.redirect(users.create_login_url(self.request.uri))

class MapHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      retreived_token = Token.all().filter('owner =', user).order('-created').get()
      checkins = Checkin.all().filter('user =', user).order('-created').fetch(1000)

      response = client.make_request("http://api.foursquare.com/v1/user.json", token = retreived_token.token, secret = retreived_token.secret)
      user_info = json.loads(response.content)

      logging.debug(user_info)
      user_lat = user_info['user']['city']['geolat']
      user_long = user_info['user']['city']['geolong']
    else:
      user_lat = 40.7778
      user_long = -73.8732

    template_values = {
      'user': user,
      'checkins': checkins,
      'centerlat': user_lat,
      'centerlong': user_long,
    }

    os_path = os.path.dirname(__file__)
    self.response.out.write(template.render(os.path.join(os_path, 'templates/header.html'), None))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/map.html')   , template_values))
    self.response.out.write(template.render(os.path.join(os_path, 'templates/footer.html'), None))

class DeleteHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      tokens = Token.all().filter('owner =', user).fetch(1000)
      db.delete(tokens)

      checkins = Checkin.all().filter('user =', user).fetch(1000)
      db.delete(checkins)

    self.redirect('/')

def main():
  application = webapp.WSGIApplication(
                                       [('/', MainHandler),
                                        ('/go_to_foursquare', AuthHandler),
                                        ('/authenticated', AuthHandler),
                                        ('/delete_all_my_data', DeleteHandler),
                                        ('/map', MapHandler),
                                        ('/tile/.*', tile.GetTile)],
                                       debug=True)

  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  consumer_key = "98ff47ad5541ebaaee51cb5a1e843d1404aeba03f"
  consumer_secret = "f661bcab0416f66a2c6633cde08aefd5"
  callback_url = " http://where-do-you-go.appspot.com/callback/foursquare"

  client = oauth.FoursquareClient(consumer_key, consumer_secret, callback_url)
  main()




