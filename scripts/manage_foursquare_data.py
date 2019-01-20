from os import environ
import constants
import logging
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError
from google.appengine.api.datastore_errors import BadRequestError
from google.appengine.runtime import DeadlineExceededError
from datetime import datetime, timedelta
from time import mktime
from models import UserInfo, UserVenue

def purge_user_data():
  num_cleared = 0
  userinfos = UserInfo.all().filter('last_updated < ', datetime(2019, 1, 20, 7, 20, 0, 0)).fetch(2000)
  try:
    for userinfo in userinfos:
      while True:
        uservenues = UserVenue.all(keys_only=True).filter('user =', userinfo.user).fetch(1000)
        if not uservenues: break
        db.delete(uservenues)
        num_cleared = num_cleared + len(uservenues)
      if hasattr(userinfo, 'is_ready'): delattr(userinfo, 'is_ready')
      if hasattr(userinfo, 'has_been_cleared'): delattr(userinfo, 'has_been_cleared')
      if hasattr(userinfo, 'has_been_purged'): delattr(userinfo, 'has_been_purged')
      if hasattr(userinfo, 'color_scheme'): delattr(userinfo, 'color_scheme')
      if hasattr(userinfo, 'level_max'): delattr(userinfo, 'level_max')
      if hasattr(userinfo, 'gender'): delattr(userinfo, 'gender')
      if hasattr(userinfo, 'checkin_count'): delattr(userinfo, 'checkin_count')
      if hasattr(userinfo, 'venue_count'): delattr(userinfo, 'venue_count')
      if hasattr(userinfo, 'citylat'): delattr(userinfo, 'citylat')
      if hasattr(userinfo, 'citylng'): delattr(userinfo, 'citylng')
      if hasattr(userinfo, 'is_authorized'): delattr(userinfo, 'is_authorized')
      if hasattr(userinfo, 'token'): delattr(userinfo, 'token')
      if hasattr(userinfo, 'secret'): delattr(userinfo, 'secret')
      userinfo.last_updated = datetime.now()
      userinfo.put()
    logging.info("finished after deleting at least %d UserVenues for %d UserInfos" % (num_cleared, len(userinfos)))
  except DeadlineExceededError:
    logging.info("exceeded deadline after deleting at least %d UserVenues for %d UserInfos" % (num_cleared, len(userinfos)))

if __name__ == '__main__':
  raw = environ['PATH_INFO']
  assert raw.count('/') == 2 or raw.count('/') == 3, "%d /'s" % raw.count('/')

  if raw.count('/') == 2:
    foo, bar, rest, = raw.split('/')
  elif raw.count('/') == 3:
    foo, bar, rest, userinfo_key = raw.split('/')

  if rest == 'purge_user_data':
    purge_user_data()
