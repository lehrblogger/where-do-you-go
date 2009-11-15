import oauth
from models import Token, Venue, Checkin
from google.appengine.ext import db
from django.utils import simplejson as json
import datetime
import logging

def fetch_and_store_n_recent_checkins_for_token(token, limit, client):
  response = client.make_request("http://api.foursquare.com/v1/history.json", token = token.token, secret = token.secret, additional_params = {'l':limit})
  #ad7zy4hiv4yi temp random password
  try:
    history = json.loads(response.content)
    logging.debug(history)
    for checkin in history['checkins']:
      if 'venue' in checkin:
        if Venue.all().filter('venue_id =', checkin['venue']['id']).count() == 0:
          # if we don't have the venue yet, add it
          venue = Venue()
          venue.venue_id    = checkin['venue']['id']
          venue.name        = checkin['venue']['name']
          venue.address     = checkin['venue']['address']
          venue.crossstreet = checkin['venue']['crossstreet']
          venue.city        = checkin['venue']['city']
          venue.state       = checkin['venue']['state']
          venue.zipcode     = checkin['venue']['zip']
          venue.geolat      = checkin['venue']['geolat']
          venue.geolong     = checkin['venue']['geolong']
          venue.phone       = checkin['venue']['phone']
          venue.put()
        else:
          # otherwise grab it
          venue = Venue.all().filter('venue_id =', checkin['venue']['id']).get()

        if Checkin.all().filter('checkin_id =', checkin['id']).count() == 0:
          # if it's a new checkin, put it in the database
          new_checkin = Checkin()
          new_checkin.user       = token.owner
          new_checkin.checkin_id = checkin['id']
          new_checkin.created    = datetime.datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000")
          new_checkin.venue      = venue
          logging.debug(new_checkin)
          new_checkin.put()
        # else
          #it's already there and we're good
  except:
    logging.error("There was a problem with the response: " % response)


consumer_key = "98ff47ad5541ebaaee51cb5a1e843d1404aeba03f"
consumer_secret = "f661bcab0416f66a2c6633cde08aefd5"
callback_url = " http://where-do-you-go.appspot.com/callback/foursquare"

client = oauth.FoursquareClient(consumer_key, consumer_secret, callback_url)

all_tokens = Token.all().order('-created').fetch(1000)
user_list = []
for token in all_tokens:
  if token.owner in user_list:
    token.delete()
  else:
    user_list.append(token.owner)
    fetch_and_store_n_recent_checkins_for_token(token, 20, client)


