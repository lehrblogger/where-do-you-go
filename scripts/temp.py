from os import environ
import constants
import foursquarev2
import logging
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError
from google.appengine.api.datastore_errors import BadRequestError
from google.appengine.runtime import DeadlineExceededError
from datetime import datetime, timedelta
from time import mktime
from models import UserInfo, UserVenue
    
def deleteAttribute(obj, attr):
  try:
    delattr(obj, attr)  
  except AttributeError, err:
    logging.info('%s deletion failed with %s' % (attr, str(err)))

if __name__ == '__main__':
  num_cleared = 0
  num_updated = 0
  userinfos = UserInfo.all().filter('venue_count <', 0).fetch(2000)
  try:
    for userinfo in userinfos:
      userinfo.venue_count = 0
      userinfo.last_updated = datetime.now()
      userinfo.put()
      num_updated += 1
    logging.info("finished after deleting at least %d UserVenues for %d UserInfos" % (num_cleared, num_updated))
  except DeadlineExceededError:
    logging.info("exceeded deadline after deleting at least %d UserVenues" % (num_cleared))