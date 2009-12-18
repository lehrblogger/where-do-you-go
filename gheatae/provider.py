from geo import geotypes
from models import UserVenue
from google.appengine.api.datastore_types import GeoPt
import logging

log = logging.getLogger('tile')

class Provider(object):

  def __init__(self):
    pass

  def get_data(self, layer, x, y):
    pass

class DBProvider(Provider):

    def get_user_data(self, user=None, lat_north=90, lng_west=-180, range_lat=-180, range_lng=360, max_results=1000):
      # log.info("GeoRange: (%6.4f, %6.4f) ZoomStep: (%6.4f, %6.4f)" % (lat_north, lng_west, range_lat, range_lng))
      # log.info("Range: (%6.4f - %6.4f), (%6.4f - %6.4f)" % (min(90, max(-90, lat_north + range_lat)), lat_north, min(180, max(-180, lng_west + range_lng)), lng_west))

      if user:
        return UserVenue.bounding_box_fetch(UserVenue.all().filter('user =', user).order('-last_checkin'), #TODO find a way to specify this elsewhere!!
          geotypes.Box(min(90, max(-90, lat_north + range_lat)),
              min(180, max(-180, lng_west + range_lng)),
              lat_north,
              lng_west),
          max_results, )
      else:
        return []

    def get_all_data(self, user=None, lat_north=90, lng_west=-180, range_lat=-180, range_lng=360, max_results=1000):
      if user:
        self.get_user_data(user, lat_north, lng_west, range_lat, range_lng, max_results)
      else:
        return UserVenue.bounding_box_fetch(UserVenue.all().order('-last_checkin'),
          geotypes.Box(min(90, max(-90, lat_north + range_lat)),
              min(180, max(-180, lng_west + range_lng)),
              lat_north,
              lng_west),
          max_results, )