import logging
from google.appengine.ext import db
from models import UserVenue
from google.appengine.runtime import DeadlineExceededError

total_deleted = 0
try:
  child_uservenues = UserVenue.all().filter('has_parent = ', True).filter('is_unique = ', False).fetch(500)
  for child_uservenue in child_uservenues:
    orphan_uservenues = UserVenue.all().filter('venue_guid =', child_uservenue.venue_guid).fetch(500)
    for orphan_uservenue in orphan_uservenues:
      if not orphan_uservenue.has_parent or orphan_uservenue.has_parent == False:
        orphan_uservenue.delete()
        total_deleted += 1
    child_uservenue.is_unique = True
    child_uservenue.put()
  logging.info("deleted a total of %d orphaned uservenues" % total_deleted)
except DeadlineExceededError:
  logging.info("deleted a total of %d orphaned uservenues (DeadlineExceededError, but it's fine)" % total_deleted)