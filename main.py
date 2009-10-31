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
from models import FoursquareToken, Venue, Checkin
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson as json

class MainHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()

    if user:
      self.response.out.write('Hello there, ' + user.nickname() + '. Where do you go?')
      self.response.out.write('<br/><br/>')
      self.response.out.write('<a href="/go_to_foursquare">authenticate with oauth</a>')
    
    else:
      self.redirect(users.create_login_url(self.request.uri))

class AuthHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    
    if user: 
      auth_token = self.request.get("oauth_token")
      if auth_token:
        credentials= client.get_credentials(auth_token)
        new_token = FoursquareToken(owner = user, token = credentials['token'], secret = credentials['secret'])
        new_token.put()
    
        self.redirect("/map")
      else:
        self.redirect(client.get_authorization_url())

    else:
      self.redirect(users.create_login_url(self.request.uri))

class MapHandler(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    
    if user:
      retreived_token = FoursquareToken.all().filter('owner =', user).order('-created').get()
     
      self.response.out.write('<object width="640" height="505"><param name="movie" value="http://www.youtube.com/v/Uc0moUPBJnM&hl=en&fs=1&rel=0"></param><param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param><embed src="http://www.youtube.com/v/Uc0moUPBJnM&hl=en&fs=1&rel=0" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="640" height="505"></embed></object>')
      self.response.out.write('<br/><br/>')
      response = client.make_request("http://api.foursquare.com/v1/history.json", token = retreived_token.token, secret = retreived_token.secret)   
      history = json.loads(response.content)
      self.response.out.write(history)
    
def main():
  application = webapp.WSGIApplication(
                                       [('/', MainHandler),
                                        ('/go_to_foursquare', AuthHandler),
                                        ('/authenticated', AuthHandler),
                                        ('/map', MapHandler)],
                                       debug=True)

  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  consumer_key = "98ff47ad5541ebaaee51cb5a1e843d1404aeba03f"
  consumer_secret = "f661bcab0416f66a2c6633cde08aefd5"
  callback_url = " http://where-do-you-go.appspot.com/callback/foursquare"

  client = oauth.FoursquareClient(consumer_key, consumer_secret, callback_url)
  main()




