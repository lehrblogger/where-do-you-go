from gheatae import color_scheme, dot, tile, cache, provider
from gheatae.tile import Tile
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from os import environ
import logging
import time

log = logging.getLogger('tile')

class Handler(webapp.RequestHandler):
  
  def respondError(self, message):
    self.response.headers["Content-Type"] = 'text/plain'
    self.response.set_status(400, "Bad Request  (%s)" % message)
    self.response.out.write(message)
