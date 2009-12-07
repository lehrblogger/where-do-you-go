import os
from os import environ
import globalvars
from google.appengine.ext import db
from google.appengine.api import users
from models import AuthToken, AccessToken, Venue, Checkin, MapImage
from gheatae import provider

if __name__ == '__main__':
  raw = environ['PATH_INFO']
  assert raw.count('/') == 2, "%d /'s" % raw.count('/')
  foo, bar, rest, = raw.split('/')

  if not globalvars.provider:
    globalvars.provider = provider.DBProvider()

  if rest == 'all':
    while(AuthToken.all().count() > 0):
      authtokens = AuthToken.all().fetch(500)
      db.delete(authtokens)

    while(AccessToken.all().count() > 0):
      tokens = AccessToken.all().fetch(500)
      db.delete(tokens)

    while(Venue.all().count() > 0):
      venues = Venue.all().fetch(500)
      db.delete(venues)

    while(Checkin.all().count() > 0):
      checkins = Checkin.all().fetch(500)
      db.delete(checkins)

    while(MapImage.all().count() > 0):
      mapimages = MapImage.all().fetch(500)
      db.delete(mapimages)

  elif rest == 'user':
    user = users.get_current_user()
    if user:
      while(AccessToken.all().filter('owner =', user).count() > 0):
        tokens = AccessToken.all().filter('owner =', user).fetch(500)
        db.delete(tokens)

      while(Checkin.all().filter('user = ', user).count() > 0):
        checkins = Checkin.all().filter('user = ', user).fetch(500)
        db.delete(checkins)

      while(MapImage.all().filter('user =', user).count() > 0):
        mapimages = MapImage.all().filter('user =', user).fetch(500)
        db.delete(mapimages)