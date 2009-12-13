import os
from os import environ
import globalvars
from google.appengine.ext import db
from google.appengine.api import users
from models import AuthToken, UserInfo, UserVenue, MapImage
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

    while(UserInfo.all().count() > 0):
      userinfos = UserInfo.all().fetch(500)
      db.delete(userinfos)

    while(UserVenue.all().count() > 0):
      uservenues = UserVenue.all().fetch(500)
      db.delete(uservenues)

    while(MapImage.all().count() > 0):
      mapimages = MapImage.all().fetch(500)
      db.delete(mapimages)

  elif rest == 'user':
    user = users.get_current_user()
    if user:
      while(UserInfo.all().filter('user =', user).count() > 0):
        userinfos = UserInfo.all().filter('user =', user).fetch(500)
        db.delete(userinfos)

      while(UserVenue.all().filter('user = ', user).count() > 0):
        uservenues = UserVenue.all().filter('user = ', user).fetch(500)
        db.delete(uservenues)

      while(MapImage.all().filter('user =', user).count() > 0):
        mapimages = MapImage.all().filter('user =', user).fetch(500)
        db.delete(mapimages)