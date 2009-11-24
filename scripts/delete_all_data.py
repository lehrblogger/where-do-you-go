from google.appengine.ext import db
from models import AuthToken, AccessToken, Venue, Checkin, MapImage
from gheatae import provider
provider = provider.DBProvider()

while(AuthToken.all().count() > 0):
  authtokens = AuthToken.all().fetch(1000)
  db.delete(authtokens)

while(AccessToken.all().count() > 0):
  tokens = AccessToken.all().fetch(1000)
  db.delete(tokens)

while(Venue.all().count() > 0):
  venues = Venue.all().fetch(1000)
  db.delete(venues)

while(Checkin.all().count() > 0): #who knows if this will work?
  checkins = provider.get_all_data()
  db.delete(checkins)

while(MapImage.all().count() > 0):
  mapimages = MapImage.all().fetch(1000)
  db.delete(mapimages)