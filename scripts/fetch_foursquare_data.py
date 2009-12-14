from os import environ
import globalvars
import oauth
from models import UserInfo, UserVenue
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from django.utils import simplejson as json
from datetime import datetime, timedelta
import logging

def fetch_and_store_checkins(userinfo):
  num_added = 0
  logging.warning("userinfo.last_checkin = " + str(userinfo.last_checkin))
  params = {'l':50, 'sinceid':userinfo.last_checkin}

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
          uservenue = UserVenue.all().filter('user =', userinfo.user).filter('venue_id =', j_venue['id']).get()
          if uservenue == None:
            uservenue = UserVenue(location = db.GeoPt(j_venue['geolat'], j_venue['geolong']))
            uservenue.update_location()
            uservenue.user = userinfo.user
            userinfo.venue_count = userinfo.venue_count + 1
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
          uservenue.last_updated = datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000")
          if datetime.now() < uservenue.last_updated + timedelta(hours=12):  continue
          uservenue.checkin_list.append(checkin['id'])
          uservenue.put()
          userinfo.checkin_count = userinfo.checkin_count + 1
          if checkin['id'] > userinfo.last_checkin: userinfo.last_checkin = checkin['id'] # because the checkins are ordered with most recent first!
          userinfo.put()
          num_added = num_added + 1
        else: # there's nothing we can do without a venue id or a lat and a long
          logging.info("Problematic j_venue: " + str(j_venue))
      else:
        logging.info("No venue in checkin: " + str(checkin))
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + response.content)
    raise
  return num_added

def fetch_and_store_checkins_initial(userinfo):
  if globalvars.client == None:
    globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)

  if fetch_and_store_checkins(userinfo) > 0:
    logging.info("checkins added so checkins might be remaining, add self to queue")
    taskqueue.add(url='/fetch_foursquare_data/all_for_user/%s' % userinfo.key())#, queue_name='initial-checkin-fetching')

def fetch_and_store_checkins_for_all():
  userinfos = UserInfo.all().order('-created').fetch(1000)
  for userinfo in userinfos:
    # if userinfo.user in userinfos:
    #   userinfo.delete() # delete extra older tokens for each user
    # else:
    #   user_list.append(userinfo.user)
    fetch_and_store_checkins(userinfo)

def fetch_user_latlong(userinfo):
  response = globalvars.client.make_request("http://api.foursquare.com/v1/user.json", token = userinfo.token, secret = userinfo.secret)
  current_info = json.loads(response.content)
  logging.info(current_info)
  return (current_info['user']['city']['geolat'], current_info['user']['city']['geolong'])

if __name__ == '__main__':
  raw = environ['PATH_INFO']
  assert raw.count('/') == 2 or raw.count('/') == 3, "%d /'s" % raw.count('/')

  if raw.count('/') == 2:
    foo, bar, rest, = raw.split('/')
  elif raw.count('/') == 3:
    foo, bar, rest, userinfo_key = raw.split('/')

  if rest == 'update_everyone':
    fetch_and_store_checkins_for_all()
  elif rest == 'all_for_user':
    logging.warning("userinfo_key " + str(userinfo_key))
    userinfo = db.get(userinfo_key)
    fetch_and_store_checkins_initial(userinfo)