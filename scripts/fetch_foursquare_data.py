from os import environ
import constants
import oauth
#import foursquare
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

def fetch_and_store_checkins(userinfo, limit=50):
  num_added = 0
  num_ignored = 0
  userinfo.valid_signature = True
  userinfo.is_authorized = True
  try:
    fs = get_new_fs_for_userinfo(userinfo)
    total_count = int(fs.users()['user']['checkins']['count'])
    logging.info('COUNT: %s'%total_count)
    if userinfo.checkin_count >= total_count:
      return 0, 0, 0
   # if userinfo.checkin_count > 0:
   #   dt = userinfo.last_checkin_at
   #   seconds = int(mktime(dt.timetuple()))
   #   logging.info('SECONDS: %s'%(seconds))

    to_skip = total_count - limit

    if to_skip >= userinfo.checkin_count:
      to_skip-=userinfo.checkin_count
    else:
      to_skip = 0
      limit = total_count - userinfo.checkin_count
	
    history = fs.users_checkins(limit=limit, offset=to_skip)
    logging.info('SKIP: %s'%to_skip)
    history = fs.users_checkins(limit=limit, offset=to_skip)
    logging.info('HADOUKEN')
    logging.info(history)
  except foursquarev2.FoursquareException, err:
    if str(err).find('SIGNATURE_INVALID') >= 0:
      userinfo.valid_signature = False
      logging.info("User %s is no longer authorized with SIGNATURE_INVALID" % userinfo.user)
      userinfo.put() 
    elif str(err).find('TOKEN_EXPIRED') >= 0:
      userinfo.is_authorized = False
      logging.info("User %s is no longer authorized with TOKEN_EXPIRED" % userinfo.user)
      userinfo.put()
    else:
      logging.warning("History not fetched for %s with %s" % (userinfo.user, err))
    return 0, 0, 0
  except DownloadError, err:
    logging.warning("History not fetched for %s with %s" % (userinfo.user, err))
    return 0, 0, 0
  try:
    if not 'checkins' in history:
      logging.error("no value for 'checkins' in history: " + str(history))
      userinfo.put()
      return -1, 0, 0
    elif history['checkins']['items'] == None:
      userinfo.put()
      return 0, 0, 0
    if not userinfo.gender is 'male' and not userinfo.gender is 'female':
      try:
        user_data = fs.users()
        if 'gender' in user_data['user']:
          userinfo.gender = user_data['user']['gender']
          if user_data['user']['gender'] is 'male':
            userinfo.photo_url = 'static/blank_boy.png'
          elif user_data['user']['gender'] is 'female':
            userinfo.photo_url = 'static/blank_girl.png'
          userinfo.put()
      except DownloadError, err:
        logging.warning("User data not fetched for %s with %s" % (userinfo.user, err))
        return 0, 0, 0
	history['checkins']['items'].reverse()
    for checkin in history['checkins']['items']:
      logging.info('VAI PROCESSAR: %s'%(len(history['checkins']['items'])))
      if 'venue' in checkin:
        logging.info('PROCESSANDO')
        j_venue = checkin['venue']
        logging.info(j_venue)
        if 'id' in j_venue and 'location' in j_venue:
          
          def uservenue_factory(userinfo_param, j_venue_param, checkin_guid_list_param, checkin_list_param, is_unique_param):
            new_uservenue = UserVenue(parent=userinfo_param, location = db.GeoPt(j_venue_param['location']['lat'], j_venue_param['location']['lng']))
            j_venue_param_loc = j_venue_param['location']
            new_uservenue.update_location()
            new_uservenue.user = userinfo_param.user
            new_uservenue.venue_guid     = str(j_venue_param['id'])
            if 'name' in j_venue_param:
              new_uservenue.name         = j_venue_param['name']
            if 'address' in j_venue_param_loc:
              new_uservenue.address      = j_venue_param_loc['address'].replace('\n', ' ').replace('\r', ' ')
            if 'cross_street' in j_venue_param_loc:
              new_uservenue.cross_street = j_venue_param_loc['cross_street']
            if 'state' in j_venue_param_loc:
              new_uservenue.state        = j_venue_param_loc['state']
            if 'zip' in j_venue_param_loc:
              new_uservenue.zipcode      = j_venue_param_loc['zip']
            if 'phone' in j_venue_param:
              new_uservenue.phone        = j_venue_param['phone']
            new_uservenue.has_parent = True
            new_uservenue.is_unique = is_unique_param 
            new_uservenue.checkin_list = checkin_list_param
            new_uservenue.checkin_guid_list = checkin_guid_list_param
            if not new_uservenue.checkin_guid_list or len(new_uservenue.checkin_guid_list) is 0:
              new_uservenue.checkin_guid_list = [str(checkin_id) for checkin_id in new_uservenue.checkin_list]
            return new_uservenue
            
          uservenue = UserVenue.all().filter('user = ', userinfo.user).filter('venue_guid = ', str(j_venue['id'])).filter('has_parent = ', True).get()
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
          uservenue.last_updated = datetime.fromtimestamp(checkin['createdAt']) #WARNING last_updated is confusing and should be last_checkin_at
          if datetime.now() < uservenue.last_updated + timedelta(hours=12):                             #WARNING last_updated is confusing and should be last_checkin_at   
            num_ignored += 1
            continue
          uservenue.checkin_guid_list.append(str(checkin['id']))
          userinfo.checkin_count += 1
          userinfo.last_updated = datetime.now()
          #if checkin['id'] == userinfo.last_checkin:
          #    num_added = 0
          userinfo.last_checkin = checkin['id']                                                # because the checkins are ordered with most recent first!
          if userinfo.last_checkin_at is None or datetime.fromtimestamp(checkin['createdAt']) > userinfo.last_checkin_at: 
            userinfo.last_checkin_at = datetime.fromtimestamp(checkin['createdAt']) # because the checkins are ordered with most recent first!
          
          def put_updated_uservenue_and_userinfo(uservenue, userinfo, num_added):
            uservenue.put()
            userinfo.put()
            return num_added + 1
          
          try:
            num_added = db.run_in_transaction(put_updated_uservenue_and_userinfo, uservenue, userinfo, num_added)
          except BadRequestError, err:
            logging.warning("Database transaction error due to entity restrictions? %s" % err)
  except KeyError:
    logging.error("There was a KeyError when processing the response: " + str(history))
    raise
  return num_added, num_ignored, int(history['checkins']['count'])	

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
    user_data = fs.users()
    logging.info(user_data)
  except foursquarev2.FoursquareException, err:
    if str(err).find('{"unauthorized":"TOKEN_EXPIRED"}') >= 0:
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
      logging.info(user_data)
    except DownloadError, err:
      logging.warning("DownloadError for user %s on first retry, returning" % userinfo.user)
      raise err
      #TODO handle this case better, it's currently a bit of a hack to just get it to return to signin page
  if 'user' in user_data:
    userinfo.real_name = user_data['user']['firstName']
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
    logging.error('no "user" key in json: %s' % user_data)

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
    if userinfo:
      fetch_and_store_checkins_initial(userinfo)
    else: 
      logging.warning('No userinfo found for key %s' % userinfo_key)