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
google_maps_apikey = 'AIzaSyAYBD8ThpvGz1biNHjH00lI-zuiNxdQLX4'
provider = None
