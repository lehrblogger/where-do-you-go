from google.appengine.api import users
from os import environ
from models import UserInfo

user = users.get_current_user()
if user:
  path = environ['PATH_INFO']
  try:
    assert path.count('/') == 2, "%d /'s" % path.count('/')
    foo, bar, color_scheme = path.split('/')
    userinfo = UserInfo.all().filter('user =', user).get()
    userinfo.color_scheme = color_scheme
    userinfo.put()
  except AssertionError, err:
    logging.error(err.args[0])
    self.respondError(err)