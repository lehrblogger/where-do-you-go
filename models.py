from google.appengine.ext import db
from geo.geomodel import GeoModel
import constants

class AuthToken(db.Model):
  service = db.StringProperty(required=True)
  token = db.StringProperty(required=True)
  secret = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)

class UserInfo(db.Model):
  user = db.UserProperty()
  last_checkin = db.IntegerProperty(default=0)
  color_scheme = db.StringProperty(default='fire')
  level_max = db.IntegerProperty(default=int(constants.level_const))
  checkin_count = db.IntegerProperty(default=0)
  venue_count = db.IntegerProperty(default=0)
  photo_url = db.StringProperty()
  real_name = db.StringProperty()
  citylat = db.FloatProperty()
  citylng = db.FloatProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  token = db.StringProperty()
  secret = db.StringProperty()

class UserVenue(GeoModel):
  user = db.UserProperty()
  checkin_list = db.ListProperty(int, default=[])
  last_updated = db.DateTimeProperty(auto_now_add=True)
  venue_id = db.IntegerProperty()
  name = db.StringProperty()
  address = db.StringProperty()
  cross_street = db.StringProperty()
  city = db.StringProperty()
  state = db.StringProperty()
  zipcode = db.StringProperty()
  phone = db.PhoneNumberProperty()

class MapImage(db.Model):
  user = db.UserProperty()
  centerlat = db.FloatProperty()
  centerlng = db.FloatProperty()
  northlat = db.FloatProperty()
  westlng = db.FloatProperty()
  zoom = db.IntegerProperty()
  width = db.IntegerProperty()
  height = db.IntegerProperty()
  img = db.BlobProperty()

