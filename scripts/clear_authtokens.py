from datetime import datetime, timedelta
import logging
from google.appengine.ext import db
from models import AuthToken

delta = timedelta(seconds=60*60*2)
while(AuthToken.all().count() > 0):
  authtokens = AuthToken.all().fetch(1000)
  for authtoken in authtokens:
    if datetime.now() > authtoken.created + delta:
      db.delete(authtoken)