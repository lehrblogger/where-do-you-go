from gheatae import color_scheme, dot, tile, cache, provider
from gheatae.point import DataPoint
from gheatae.tile import Tile
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from os import environ
import datetime
import handler
import logging
import time

log = logging.getLogger('tile')

class Data(handler.Handler):

  def get(self):
    log.info("Running Data:GET...")
    st = time.clock()
    path = environ['PATH_INFO']

    log.debug("Path:" + path)
    if path.endswith('.cmd'):
      raw = path[:-4] # strip extension
      try:
        assert raw.count('/') == 7, "%d /'s" % raw.count('/')
        foo, bar, cmd, lat, lng, timeOccured, weight, range = raw.split('/')
        assert cmd in ('add', 'del', 'upd'), "'%s' invalid command" % cmd
        assert float(lat), "lat invalid"
        assert float(lng), "lng invalid"
        assert datetime.datetime.fromtimestamp(int(timeOccured)), "time invalid"
        assert int(weight), "weight invalid"
        assert int(range), "weight invalid"
      except AssertionError, err:
        log.error(err.args[0])
        self.respondError(err)
        return
    else:
      self.respondError("Invalid path")
      return

    self.response.headers['Content-Type'] = "text/plain"
    if cmd == "add":
      # Actually add the data specified
      new_data = DataPoint(location=db.GeoPt(float(lat), float(lng)),
                           time=datetime.datetime.fromtimestamp(int(timeOccured)),
                           weight=int(weight),
                           range=int(range))
      new_data.update_location()
      new_data.put()
      log.info("Data Stored")
      self.response.out.write("Data Stored")

    log.info("Start-End: %2.2f" % (time.clock() - st))
