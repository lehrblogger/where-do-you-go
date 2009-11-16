from geo.geomodel import GeoModel
from google.appengine.ext import db

class DataPoint(GeoModel):
  time = db.DateTimeProperty()
  weight = db.IntegerProperty()
  range = db.IntegerProperty()

#TODO add user stuff here so we dont display everyone's poitns on the map, or integrate into Checkins