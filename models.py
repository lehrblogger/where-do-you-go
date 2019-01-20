from google.appengine.ext import db
from geo.geomodel import GeoModel
import constants
from datetime import datetime

class UserInfo(db.Model):
  user = db.UserProperty()
  created = db.DateTimeProperty(auto_now_add=True) # unused to save index space, but keep anyway
  last_updated = db.DateTimeProperty(auto_now_add=True)
  photo_url = db.StringProperty()
  real_name = db.StringProperty()

  def __str__(self):
    return 'UserInfo:  | user =' + str(self.user) + ' | key =' + str(self.key()) + ' | created =' + str(self.created)

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

