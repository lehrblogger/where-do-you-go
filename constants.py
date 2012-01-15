import oauth_secrets #NOTE this file is not included in the repository because it contains the OAuth consumer secrets
from os import environ
from gheatae import color_scheme
import logging

min_zoom = 3
max_zoom = 18 # note that these must also be in the static wdyg-private.js file

level_const = 140. #TODO fix this from being hard coded in models.py for UserInfo - I was getting a <type 'exceptions.AttributeError'>: 'module' object has no attribute 'level_const'

default_photo = 'static/foursquare_girl.png'
# def get_default_photo(gender='male'):
#   if gender is 'male':
#     return 'static/foursquare_boy.png'
#   else:
#     return 'static/foursquare_girl.png'   
default_color = color_scheme.color_schemes.keys()[0]
default_lat = 40.73607172122901 #NYC
default_lng = -73.96699905395508
default_zoom = 13
default_dimension = 640

def get_google_maps_apikey():
  domain = environ['HTTP_HOST']
  if domain == 'www.wheredoyougo.net':
    return 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBSujOi3smKLcjzph36ZE8UXngM_5BTs-xHblsuwK8V9g8bZ_PTfOWR1Fg'
  elif domain == 'where-do-you-go.appspot.com':
    return 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBQO7aMTgd18mR6eRdj9blrVCeGU7BS14EnkGH_2LpNpZ8DJW0u7G5ocLQ'
  elif domain == 'www.heredoyougo.com':
    return 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBSsSgGJ9VrJSemFFJvFbS88IsMvVhSj9Nx7jlLtQGoB4gR4tshPH1Hvew'
  else:
    logging.error('No Google maps key found for domain ' + domain)

def get_oauth_strings(force_primary_domain=False):
  if force_primary_domain: # I was getting SIGNATURE_INVALID oauth errors on many of my backend calls because 
                           # I was not using the same domain for the requests as I was when the users signed up
                           # Always forcing this will break support for other domains, but will fix some OAuth
                           # issues, so that's what I'm doing for now.
      domain = 'www.wheredoyougo.net'
  else:
      domain = environ['HTTP_HOST']
  logging.info('-------------------------------')
  logging.info(domain)
  if domain == 'www.wheredoyougo.net':
    consumer_key = 'KTNXGQJ4JXDZGAG35MGZ3WN0EQIO5XHNALYQZATHVEPDR3TI'
    callback_url = 'http://www.wheredoyougo.net/authenticated'
  elif domain == 'where-do-you-go.appspot.com':
    consumer_key = 'S1PL51GWSZORANT244XXZC2UXIZGUUPGGNWNA3YHDGWM4M4U'
    callback_url = 'http://where-do-you-go.appspot.com/authenticated'
  elif domain == 'www.heredoyougo.com':
    consumer_key = 'EGB1JZBOMTTNBPVDCHVB3VGGMIXMEYIJKPPTCQGKMPQ4NPCY'
    callback_url = 'http://www.heredoyougo.com/authenticated'
  else:
    consumer_key = ''
    callback_url = ''
    logging.error('No Foursquare OAuth consumer key found for domain ' + domain)
  return consumer_key, oauth_secrets.get_oauth_consumer_secret_for_domain(domain), callback_url

provider = None