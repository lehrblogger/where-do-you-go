import globalvars
import oauth
from models import AccessToken, Venue, Checkin
from google.appengine.ext import db
from django.utils import simplejson as json
import datetime
import logging

def fetch_and_store_n_recent_checkins_for_token(token, limit):
  response = globalvars.client.make_request("http://api.foursquare.com/v1/history.json", token = token.token, secret = token.secret, additional_params = {'l':limit})
  #ad7zy4hiv4yi temp random password
  try:
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
            venue.zipcode     = json_venue['zip']
          if 'geolat' in json_venue:
            venue.geolat      = json_venue['geolat']
          if 'geolong' in json_venue:
            venue.geolong     = json_venue['geolong']
          if 'phone' in json_venue:
            venue.phone       = json_venue['phone']

          if venue.geolong == None or venue.geolat == None:
            continue # nothing to be done without a latlon
          else:
            venue.put()
        elif 'id' in json_venue:
          # otherwise grab it
          venue = Venue.all().filter('venue_id =', json_venue['id']).get()
        else:
          # there's nothing we can do without a venue id...
          logging.info("Problematic json_venue: " + str(json_venue))

        if Checkin.all().filter('checkin_id =', checkin['id']).count() == 0:
          # if it's a new checkin, put it in the database
          new_checkin = Checkin(location = db.GeoPt(venue.geolat, venue.geolong))
          new_checkin.user       = token.owner
          new_checkin.checkin_id = checkin['id']
          new_checkin.created    = datetime.datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000")
          new_checkin.venue      = venue
          new_checkin.weight     = 3
          new_checkin.range      = 3
          new_checkin.update_location()
          new_checkin.put()
        # else
          #it's already there and we're good
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + response.content)
    raise

def fetch_and_store_all_recent_checkins():
    all_tokens = AccessToken.all().order('-created').fetch(1000)
    user_list = []
    for token in all_tokens:
      if token.owner in user_list:
        token.delete() # delete extra older tokens for each user
      else:
        user_list.append(token.owner)
        fetch_and_store_n_recent_checkins_for_token(token, 20)

def fetch_user_latlong(user, retreived_token):
  response = globalvars.client.make_request("http://api.foursquare.com/v1/user.json", token = retreived_token.token, secret = retreived_token.secret)
  user_info = json.loads(response.content)
  return (user_info['user']['city']['geolat'], user_info['user']['city']['geolong'])

if __name__ == '__main__':
  if globalvars.client == None:
    globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)

  fetch_and_store_all_recent_checkins()
