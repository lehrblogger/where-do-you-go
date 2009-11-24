from google.appengine.ext import db
from geo.geomodel import GeoModel

class AuthToken(db.Model):
  service = db.StringProperty(required=True)
  token = db.StringProperty(required=True)
  secret = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)

class AccessToken(db.Model):
  owner = db.UserProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  token = db.StringProperty()
  secret = db.StringProperty()

class Venue(db.Model):
  venue_id = db.IntegerProperty()
  name = db.StringProperty()
  address = db.StringProperty()
  crossstreet = db.StringProperty()
  city = db.StringProperty()
  state = db.StringProperty()
  zipcode = db.StringProperty()
  geolat = db.FloatProperty()
  geolong = db.FloatProperty()
  phone = db.PhoneNumberProperty()

class Checkin(GeoModel):
  user = db.UserProperty()
  checkin_id = db.IntegerProperty()
  created = db.DateTimeProperty()
  venue =  db.ReferenceProperty(Venue)
  weight = db.IntegerProperty()
  range = db.IntegerProperty()

class MapImage(db.Model):
  user = db.UserProperty()
  centerlat = db.FloatProperty()
  centerlong = db.FloatProperty()
  zoomlevel = db.IntegerProperty()
  width = db.IntegerProperty()
  height = db.IntegerProperty()
  img = db.BlobProperty()

