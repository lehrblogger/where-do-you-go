


Where Do You Go provided Foursquare users with a dynamic heat map of the places they had visited on top of a standard Google Maps interface. Users could create static snapshots of their maps and then share them on Twitter, and these maps would self-update automatically in the background as users continued to visit new places and checkin with Foursquare.

(Note that user privacy was protected because recent data is not shown and because individual check-ins are aggregated into an imprecise heat map.)

http://lehrblogger.com/2010/03/19/where-do-you-go/

This project went on for quite a while longer than the quick hack I intended it to be, so I apologize if the code is a bit of a mess. To create your own Google App Engine installation of Where Do You Go you'll need to modify constants.py (and create the gitignore'd oauth_secrets.py) to contain the Google Maps API key and Foursquare consumer key/secret for the domain(s) you're using. Many thanks to Thiago Ganzarolli (https://github.com/tganzarolli) for updating the app to work with v2 of Foursquare's API!

Feel free to contact me if you have any questions!

### Update on June 30, 2023

Due to changes in Google App Engine and the associated tooling ([RIP `appcfg`](https://cloud.google.com/appengine/docs/legacy/standard/python/deprecations/shut-down)), a nontrivial amount of effort would be needed before this application could be re-deployed. When changes are inevitably necessary, I'm probably going to:

  1. Shut down the App Engine app.
  0. Use the [Google Cloud Console](https://console.cloud.google.com/datastore/databases/) to export and download my databases.
  0. Generate a list of the public static map URLs, which I can download with [SiteSucker](https://ricks-apps.com/osx/sitesucker/index.html) or a similar tool.
  0. Perform a find-replace to update the Universal Analytics tags for Google Analytics 4.
  0. Re-host those static files on S3 and update the DNS, so the URLs will continue to work and people can enjoy their old maps.
  0. Provide a link to a Google Form (even requiring authentication so I can verify the submitter is a user!) to handle data deletion requests.
