import globalvars
import oauth
from models import UserInfo, UserVenue
from google.appengine.ext import db
from django.utils import simplejson as json
import datetime
import logging

def fetch_and_store_checkins(user):
  userinfo = UserInfo.all().filter('user =', user).get()
  if userinfo.last_checkin:
    logging.warning("userinfo.last_checkin = " + str(userinfo.last_checkin))
    params = {'l':250, 'sinceid':userinfo.last_checkin}
  else:
    params = {'l':250}
  response = globalvars.client.make_request("http://api.foursquare.com/v1/history.json",
                                            token = userinfo.token,
                                            secret = userinfo.secret,
                                            additional_params = params)
  try:
    history = json.loads(response.content)
    for checkin in history['checkins']:
      if 'venue' in checkin:
        j_venue = checkin['venue']
        if 'id' in j_venue and 'geolat' in j_venue and 'geolong' in j_venue:
          uservenue = UserVenue.all().filter('user =', user).filter('venue_id =', j_venue['id']).get()
          if uservenue == None:
            uservenue = UserVenue(location = db.GeoPt(j_venue['geolat'], j_venue['geolong']))
            uservenue.update_location()
            uservenue.user = user
            uservenue.venue_id       = int(j_venue['id'])
            if 'name' in j_venue:
              uservenue.name         = j_venue['name']
            if 'address' in j_venue:
              uservenue.address      = j_venue['address']
            if 'cross_street' in j_venue:
              uservenue.cross_street = j_venue['cross_street']
            if 'city' in j_venue:
              uservenue.city         = j_venue['city']
            if 'state' in j_venue:
              uservenue.state        = j_venue['state']
            if 'zip' in j_venue:
              uservenue.zipcode      = j_venue['zip']
            if 'phone' in j_venue:
              uservenue.phone        = j_venue['phone']
          uservenue.last_updated = datetime.datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000")
          uservenue.checkin_list.append(checkin['id'])
          uservenue.put()
          userinfo.last_checkin = checkin['id']
          userinfo.put()
        else: # there's nothing we can do without a venue id or a lat and a long
          logging.info("Problematic j_venue: " + str(j_venue))
      else:
        logging.info("No venue in checkin: " + str(checkin))
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + response.content)
    raise

def fetch_and_store_checkins_for_all():
    userinfos = UserInfo.all().order('-created').fetch(1000)
    for userinfo in userinfos:
      # if userinfo.user in userinfos:
      #   userinfo.delete() # delete extra older tokens for each user
      # else:
      #   user_list.append(userinfo.user)
      fetch_and_store_checkins(userinfo.user)

def fetch_user_latlong(userinfo):
  response = globalvars.client.make_request("http://api.foursquare.com/v1/user.json", token = userinfo.token, secret = userinfo.secret)
  current_info = json.loads(response.content)
  logging.info(current_info)
  return (current_info['user']['city']['geolat'], current_info['user']['city']['geolong'])

if __name__ == '__main__':
  if globalvars.client == None:
    globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)

  fetch_and_store_checkins_for_all()
