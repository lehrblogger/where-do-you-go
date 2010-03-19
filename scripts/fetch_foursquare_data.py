from os import environ
import constants
import oauth
import foursquare
from models import UserInfo, UserVenue
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError
from google.appengine.runtime import DeadlineExceededError
#from django.utils import simplejson as json
from datetime import datetime, timedelta
import logging


def get_new_fs_for_userinfo(userinfo):
  oauth_token, oauth_secret = constants.get_oauth_strings()
  credentials = foursquare.OAuthCredentials(oauth_token, oauth_secret)
  user_token = oauth.OAuthToken(userinfo.token, userinfo.secret)
  credentials.set_access_token(user_token)
  return foursquare.Foursquare(credentials)

def fetch_and_store_checkins(userinfo, limit=50):
  num_added = 0
  num_ignored = 0
  try:
    fs = get_new_fs_for_userinfo(userinfo)
    history = fs.history(l=limit, sinceid=userinfo.last_checkin)
  except foursquare.FoursquareRemoteException, err:
    logging.warning("Checkins not fetched for %s with error %s" % (userinfo.user, err))
    return 0, 0, 0
  logging.debug(history)
  userinfo.valid_signature = True
  userinfo.is_authorized = True
  try:
    if not 'checkins' in history:
      if 'unauthorized' in history:
        if history['unauthorized'].find('SIGNATURE_INVALID') >= 0:
           userinfo.valid_signature = False
        if history['unauthorized'].find('TOKEN_UNAUTHORIZED') >= 0:
          userinfo.is_authorized = False
        logging.info("User %s is no longer authorized with SIGNATURE_INVALID=%s and TOKEN_UNAUTHORIZED=%s" % userinfo.user,  userinfo.valid_signature, userinfo.is_authorized)
        userinfo.put()
        return 0, 0, 0 
      else:
        logging.error("no value for 'checkins' or 'unauthorized' in history: " + str(history))
        userinfo.put()
        return -1, 0, 0
    elif history['checkins'] == None:
      userinfo.put()
      return 0, 0, 0
    if not userinfo.gender is 'male' and not userinfo.gender is 'female':
      user_data = fs.user()
      if 'gender' in user_data['user']:
        userinfo.gender = user_data['user']['gender']
        if user_data['user']['gender'] is 'male':
          userinfo.photo_url = 'static/blank_boy.png'
        elif user_data['user']['gender'] is 'female':
          userinfo.photo_url = 'static/blank_girl.png'
        userinfo.put()
    for checkin in history['checkins']:
      if 'venue' in checkin:
        j_venue = checkin['venue']
        if 'id' in j_venue and 'geolat' in j_venue and 'geolong' in j_venue:
          uservenue = UserVenue.all().filter('user =', userinfo.user).filter('venue_guid =', str(j_venue['id'])).get()
          if uservenue == None:
            uservenue   = UserVenue.all().filter('user =', userinfo.user).filter('venue_id =', str(j_venue['id'])).get()
          # first we look for guid. if nothing, look as reg id, and convert to guid if we find it, else we need to instantiate it
          if uservenue:
            uservenue.venue_guid = str(uservenue.venue_id)
          else:
            uservenue = UserVenue(location = db.GeoPt(j_venue['geolat'], j_venue['geolong']))
            uservenue.update_location()
            uservenue.user = userinfo.user
            userinfo.venue_count = userinfo.venue_count + 1
            uservenue.venue_guid     = str(j_venue['id'])
            if 'name' in j_venue:
              uservenue.name         = j_venue['name']
            try:
              if 'address' in j_venue:
                uservenue.address    = j_venue['address']
            except BadValueError:
              logging.error("Address not added for venue %s with address json '%s'" % (str(j_venue['id']), j_venue['address']))
            if 'cross_street' in j_venue:
              uservenue.cross_street = j_venue['cross_street']
            if 'state' in j_venue:
              uservenue.state        = j_venue['state']
            if 'zip' in j_venue:
              uservenue.zipcode      = j_venue['zip']
            if 'phone' in j_venue:
              uservenue.phone        = j_venue['phone']
          uservenue.last_updated = datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000") #WARNING last_updated is confusing and should be last_checkin_at
          if datetime.now() < uservenue.last_updated + timedelta(hours=12): #WARNING last_updated is confusing and should be last_checkin_at   
            num_ignored += 1
            continue # ignore recent checkins for the sake of privacy
          if not uservenue.checkin_guid_list or len(uservenue.checkin_guid_list) is 0:
            uservenue.checkin_guid_list = [str(checkin_id) for checkin_id in uservenue.checkin_list]
          uservenue.checkin_guid_list.append(str(checkin['id']))
          userinfo.checkin_count += 1
          userinfo.last_updated = datetime.now()
          if checkin['id'] > userinfo.last_checkin: 
            userinfo.last_checkin = checkin['id'] # because the checkins are ordered with most recent first!
          if userinfo.last_checkin_at is None or datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000") > userinfo.last_checkin_at: 
            userinfo.last_checkin_at = datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000") # because the checkins are ordered with most recent first!
          # def put_updated_uservenue_and_userinfo(uservenue, userinfo, num_added):
          #   uservenue.put()
          #   userinfo.put()
          #   return num_added + 1
          # 
          # num_added = db.run_in_transaction(put_updated_uservenue_and_userinfo, uservenue, userinfo, num_added)
          try:
            uservenue.put()
            userinfo.put()
          except DeadlineExceededError, err:
            logging.warning('start hacky deadline exceeded handling while fetching new checkins!')
            uservenue.put()
            userinfo.put()
            logging.warning('end hacky deadline exceeded handling while fetching new checkins!')
            raise err
          num_added += 1
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + content)
    raise
  return num_added, num_ignored, len(history['checkins'])

def fetch_and_store_checkins_initial(userinfo):
  #logging.info("about to fetch, userinfo.last_checkin = %d" % (userinfo.last_checkin))
  num_added, num_ignored, num_received = fetch_and_store_checkins(userinfo)
  #logging.info("%d checkins added this time, userinfo.last_checkin = %d" % (num_added, userinfo.last_checkin))
  if num_added != 0:
    #logging.info("more than 0 checkins added so there might be checkins remaining. requeue!")
    taskqueue.add(url='/fetch_foursquare_data/all_for_user/%s' % userinfo.key())
  else:
    #logging.info("no more checkins found, we're all set!")
    userinfo.is_ready = True
  userinfo.level_max = int(3 * constants.level_const)
  userinfo.put()

def fetch_and_store_checkins_for_batch():
  userinfos = UserInfo.all().order('last_updated').filter('is_authorized = ', True).fetch(50)
  logging.info("performing batch update for up to %d users-------------------------------" % len(userinfos))
  num_users_completed = 0
  current_userinfo = None
  try:
    for userinfo in userinfos:
      current_userinfo = userinfo
      num_added, num_ignored, num_received = fetch_and_store_checkins(userinfo)
      if not (num_added + num_ignored) == num_received:
        logging.info("updating %d and ignoring %d of %d checkins for %s but they don't match - there are probably shouts or venues without a lat/lon!" % (num_added, num_ignored, num_received, userinfo.user))
      elif num_received > 0:
        logging.info("updating %d and ignoring %d of %d checkins for %s" % (num_added, num_ignored, num_received, userinfo.user))
      userinfo.last_updated = datetime.now() # redundant with the above but oh well
      userinfo.put()
      num_users_completed += 1
  except DeadlineExceededError:
    logging.info("exceeded deadline after %d users, unfinished user was %s" % (num_users_completed, current_userinfo.user))

def update_user_info(userinfo):
  fs = get_new_fs_for_userinfo(userinfo)
  try:
    user_data = fs.user()
  except foursquare.FoursquareRemoteException, err:
    if str(err).find('{"unauthorized":"TOKEN_EXPIRED"}') >= 0:
      userinfo.is_authorized = False
      userinfo.put()
      logging.warning("User %s has unauthorized with error %s" % (userinfo.user, err))
      return
    else:
      raise err
  if 'user' in user_data:
    userinfo.real_name = user_data['user']['firstname']
    if 'gender' in user_data['user']:
      userinfo.gender = user_data['user']['gender']
    if 'photo' in user_data['user'] and not user_data['user']['photo'] == '' :
      userinfo.photo_url = user_data['user']['photo']
    elif 'gender' in user_data['user'] and user_data['user']['gender'] is 'male':
      userinfo.photo_url = 'static/blank_boy.png'
    elif 'gender' in user_data['user'] and user_data['user']['gender'] is 'female':
      userinfo.photo_url = 'static/blank_girl.png'
    else:
      userinfo.photo_url = constants.default_photo
    if 'checkin' in user_data['user'] and 'venue' in user_data['user']['checkin']:
      userinfo.citylat = user_data['user']['checkin']['venue']['geolat']
      userinfo.citylng = user_data['user']['checkin']['venue']['geolong']
    else:
      userinfo.citylat = constants.default_lat
      userinfo.citylng = constants.default_lng
    userinfo.put()
  else:
    logging.error('no "user" key in json: %s' % user)

if __name__ == '__main__':
  raw = environ['PATH_INFO']
  assert raw.count('/') == 2 or raw.count('/') == 3, "%d /'s" % raw.count('/')

  if raw.count('/') == 2:
    foo, bar, rest, = raw.split('/')
  elif raw.count('/') == 3:
    foo, bar, rest, userinfo_key = raw.split('/')

  if rest == 'update_users_batch':
    fetch_and_store_checkins_for_batch()
  elif rest == 'all_for_user':
    userinfo = db.get(userinfo_key)
    fetch_and_store_checkins_initial(userinfo)