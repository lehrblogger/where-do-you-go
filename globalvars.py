import oauth
from gheatae import provider

# where-do-you-go.appspot.com
google_maps_apikey = 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBQO7aMTgd18mR6eRdj9blrVCeGU7BS14EnkGH_2LpNpZ8DJW0u7G5ocLQ'

# www.heredoyougo.com
# google_maps_apikey = 'ABQIAAAAwA6oEsCLgzz6I150wm3ELBSsSgGJ9VrJSemFFJvFbS88IsMvVhSj9Nx7jlLtQGoB4gR4tshPH1Hvew'

consumer_key = "98ff47ad5541ebaaee51cb5a1e843d1404aeba03f"
consumer_secret = "f661bcab0416f66a2c6633cde08aefd5"
callback_url = " http://where-do-you-go.appspot.com/callback/foursquare"

client = None
provider = None