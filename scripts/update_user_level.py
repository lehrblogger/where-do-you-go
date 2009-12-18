from google.appengine.api import users
from gheatae import provider
from os import environ
from models import UserInfo
import constants
import logging


user = users.get_current_user()
if user:
  userinfo = UserInfo.all().filter('user =', user).order('-created').get()
  path = environ['PATH_INFO']

  try:
    assert path.count('/') == 4, "%d /'s" % path.count('/')
    foo, bar, level_offset, northwest, southeast = path.split('/')
    level_offset = int(level_offset)
    assert northwest.count(',') == 1, "%d ,'s" % northwest.count(',')
    northlat, westlng = northwest.split(',')
    assert southeast.count(',') == 1, "%d ,'s" % southeast.count(',')
    southlat, eastlng = southeast.split(',')

    if not constants.provider:
      constants.provider = provider.DBProvider()
    visible_uservenues = constants.provider.get_user_data(user, float(northlat), float(westlng), float(southlat) - float(northlat), float(eastlng) - float(westlng))

    visible_checkin_count = 0
    for venue in visible_uservenues:
      visible_checkin_count = visible_checkin_count + len(venue.checkin_list)

    logging.info("visible_checkin_count=%d  len(visible_uservenues)=%d" % (visible_checkin_count, len(visible_uservenues)))
    userinfo.level_max = int(float(visible_checkin_count) / max(float(len(visible_uservenues)), 1) * (constants.level_const + level_offset))
    userinfo.put()

  except AssertionError, err:
    logging.error(err.args[0])
