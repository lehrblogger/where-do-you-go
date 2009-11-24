all_tokens = AccessToken.all().order('-created').fetch(1000)
user_list = []
for token in all_tokens:
  if token.owner in user_list:
    token.delete() # delete extra older tokens for each user
  else:
    user_list.append(token.owner)
    fetch_and_store_n_recent_checkins_for_token(token, 20, oauthcleint.client)
