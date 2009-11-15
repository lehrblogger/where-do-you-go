from gheatae import dot
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import logging

log = logging.getLogger('heat_tile')

class MainPage(webapp.RequestHandler):

  def get(self):
    log.info("Running GET...")

    log.info("Writing out image...")
    self.response.headers['Content-Type'] = "image/png"
    self.response.out.write(dot.dot[0])


application = webapp.WSGIApplication(
   [('/.*', MainPage)],
   debug=True)

def main():
  log.info("Running GET...")
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
