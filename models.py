from google.appengine.ext import db
from geo.geomodel import GeoModel
import constants
from datetime import datetime

class LastOffset(db.Model):
  offset = db.IntegerProperty(default=0)

class UserInfo(db.Model):  
  user = db.UserProperty()
  created = db.DateTimeProperty(auto_now_add=True) # unused to save index space, but keep anyway
  last_updated = db.DateTimeProperty(auto_now_add=True)
  is_ready = db.BooleanProperty() # if this has a default value of Fale, setting it seems to sometimes not work...
  has_been_cleared = db.BooleanProperty(default=False)
  color_scheme = db.StringProperty(default='fire')
  level_max = db.IntegerProperty(default=int(140.)) #TODO see note in constants.py, was =int(constants.level_const))
  checkin_count = db.IntegerProperty(default=0)
  venue_count = db.IntegerProperty(default=0)
  gender = db.StringProperty()
  photo_url = db.StringProperty()
  real_name = db.StringProperty()
  citylat = db.FloatProperty() # no longer really cities! just where the user was scene at the time of signup
  citylng = db.FloatProperty()
  is_authorized = db.BooleanProperty(default=False)
  token = db.StringProperty()
  secret = db.StringProperty()

  def __str__(self):
    return 'UserInfo:  | user =' + str(self.user) + ' | key =' + str(self.key()) + ' | is_ready =' + str(self.is_ready) + ' | color_scheme = ' + str(self.color_scheme) + ' | level_max =' + str(self.level_max) + ' | checkin_count =' + str(self.checkin_count) + ' | venue_count =' + str(self.venue_count) + ' | photo_url =' + str(self.photo_url) + ' | real_name =' + str(self.real_name) + ' | citylat =' + str(self.citylat) + ' | citylng =' + str(self.citylng) + ' | created =' + str(self.created)

class UserVenue(GeoModel):
  user = db.UserProperty()
  last_checkin_at = db.DateTimeProperty()
  checkin_guid_list = db.ListProperty(str, default=[])
  venue_guid = db.StringProperty()
  
class MapImage(db.Model):
  last_updated = db.DateTimeProperty(auto_now_add=True)
  user = db.UserProperty()
  tiles_remaining = db.IntegerProperty(default=0)
  centerlat = db.FloatProperty()
  centerlng = db.FloatProperty()
  northlat = db.FloatProperty()
  westlng = db.FloatProperty()
  zoom = db.IntegerProperty()
  width = db.IntegerProperty()
  height = db.IntegerProperty()
  img = db.BlobProperty()
  static_url = db.StringProperty()
  update_count = db.IntegerProperty(default=0)

