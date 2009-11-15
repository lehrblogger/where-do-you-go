from gheatae import color_scheme, dot, tile, cache, provider
from gheatae.tile import Tile
from gheatae import consts
from os import environ
import logging
import time
import handler

log = logging.getLogger('tile')

tile.cache = cache.Cache()
tile.provider = provider.DBProvider()

class GetTile(handler.Handler):

  def get(self):
    log.info("Running GetTile:GET...")
    st = time.clock()
    path = environ['PATH_INFO']

    log.debug("Path:" + path)
    if path.endswith('.png'):
      raw = path[:-4] # strip extension
      try:
          assert raw.count('/') == 4, "%d /'s" % raw.count('/')
          foo, bar, layer, zoom, yx = raw.split('/')
#          assert color_scheme in color_schemes, ("bad color_scheme: "
#                                                + color_scheme
#                                                 )
          assert yx.count(',') == 1, "%d /'s" % yx.count(',')
          y, x = yx.split(',')
          assert zoom.isdigit() and x.isdigit() and y.isdigit(), "not digits"
          zoom = int(zoom)
          x = int(x)
          y = int(y)
          assert 0 <= zoom <= (consts.MAX_ZOOM - 1), "bad zoom: %d" % zoom
      except AssertionError, err:
          log.error(err.args[0])
          self.respondError(err)
          return
    else:
      self.respondError("Invalid path")
      return

#    color_scheme = color_schemes[color_scheme]
    #try:
    tile = Tile(layer, zoom, x, y)
    log.info("Start-B1: %2.2f" % (time.clock() - st))
#    except Exception, err:
#      self.respondError(err)
#      raise err
#      return

    self.response.headers['Content-Type'] = "image/png"
    #log.info("Building image...")
    img_data = tile.image_out()
    log.info("Start-B2: %2.2f" % (time.clock() - st))
    
    #log.info("Writing out image...")
    self.response.out.write(img_data)
    log.info("Start-End: %2.2f" % (time.clock() - st))
