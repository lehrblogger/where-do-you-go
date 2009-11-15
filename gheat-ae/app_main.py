'''
Created on Nov 11, 2009

@author: ddelima
'''

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import tile
import data

application = webapp.WSGIApplication(
   [('/tile/.*', tile.GetTile), 
    ('/data/.*', data.Data)],
   debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()

