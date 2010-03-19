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
  userinfo.valid_signature = True
  userinfo.is_authorized = True
  try:
    fs = get_new_fs_for_userinfo(userinfo)
    history = fs.history(l=limit, sinceid=userinfo.last_checkin)
  except foursquare.FoursquareRemoteException, err:
    if str(err).find('SIGNATURE_INVALID') >= 0:
      userinfo.valid_signature = False
      logging.info("User %s is no longer authorized with SIGNATURE_INVALID" % userinfo.user)
      userinfo.put()
    elif str(err).find('TOKEN_UNAUTHORIZED') >= 0:
      userinfo.is_authorized = False
      logging.info("User %s is no longer authorized with TOKEN_UNAUTHORIZED" % userinfo.userd)
      userinfo.put()
    else:
      logging.warning("Checkins not fetched for %s with error %s" % (userinfo.user, err))
      return 0, 0, 0
  logging.debug(history)
  try:
    if not 'checkins' in history:
      logging.error("no value for 'checkins' in history: " + str(history))
      userinfo.put()
      return -1, 0, 0
    elif history['checkins'] == None:
      userinfo.put()
      return 0, 0, 0
    if not userinfo.gender is 'male' and not userinfo.gender is 'female':
      try:
        user_data = fs.user()
        if 'gender' in user_data['user']:
          userinfo.gender = user_data['user']['gender']
          if user_data['user']['gender'] is 'male':
            userinfo.photo_url = 'static/blank_boy.png'
          elif user_data['user']['gender'] is 'female':
            userinfo.photo_url = 'static/blank_girl.png'
          userinfo.put()
      except DownloadError:
        logging.warning("Checkins not fetched for %s with error %s" % (userinfo.user, err))
        return 0, 0, 0
    for checkin in history['checkins']:
      if 'venue' in checkin:
        j_venue = checkin['venue']
        if 'id' in j_venue and 'geolat' in j_venue and 'geolong' in j_venue:
          
          def uservenue_factory(userinfo_param, j_venue_param, checkin_guid_list_param, checkin_list_param, is_unique_param):
            new_uservenue = UserVenue(parent=userinfo_param, location = db.GeoPt(j_venue_param['geolat'], j_venue_param['geolong']))
            new_uservenue.update_location()
            new_uservenue.user = userinfo_param.user
            new_uservenue.venue_guid     = str(j_venue_param['id'])
            if 'name' in j_venue_param:
              new_uservenue.name         = j_venue_param['name']
            if 'address' in j_venue_param:
              new_uservenue.address      = j_venue_param['address']
            if 'cross_street' in j_venue_param:
              new_uservenue.cross_street = j_venue_param['cross_street']
            if 'state' in j_venue_param:
              new_uservenue.state        = j_venue_param['state']
            if 'zip' in j_venue_param:
              new_uservenue.zipcode      = j_venue_param['zip']
            if 'phone' in j_venue_param:
              new_uservenue.phone        = j_venue_param['phone']
            new_uservenue.has_parent = True
            new_uservenue.is_unique = is_unique_param 
            new_uservenue.checkin_list = checkin_list_param
            new_uservenue.checkin_guid_list = checkin_guid_list_param
            if not new_uservenue.checkin_guid_list or len(new_uservenue.checkin_guid_list) is 0:
              new_uservenue.checkin_guid_list = [str(checkin_id) for checkin_id in new_uservenue.checkin_list]
            return new_uservenue
            
          uservenue = UserVenue.all().filter('user =', userinfo.user).filter('venue_guid =', str(j_venue['id'])).filter('has_parent = ', True).get()
          if uservenue: 
            if not uservenue.checkin_guid_list or len(uservenue.checkin_guid_list) is 0:
              uservenue.checkin_guid_list = [str(checkin_id) for checkin_id in uservenue.checkin_list]
          else:
            uservenue = UserVenue.all().filter('user =', userinfo.user).filter('venue_guid =', str(j_venue['id'])).get()
            if uservenue:
              uservenue = uservenue_factory(userinfo, j_venue, uservenue.checkin_guid_list, uservenue.checkin_list, False)
            else:
              uservenue = UserVenue.all().filter('user =', userinfo.user).filter('venue_id =', j_venue['id']).get()
              if uservenue:
                uservenue = uservenue_factory(userinfo, j_venue, uservenue.checkin_guid_list, uservenue.checkin_list, False)  
              else:
                userinfo.venue_count = userinfo.venue_count + 1
                uservenue = uservenue_factory(userinfo, j_venue, [], [], True)
          uservenue.last_updated = datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000") #WARNING last_updated is confusing and should be last_checkin_at
          if datetime.now() < uservenue.last_updated + timedelta(hours=12):                             #WARNING last_updated is confusing and should be last_checkin_at   
            num_ignored += 1
            continue
          uservenue.checkin_guid_list.append(str(checkin['id']))
          userinfo.checkin_count += 1
          userinfo.last_updated = datetime.now()
          if checkin['id'] > userinfo.last_checkin: 
            userinfo.last_checkin = checkin['id']                                                           # because the checkins are ordered with most recent first!
          if userinfo.last_checkin_at is None or datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000") > userinfo.last_checkin_at: 
            userinfo.last_checkin_at = datetime.strptime(checkin['created'], "%a, %d %b %y %H:%M:%S +0000") # because the checkins are ordered with most recent first!
          
          def put_updated_uservenue_and_userinfo(uservenue, userinfo, num_added):
            uservenue.put()
            userinfo.put()
            return num_added + 1
          
          num_added = db.run_in_transaction(put_updated_uservenue_and_userinfo, uservenue, userinfo, num_added)
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + content)
    raise
  return num_added, num_ignored, len(history['checkins'])

def fetch_and_store_checkins_initial(userinfo):
  num_added, num_ignored, num_received = fetch_and_store_checkins(userinfo)
  if num_added != 0:
    taskqueue.add(url='/fetch_foursquare_data/all_for_user/%s' % userinfo.key())
  else:
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
  except DownloadError:    
    logging.warning("DownloadError for user %s, retrying once" % userinfo.user)
    user_data = fs.user()
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
    if 'checkin' in user_data['user'] and 'venue' in user_data['user']['checkin'] and 'geolat' in user_data['user']['checkin']['venue'] and 'geolong' in user_data['user']['checkin']['venue']:
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