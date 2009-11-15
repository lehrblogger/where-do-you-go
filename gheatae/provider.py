from geo import geotypes
from gheatae import consts
from gheatae.point import DataPoint
from google.appengine.api.datastore_types import GeoPt
import logging

log = logging.getLogger('tile')


class Provider(object):
  
  def __init__(self):
    pass
  
  def get_data(self, layer, x, y):
    pass

#cache_georanges = [ [], ] * consts.MAX_ZOOM
#cache_zoom_step = [ [], ] * consts.MAX_ZOOM

#for zoom in range(consts.MAX_ZOOM):
#  width, height = gmerc.ll2px(-90, 180, zoom)
#  numcols = int(math.ceil(width / 256.0))
#  numrows = int(math.ceil(height / 256.0))
#  cache_zoom_step[zoom] = ( 180. / numrows, 360. / numcols )
#  cache_georanges[zoom] = [ [], ] * numrows
#  for y in range(numrows):
#    cache_georanges[zoom][y] = [ [], ] * numcols
#    for x in range(numcols):
#      cache_georanges[zoom][y][x] = ( 180. / numrows * y - 90, 360. / numcols * x - 180 )


class DummyProvider(Provider):
  
  def get_data(self, zoom, layer, x, y):
    return [ DataPoint(location=GeoPt(37.2344, 82.34)), 
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            DataPoint(location=GeoPt(37.2344, 82.34)),
            ]


class DBProvider(Provider):
  
  def get_data(self, zoom, layer, lat_north, lng_west, range_lat, range_lng):
    log.info("GeoRange: (%6.4f, %6.4f) ZoomStep: (%6.4f, %6.4f)" % (lat_north, lng_west, range_lat, range_lng))
    log.info("Range: (%6.4f - %6.4f), (%6.4f - %6.4f)" % (min(90, max(-90, lat_north + range_lat)), lat_north, min(180, max(-180, lng_west + range_lng)), lng_west))
    return DataPoint.bounding_box_fetch(
        DataPoint.all(),
        geotypes.Box(min(90, max(-90, lat_north + range_lat)),
            min(180, max(-180, lng_west + range_lng)),
            lat_north,
            lng_west),
        max_results=1000, )
