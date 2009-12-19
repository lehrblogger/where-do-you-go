from os import environ
import constants
import oauth
from models import UserInfo, UserVenue
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from django.utils import simplejson as json
from datetime import datetime, timedelta
import logging

def fetch_and_store_checkins(userinfo, limit=50):
  num_added = 0
  params = {'l':limit, 'sinceid':userinfo.last_checkin}
  response = constants.client.make_request("http://api.foursquare.com/v1/history.json",
                                            token = userinfo.token,
                                            secret = userinfo.secret,
                                            additional_params = params)
  try:
    history = json.loads(response.content)
    if not 'checkins' in history:
      logging.warning("no value for 'checkins' in history: " + str(history))
      return -1
    if history['checkins'] == None:
      logging.warning("history['checkins'] is None: " + str(history))
      return 0
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
          uservenue.last_updated = datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000") #WARNING last_updated is confusing and should be last_checkin_at
          if datetime.now() < uservenue.last_updated + timedelta(hours=12):  continue #WARNING last_updated is confusing and should be last_checkin_at
          uservenue.checkin_list.append(checkin['id'])
          uservenue.put()
          userinfo.checkin_count = userinfo.checkin_count + 1
          if checkin['id'] > userinfo.last_checkin: userinfo.last_checkin = checkin['id'] # because the checkins are ordered with most recent first!
          userinfo.put()
          num_added = num_added + 1
      #   else: # there's nothing we can do without a venue id or a lat and a lng
      #     logging.info("Problematic j_venue: " + str(j_venue))
      # else:
      #   logging.info("No venue in checkin: " + str(checkin))
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + response.content)
    raise
  return num_added

def fetch_and_store_checkins_initial(userinfo):
  if constants.client == None:
    oauth_strings = constants.get_oauth_strings()
    constants.client = oauth.FoursquareClient(oauth_strings[0], oauth_strings[1], oauth_strings[2])
  logging.info("about to fetch, userinfo.last_checkin = %d" % (userinfo.last_checkin))
  num_added = fetch_and_store_checkins(userinfo)
  logging.info("%d checkins added this time, userinfo.last_checkin = %d" % (num_added, userinfo.last_checkin))
  if num_added != 0:
    logging.info("more than 0 checkins added so there might be checkins remaining. requeue!")
    taskqueue.add(url='/fetch_foursquare_data/all_for_user/%s' % userinfo.key())
  else:
    logging.info("no more checkins found, we're all set!")
    userinfo.is_ready = True
  userinfo.level_max = int(3 * constants.level_const)
  userinfo.put()

def fetch_and_store_checkins_for_all():
  userinfos = UserInfo.all().order('-last_updated').fetch(1000)
  for userinfo in userinfos:
    fetch_and_store_checkins(userinfo)

def update_user_info(userinfo):
  response = constants.client.make_request("http://api.foursquare.com/v1/user.json", token = userinfo.token, secret = userinfo.secret)
  current_info = json.loads(response.content)
  if 'user' in current_info:
    userinfo.real_name = current_info['user']['firstname']
    if 'photo' in current_info['user'] and not current_info['user']['photo'] == '' :
      userinfo.photo_url = current_info['user']['photo']
    else:
      userinfo.photo_url = constants.default_photo
    if 'city' in current_info['user']:
      userinfo.citylat = current_info['user']['city']['geolat']
      userinfo.citylng = current_info['user']['city']['geolong']
    else:
      userinfo.citylat = constants.default_lat
      userinfo.citylng = constants.default_lng
    userinfo.put()
  else:
    logging.error('user object not updated!')

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
    userinfo = db.get(userinfo_key)
    fetch_and_store_checkins_initial(userinfo)