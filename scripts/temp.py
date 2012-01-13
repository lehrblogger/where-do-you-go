from os import environ
import constants
import oauth
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
  userinfos = UserInfo.all().filter('venue_count >=', 0).fetch(1000)
  try:
    for userinfo in userinfos:
      while True:
        uservenues = UserVenue.all(keys_only=True).filter('user =', userinfo.user).fetch(1000)
        #logging.info("you haz %d UserVenues for %s" % (len(uservenues), userinfo.user))
        if not uservenues: break
        db.delete(uservenues)
        num_cleared = num_cleared + len(uservenues)
      deleteAttribute(userinfo, 'last_checkin')  
      deleteAttribute(userinfo, 'last_checkin_at')
      deleteAttribute(userinfo, 'last_checkin_str')  
      deleteAttribute(userinfo, 'valid_signature')
      userinfo.has_been_cleared = True
      userinfo.checkin_count = 0
      userinfo.venue_count = -1 # just to keep track of which I've deleted
      userinfo.last_updated = datetime.now()
      userinfo.put()
      num_updated += 1
    logging.info("finished after deleting at least %d UserVenues for %d UserInfos" % (num_cleared, num_updated))
  except DeadlineExceededError:
    logging.info("exceeded deadline after deleting at least %d UserVenues" % (num_cleared))