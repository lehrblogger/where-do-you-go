import os
from os import environ
import constants
from google.appengine.ext import db
from google.appengine.api import users
from models import UserInfo, UserVenue, MapImage
from gheatae import provider

if __name__ == '__main__':
  raw = environ['PATH_INFO']
  assert raw.count('/') == 2, "%d /'s" % raw.count('/')
  foo, bar, rest, = raw.split('/')

  if not constants.provider:
    constants.provider = provider.DBProvider()

  elif rest == 'user':
    user = users.get_current_user()
    if user:
      while(MapImage.all().filter('user =', user).count() > 0):
        mapimages = MapImage.all().filter('user =', user).fetch(500)
        db.delete(mapimages)
      while(UserVenue.all().filter('user = ', user).count() > 0):
        uservenues = UserVenue.all().filter('user = ', user).fetch(500)
        db.delete(uservenues)
      while(UserInfo.all().filter('user =', user).count() > 0):
        userinfos = UserInfo.all().filter('user =', user).fetch(500)
        db.delete(userinfos)

  elif rest == 'mapimage':
    user = users.get_current_user()
    if user:
      while(MapImage.all().filter('user =', user).count() > 0):
        mapimages = MapImage.all().filter('user =', user).fetch(500)
        db.delete(mapimages)
