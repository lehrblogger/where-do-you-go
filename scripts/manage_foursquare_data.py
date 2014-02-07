from os import environ
import constants
import foursquarev2
import logging
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.api.urlfetch import DownloadError
from google.appengine.api.datastore_errors import BadRequestError
from google.appengine.runtime import DeadlineExceededError
from datetime import datetime, timedelta
from time import mktime
from models import UserInfo, UserVenue

def get_new_fs_for_userinfo(userinfo):
  return foursquarev2.FoursquareClient(userinfo.token)

def fetch_and_store_checkins(userinfo, limit):
  num_added = 0
  userinfo.is_authorized = True
  logging.info('in fetch_and_store_checkins for user %s' % userinfo.user)
  try:
    fs = get_new_fs_for_userinfo(userinfo)
    total_count = int(fs.users()['user']['checkins']['count'])
    logging.info('total checkin count for user %s: %d' % (userinfo.user, total_count))
    if userinfo.checkin_count >= total_count:
      return 0, 0
    to_skip = total_count - limit
    if to_skip >= userinfo.checkin_count:
      to_skip -= userinfo.checkin_count
    else:
      to_skip = 0
      limit = total_count - userinfo.checkin_count
    history = fs.users_checkins(limit=limit, offset=to_skip)
    logging.info('number skipped for user %s: %d' % (userinfo.user, to_skip))
  except foursquarev2.FoursquareException, err:  
    if str(err).find('SIGNATURE_INVALID') >= 0 or str(err).find('TOKEN_EXPIRED') >= 0:
      userinfo.is_authorized = False
      logging.warning("User %s is no longer authorized with err: %s" % (userinfo.user, err))
      userinfo.put()
    else:
      logging.warning("History not fetched for %s with %s" % (userinfo.user, err))
    return 0, 0
  except DownloadError, err:
    logging.warning("History not fetched for %s with %s" % (userinfo.user, err))
    return 0, 0
  try:
    if not 'checkins' in history:
      logging.error("no value for 'checkins' in history: " + str(history))
      userinfo.put()
      return -1, 0
    elif history['checkins']['items'] == None:
      userinfo.put()
      return 0, 0
    history['checkins']['items'].reverse()
    logging.debug('will process %d items' % (len(history['checkins']['items'])))
    for checkin in history['checkins']['items']:
      if 'venue' in checkin:
        j_venue = checkin['venue']
        if 'id' in j_venue:
          uservenue = UserVenue.all().filter('user = ', userinfo.user).filter('venue_guid = ', str(j_venue['id'])).get()
          if not uservenue and 'location' in j_venue and 'lat' in j_venue['location'] and 'lng' in j_venue['location']:
            userinfo.venue_count = userinfo.venue_count + 1
            uservenue = UserVenue(parent=userinfo, location = db.GeoPt(j_venue['location']['lat'], j_venue['location']['lng']))
            uservenue.venue_guid = str(j_venue['id'])
            uservenue.update_location()
            uservenue.user = userinfo.user
            uservenue.checkin_guid_list = []
          if uservenue: # if there's no uservenue by this point, then the venue was missing a location
            uservenue.checkin_guid_list.append(str(checkin['id']))
            userinfo.checkin_count += 1
            def put_updated_uservenue_and_userinfo(uservenue_param, userinfo_param, num_added):
              uservenue_param.put()
              userinfo_param.put()
              return num_added + 1
            try:
              num_added = db.run_in_transaction(put_updated_uservenue_and_userinfo, uservenue, userinfo, num_added)
            except BadRequestError, err:
              logging.warning("Database transaction error due to entity restrictions: %s" % err)
          else:
            logging.error("Venue missing location with JSON: %s" % str(j_venue))
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + str(history))
    raise
  return num_added, int(history['checkins']['count'])	

def fetch_and_store_checkins_next(userinfo, limit=100):
  num_added, num_received = fetch_and_store_checkins(userinfo, limit)
  logging.info("num_added = %d, num_received = %d" % (num_added, num_received))
  if num_added == 0:
    def put_ready_userinfo(userinfo_param):
      userinfo_param.is_ready = True
      userinfo_param.put()
    db.run_in_transaction(put_ready_userinfo, userinfo)
  else:
    taskqueue.add(queue_name='checkins', url='/manage_foursquare_data/next_for_user/%s' % userinfo.key())

def update_user_info(userinfo):
  fs = get_new_fs_for_userinfo(userinfo)
  try:
    user_data = fs.users()
  except foursquarev2.FoursquareException, err:
    if str(err).find('{"unauthorized":"TOKEN_EXPIRED"}') >= 0 or str(err).find('OAuth token invalid or revoked') >= 0:
      userinfo.is_authorized = False
      userinfo.put()
      logging.warning("User %s has unauthorized with %s" % (userinfo.user, err))
      return
    else:
      raise err
  except DownloadError:    
    logging.warning("DownloadError for user %s, retrying once" % userinfo.user)
    try:
      user_data = fs.users()
    except DownloadError, err:
      logging.warning("DownloadError for user %s on first retry, returning" % userinfo.user)
      raise err
      #TODO handle this case better, it's currently a bit of a hack to just get it to return to signin page
  if 'user' in user_data:
    userinfo.real_name = user_data['user']['firstName']
    if 'gender' in user_data['user']:
      userinfo.gender = user_data['user']['gender']
    if 'photo' in user_data['user'] and not user_data['user']['photo'] == '' :
      userinfo.photo_url = user_data['user']['photo']['prefix'] + '100x100' + user_data['user']['photo']['suffix']
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
    logging.error('no "user" key in json: %s' % user_data)

def clear_old_uservenues():
  num_cleared = 0
  cutoff = datetime.now() - timedelta(days=7)   
  userinfos = UserInfo.all().filter('has_been_cleared = ', False).filter('last_updated <', cutoff).fetch(200)
  try:
    for userinfo in userinfos:
      while True:
        uservenues = UserVenue.all(keys_only=True).filter('user =', userinfo.user).fetch(1000)
        if not uservenues: break
        db.delete(uservenues)
        num_cleared = num_cleared + len(uservenues)
      userinfo.has_been_cleared = True
      userinfo.checkin_count = 0
      userinfo.venue_count = 0
      userinfo.last_updated = datetime.now()
      userinfo.put()
    logging.info("finished after deleting at least %d UserVenues for %d UserInfos" % (num_cleared, len(userinfos)))
  except DeadlineExceededError:
    logging.info("exceeded deadline after deleting at least %d UserVenues for %d UserInfos" % (num_cleared, len(userinfos)))
    
if __name__ == '__main__':
  raw = environ['PATH_INFO']
  assert raw.count('/') == 2 or raw.count('/') == 3, "%d /'s" % raw.count('/')

  if raw.count('/') == 2:
    foo, bar, rest, = raw.split('/')
  elif raw.count('/') == 3:
    foo, bar, rest, userinfo_key = raw.split('/')

  if rest == 'clear_old_uservenues':
    clear_old_uservenues()
  elif rest == 'all_for_user':
    user = users.get_current_user()
    if user:
      userinfo = UserInfo.all().filter('user =', user).get()
      if userinfo:
        fetch_and_store_checkins_next(userinfo)
      else:
        logging.warning('No userinfo found for re-fetching user %s' % user)      
    else:
      logging.warning('No user found for re-fetch')
  elif rest == 'next_for_user':
    userinfo = db.get(userinfo_key)
    if userinfo:
      fetch_and_store_checkins_next(userinfo)
    else:
      logging.warning('No userinfo found for key %s' % userinfo_key)