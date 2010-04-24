from os import environ
import constants
import logging
from google.appengine.ext import db
from models import UserVenue
from google.appengine.api import users

user = users.get_current_user()
user_venue = UserVenue.all().filter('user =', user).filter('venue_guid =', '1840858').get()
user_venue.address = 'place du Casino 4'
user_venue.city = 'Morges'
user_venue.state = 'Switzerland'
# user_venue.checkin_guid_list
# user_venue.cross_street
# user_venue.has_parent
# user_venue.is_unique
# user_venue.last_updated
user_venue.location = db.GeoPt('46.5087479', 6.499816)
# user_venue.location_geocells
user_venue.name =  'le Casino'
user_venue.phone = '(021) 802-6215'
# user_venue.user
user_venue.venue_guid = '2917512'
# user_venue.venue_id
user_venue.zipcode = '1110'
user_venue.update_location()
user_venue.put()
logging.error("done! venue updated")