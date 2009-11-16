import oauth
from models import Token, Venue, Checkin
from google.appengine.ext import db
from django.utils import simplejson as json
import datetime
import logging
from gheatae import color_scheme, dot, tile, cache, provider
from gheatae.point import DataPoint
from gheatae.tile import Tile
import handler
import time

def fetch_and_store_n_recent_checkins_for_token(token, limit, client):
  response = client.make_request("http://api.foursquare.com/v1/history.json", token = token.token, secret = token.secret, additional_params = {'l':limit})
  #ad7zy4hiv4yi temp random password
  # try:
  history = json.loads(response.content)
  for checkin in history['checkins']:
    if 'venue' in checkin:
      json_venue = checkin['venue']
      if 'id' in json_venue and Venue.all().filter('venue_id =', json_venue['id']).count() == 0:
        # if we don't have the venue yet, add it
        venue = Venue()
        venue.venue_id    = checkin['venue']['id']

        if 'name' in json_venue:
          venue.name        = json_venue['name']
        if 'address' in json_venue:
          venue.address     = json_venue['address']
        if 'crossstreet' in json_venue:
          venue.crossstreet = json_venue['crossstreet']
        if 'city' in json_venue:
          venue.city        = json_venue['city']
        if 'state' in json_venue:
          venue.state       = json_venue['state']
        if 'zip' in json_venue:
          venue.zipcode     = int(json_venue['zip'])
        if 'geolat' in json_venue:
          venue.geolat      = json_venue['geolat']
        if 'geolong' in json_venue:
          venue.geolong     = json_venue['geolong']
        if 'phone' in json_venue:
          venue.phone       = json_venue['phone']
        venue.put()
      else:
        # otherwise grab it
        venue = Venue.all().filter('venue_id =', json_venue['id']).get()

      if Checkin.all().filter('checkin_id =', checkin['id']).count() == 0:
        # if it's a new checkin, put it in the database
        new_checkin = Checkin()
        new_checkin.user       = token.owner
        new_checkin.checkin_id = checkin['id']
        new_checkin.created    = datetime.datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000")
        new_checkin.venue      = venue
        logging.debug(new_checkin)
        new_checkin.put()

        new_data = DataPoint(location=db.GeoPt(venue.geolat, venue.geolong), time=new_checkin.created, weight=3, range=3)
        new_data.update_location()
        new_data.put()

      # else
        #it's already there and we're good
  # except:
  #   logging.error("There was a problem with the response: " + response.content)


consumer_key = "98ff47ad5541ebaaee51cb5a1e843d1404aeba03f"
consumer_secret = "f661bcab0416f66a2c6633cde08aefd5"
callback_url = " http://where-do-you-go.appspot.com/callback/foursquare"

client = oauth.FoursquareClient(consumer_key, consumer_secret, callback_url)

all_tokens = Token.all().order('-created').fetch(1000)
user_list = []
for token in all_tokens:
  if token.owner in user_list:
    token.delete() # delete extra older tokens for each user
  else:
    user_list.append(token.owner)
    fetch_and_store_n_recent_checkins_for_token(token, 20, client)


