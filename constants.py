from os import environ
from gheatae import color_scheme

client = None
provider = None

min_zoom = 10
max_zoom = 18 # note that these must also be in the static wdyg-private.js file

level_const = 140.

default_photo = '/static/foursquare_icon.png'
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


def get_oauth_strings():
  domain = environ['HTTP_HOST']
  if domain == 'www.wheredoyougo.net':
    consumer_key = 'XAWY053VFN4IPANYTHOITQK4UCJIAO20UOCWLEXBCD21H100'
    consumer_secret = 'MWSEKYB2XLGSWZ01SN3KLVOS3YX5COLPUYOAFACJAVTTV5CM'
    callback_url = 'http://www.wheredoyougo.net/authenticated'
  elif domain == 'where-do-you-go.appspot.com':
    consumer_key = '98ff47ad5541ebaaee51cb5a1e843d1404aeba03f'
    consumer_secret = 'f661bcab0416f66a2c6633cde08aefd5'
    callback_url = 'http://where-do-you-go.appspot.com/authenticated'
  elif domain == 'www.heredoyougo.com':
    consumer_key = 'DMP4Z4RGDFRA15GWVPSQ2RVRYC2KSGLFLPX1B5IGD0JE5GPR'
    consumer_secret = 'DHIOPECQMJCXACJQ05FZ14ZYFR3JTC3NKB1XI11DYVGFK4W2'
    callback_url = 'http://www.heredoyougo.com/authenticated'
  else:
    consumer_key = ''
    consumer_secret = ''
    callback_url = ''
    logging.error('No Google maps key found for domain ' + domain)
  return (consumer_key, consumer_secret, callback_url)