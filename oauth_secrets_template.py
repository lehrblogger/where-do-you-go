import logging

# this function allows you to simultaneously run the application on multiple domains
# (such as the default application-name.appspot.com domain as well as your own www.somedomain.com)

def get_oauth_consumer_secret_for_domain(domain):
  if domain == 'FIRST DOMAIN':
    return 'CORRESPONDING CONSUMER SECRET'
  elif domain == 'SECOND DOMAIN':
    return 'CORRESPONDING CONSUMER SECRET'
  else:
    logging.error('No Foursquare OAuth consumer secret found for domain ' + domain)
    return ''