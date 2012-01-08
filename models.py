from google.appengine.ext import db
from geo.geomodel import GeoModel
import constants
from datetime import datetime

class LastOffset(db.Model):
  offset = db.IntegerProperty(default=0)

# class AuthToken(db.Model):
#   service = db.StringProperty(required=True)
#   token = db.StringProperty(required=True)
#   secret = db.StringProperty(required=True)
#   created = db.DateTimeProperty(auto_now_add=True)

# class AppToken(db.Model):
#   token = db.StringProperty(required=True)
#   secret = db.StringProperty(required=True)
#   created = db.DateTimeProperty(auto_now_add=True)

class UserInfo(db.Model):
  last_updated = db.DateTimeProperty()
  user = db.UserProperty()
  is_ready = db.BooleanProperty()
  is_authorized = db.BooleanProperty()
  valid_signature = db.BooleanProperty()
  last_checkin_str = db.StringProperty() #TODO delete this
  last_checkin_at = db.DateTimeProperty(datetime.strptime('1970', "%Y"))
  color_scheme = db.StringProperty(default='fire')
  level_max = db.IntegerProperty(default=int(140.)) #TODO see note in constants.py, was =int(constants.level_const))
  checkin_count = db.IntegerProperty(default=0)
  venue_count = db.IntegerProperty(default=0)
  gender = db.StringProperty()
  photo_url = db.StringProperty()
  real_name = db.StringProperty()
  citylat = db.FloatProperty() #no longer really cities! just where the user was scene at the time of signup
  citylng = db.FloatProperty()
  token = db.StringProperty()
  secret = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)

  def __str__(self):
    return 'UserInfo:  last_updated = ' + str(self.last_updated) + ' | user =' + str(self.user) #+ ' | is_ready =' + str(self.is_ready) + ' | last_checkin_str = ' + self.last_checkin_str + ' | last_checkin = ' + str(self.last_checkin) + ' | color_scheme = ' + str(self.color_scheme) + ' | level_max =' + str(self.level_max) + ' | checkin_count =' + str(self.checkin_count) + ' | venue_count =' + str(self.venue_count) + ' | photo_url =' + str(self.photo_url) + ' | real_name =' + str(self.real_name) + ' | citylat =' + str(self.citylat) + ' | citylng =' + str(self.citylng) + ' | created =' + str(self.created)

class UserVenue(GeoModel):
  user = db.UserProperty()
  last_checkin_at = db.DateTimeProperty()
  checkin_guid_list = db.ListProperty(str, default=[])
  venue_guid = db.StringProperty()
  
class MapImage(db.Model):
  last_updated = db.DateTimeProperty(auto_now_add=True)
  user = db.UserProperty()
  centerlat = db.FloatProperty()
  centerlng = db.FloatProperty()
  northlat = db.FloatProperty()
  westlng = db.FloatProperty()
  zoom = db.IntegerProperty()
  width = db.IntegerProperty()
  height = db.IntegerProperty()
  input_imgs = db.ListProperty(db.Blob, default=[])
  img = db.BlobProperty()
  static_url = db.StringProperty()
  update_count = db.IntegerProperty(default=0)

