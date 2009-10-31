from google.appengine.ext import db

class FoursquareToken(db.Model):
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
  zipcode = db.IntegerProperty()
  geolat = db.StringProperty()
  geolong = db.StringProperty()
  phone = db.PhoneNumberProperty()

class Checkin(db.Model):
  user = db.UserProperty()
  datetime = db.DateTimeProperty()
  venue =  db.ReferenceProperty(Venue)