import globalvars
import oauth
from models import AccessToken
from data import fetch_and_store_n_recent_checkins_for_token

if globalvars.client == None:
  globalvars.client = oauth.FoursquareClient(globalvars.consumer_key, globalvars.consumer_secret, globalvars.callback_url)

all_tokens = AccessToken.all().order('-created').fetch(1000)
user_list = []
for token in all_tokens:
  if token.owner in user_list:
    token.delete() # delete extra older tokens for each user
  else:
    user_list.append(token.owner)
    fetch_and_store_n_recent_checkins_for_token(token, 20)
