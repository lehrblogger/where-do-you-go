import logging
from google.appengine.ext import db
from models import UserVenue, LastOffset

COUNT = 200

last_offset = LastOffset().all().get()
uservenues = UserVenue.all().order('venue_id').fetch(COUNT, offset=last_offset.offset)
logging.debug("Updating %d UserVenues starting with %d" % (COUNT, last_offset.offset))
logging.debug(uservenues)
for uservenue in uservenues:
  uservenue.ids_converted = False
  uservenue.put()
last_offset.offset += COUNT
last_offset.put()

# filter('venue_id >=', 0).filter('ids_converted !=', True).fetch(1)
# # if we filter greater 
# logging.debug(uservenues)
# for uservenue in uservenues:
#   uservenue.venue_id = str(uservenue.venue_id)
#   uservenue.checkin_list = [str(e) for e in uservenue.checkin_list]
#   uservenue.ids_converted = True
#   uservenue.put()
#   