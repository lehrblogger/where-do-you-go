import oauth
from gheatae import provider
from os import environ
import logging
from gheatae import color_scheme


def get_google_maps_apikey():
  path = environ['HTTP_HOST']
  if path == 'where-do-you-go.appspot.com':
    return 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBQO7aMTgd18mR6eRdj9blrVCeGU7BS14EnkGH_2LpNpZ8DJW0u7G5ocLQ'
  elif path == 'www.heredoyougo.com':
    return 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBSsSgGJ9VrJSemFFJvFbS88IsMvVhSj9Nx7jlLtQGoB4gR4tshPH1Hvew'
  elif path == 'www.wheredoyougo.net':
    return 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBSujOi3smKLcjzph36ZE8UXngM_5BTs-xHblsuwK8V9g8bZ_PTfOWR1Fg'

consumer_key = '98ff47ad5541ebaaee51cb5a1e843d1404aeba03f'
consumer_secret = 'f661bcab0416f66a2c6633cde08aefd5'
callback_url = 'http://where-do-you-go.appspot.com/callback/foursquare'

client = None
provider = None

min_zoom = 10
max_zoom = 18 # note that these must also be in the static wdyg.js file

level_const = 150.

default_photo = '/static/foursquare_girl_icon.png'
default_color = color_scheme.color_schemes.keys()[0]
default_lat = 40.728397037445006 #NYC
default_lng = -73.99429321289062