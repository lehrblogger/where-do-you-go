from google.appengine.ext import db

class User(User):
	foursquare_id = db.IntegerProperty()

class Checkin(db.Model):
  user = db.UserProperty()
  venue =  db.ReferenceProperty(Venue)
  
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