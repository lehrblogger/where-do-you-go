# -*- coding: utf-8 -*-
"""
A python wrapper for the foursquare APIv2

Author: Juan Odicio <juanodicio@gmail.com>

https://github.com/juanodicio/foursquare-apiv2-python

If you are looking for a complete foursquare-APIv2 reference, go to
http://developer.foursquare.com/docs/

"""

import urllib
import httplib2
import json
import logging

VERSION = '0.7'
VERSION_DATE = '20120609'


class FoursquareException(Exception):
    pass
    
class FoursquareRemoteException(FoursquareException):
    def __init__(self, method, code, msg):
        self.method = method
        self.code = code
        self.msg = msg

    def __str__(self):
        return 'Error signaled by remote method %s: %s (%s)' % (self.method, self.msg, self.code)

class FoursquareAuthHelper(object):
    _consumer_key = ''
    _consumer_secret = ''
    
    _access_token_url = 'https://foursquare.com/oauth2/access_token'
    _authentication_url = 'https://foursquare.com/oauth2/authenticate'
    _oauth_callback_uri = ''
    
    API_URL = 'https://api.foursquare.com/v2/'
    
    def __init__(self, key, secret, redirect_uri):
        self._consumer_key = key
        self._consumer_secret = secret
        self._oauth_callback_uri = redirect_uri
        
    def get_callback_uri(self):
        return self._oauth_callback_uri
    
    def get_authentication_url(self):
        query = {
            'v': VERSION_DATE,
            'client_id': self._consumer_key,
            'response_type': 'code',
            'redirect_uri': self._oauth_callback_uri
        }
        query_str = self.urlencode(query)
        return self._authentication_url + "?" + query_str

    def get_access_token_url(self, code):
        query = {
            'v': VERSION_DATE,
            'client_id': self._consumer_key,
            'client_secret': self._consumer_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self._oauth_callback_uri,
            'code': code
        }
        query_str = self.urlencode(query)
        return self._access_token_url + "?" + query_str
    
    def get_access_token(self, code):
        http = httplib2.Http()
        resp, content = http.request(self.get_access_token_url(code))
        j = json.loads(content)
        if 'access_token' in j:
            return j['access_token']
        else:
            return None
                
    def urlencode(self, query):
        return urllib.urlencode(query)
    
    
class FoursquareClient(object):
    
    API_URL = 'https://api.foursquare.com/v2'
    
    _access_token = ''
    
    def __init__(self, access_token):
        self._access_token = access_token
        
    def get_access_token(self):
        return self._access_token
        
    def _remove_empty_params(self, params):
        ret = {}
        for key in params:
            if not params[key] == None:
                ret[key] = params[key]
        return ret
                
    def make_api_call(self, url, method='GET', query={}, body={}, add_token=True):
        if add_token:
            query['oauth_token'] = self._access_token
            
        query = self._remove_empty_params(query)
        body = self._remove_empty_params(body)
        if 'v' not in query:
            query['v'] = VERSION_DATE
        query_str = urllib.urlencode(query)
        body_str = urllib.urlencode(body)
        
        if len(query) > 0:
            if url.find('?') == -1:
                url = url + '?' + query_str
            else:
                url = url + '&' + query_str
                    
        h = httplib2.Http()
        try:
          resp, content = h.request(url, method, body=body_str)
          raw_response = json.loads(content)
          if raw_response['meta']['code'] != 200:
            logging.error('ERROR: %s' % raw_response)
            raise FoursquareRemoteException(url, response.status, response_body)
          return raw_response['response']
        except Exception, err:
          logging.error(err)
          raise FoursquareException()
        
        
        
    # Not tested
    def users(self, user_id='self'):
        url = self.API_URL + '/users/%s' % user_id
        return self.make_api_call(url, method='GET')

    def users_search(self, phone=None, email=None, twitter=None
                     , twitter_source=None, fbid=None, name=None):
        url = self.API_URL + '/users/search'
        query = {
            'phone': phone,
            'email': email,
            'twitter': twitter,
            'twitterSource': twitter_source,
            'fbid': fbid,
            'name': name
        }
        return self.make_api_call(url, method='GET', query=query)
        
    def users_requests(self):
        url = self.API_URL + '/users/requests'
        return self.make_api_call(url, method='GET')

    def users_badges(self, user_id='self'):
        url = self.API_URL + '/users/%s/badges' % user_id
        return self.make_api_call(url, method='GET')
    
    def users_checkins(self, user_id='self', limit=250, after_timestamp=None, offset=0):
        url = self.API_URL + '/users/%s/checkins?offset=%s&limit=%s'%(user_id, offset, limit)
        if after_timestamp:
            url = url+'&afterTimestamp=%s'%(after_timestamp)
        return self.make_api_call(url, method='GET')
    
    def users_friends(self, user_id='self'):
        url = self.API_URL + '/users/%s/friends' % user_id
        return self.make_api_call(url, method='GET')
    
    def users_tips(self, user_id='self', sort='recent', ll=None):
        url = self.API_URL + '/users/%s/tips' % user_id
        query = {
            'sort': sort,
            'll': ll
        }
        return self.make_api_call(url, method='GET', query=query)
    
    def users_todos(self, user_id='self', sort='recent', ll=None):
        url = self.API_URL + '/users/%s/todos' % user_id
        query = {
            'sort': sort,
            'll': ll
        }
        return self.make_api_call(url, method='GET', query=query)
    
    def users_venuehistory(self, user_id='self'):
        url = self.API_URL + '/users/%s/venuehistory' % user_id
        return self.make_api_call(url, method='GET')
    
    def users_lists(self, user_id='self', ll='40.7,-74'):
        url = self.API_URL + '/users/%s/lists' % user_id
        query = {'ll': ll}
        return self.make_api_call(url, method='GET', query=query)
    #---------- POST -----------------------
    
    def users_request(self, user_id):
        url = self.API_URL + '/users/%s/request' % user_id
        return self.make_api_call(url, method='POST')
    
    def users_unfriend(self, user_id):
        url = self.API_URL + '/users/%s/unfriend' % user_id
        return self.make_api_call(url, method='POST')
    
    def users_approve(self, user_id):
        url = self.API_URL + '/users/%s/approve' % user_id
        return self.make_api_call(url, method='POST')
    
    def users_deny(self, user_id):
        url = self.API_URL + '/users/%s/deny' % user_id
        return self.make_api_call(url, method='POST')
    
    def users_setpings(self, user_id, value=False):
        """ NOTE: Documentation says that value parameter should be sent as
        POST var but it only works if you send it as query string
        """
        url = self.API_URL + '/users/%s/setpings' % user_id
        query = {
            'value': value
        }
        return self.make_api_call(url, method='POST', query=query)
    
    def venues(self, venue_id):
        url = self.API_URL + '/venues/%s' % venue_id
        return self.make_api_call(url, method='GET')
    # TODO: not tested
    def venues_add(self, name, address=None, cross_street=None, city=None
                   , state=None, zip=None, phone=None
                   , ll=None, primary_category_id=None):
        url = self.API_URL + '/venues/add'
        body = {
            'name': name,
            'address': address,
            'crossStreet': cross_street,
            'city': city,
            'state': state,
            'zip': zip,
            'phone': phone,
            'll': ll,
            'primaryCategoryId': primary_category_id
        }
        return self.make_api_call(url, method='POST', body=body)
    
    def venues_categories(self):
        url = self.API_URL + '/venues/categories'
        return self.make_api_call(url, method='GET')

    def venues_search(self, ll=None, ll_acc=None, alt=None, alt_acc=None
                      , query=None, limit=None, intent=None):
        url = self.API_URL + '/venues/search'
        query = {
            'll': ll,
            'llAcc': ll_acc,
            'alt': alt,
            'altAcc': alt_acc,
            'query': query,
            'limit': limit,
            'intent': intent
        }
        return self.make_api_call(url, method='GET', query=query)
    
    def venues_herenow(self, venue_id):
        url = self.API_URL + '/venues/%s/herenow' % venue_id
        return self.make_api_call(url, method='GET')
    
    def venues_tips(self, venue_id, sort='recent'):
        url = self.API_URL + '/venues/%s/tips' % venue_id
        return self.make_api_call(url, method='GET')

    def venues_marktodo(self, venue_id, text=''):
        url = self.API_URL + '/venues/%s/marktodo' % venue_id
        body = {
            'text': text
        }
        return self.make_api_call(url, method='POST', body=body)

    def venues_flag(self, venue_id, problem):
        problem_set = ['mislocated', 'closed', 'duplicated']
        url = self.API_URL + '/venues/%s/flag' % venue_id
        query = {
            'problem': problem
        }
        return self.make_api_call(url, method='POST', query=query)
    # TODO: not tested
    def venues_proposeedit(self, venue_id, name, address=None
                   , cross_street=None, city=None
                   , state=None, zip=None, phone=None
                   , ll=None, primary_category_id=None):
        url = self.API_URL + '/venues/%s/proposeedit' % venue_id
        body = {
            'name': name,
            'address': address,
            'crossStreet': cross_street,
            'city': city,
            'state': state,
            'zip': zip,
            'phone': phone,
            'll': ll,
            'primaryCategoryId': primary_category_id
        }
        return self.make_api_call(url, method='POST', body=body)
    
    def checkins(self, checkin_id):
        url = self.API_URL + '/checkins/%s' % checkin_id
        return self.make_api_call(url, method='GET')
    
    def checkins_add(self, venue_id=None, venue=None, shout=None
                     , broadcast='public', ll=None, ll_acc=None
                     , alt=None, alt_acc=None):
        url = self.API_URL + '/checkins/add'
        body = {
            'venueId': venue_id,
            'venue': venue,
            'shout': shout,
            'broadcast': broadcast,
            'll': ll,
            'llAcc': ll_acc,
            'alt': alt,
            'altAcc': alt_acc
        }
        return self.make_api_call(url, method='POST', query=body)
    
    def checkins_recent(self, ll=None, limit=None, offset=None
                        , after_timestamp=None):
        url = self.API_URL + '/checkins/recent'
        query = {
            'll': ll,
            'limit': limit,
            'offset': offset,
            'afterTimestamp': after_timestamp
        }
        return self.make_api_call(url, method='GET', query=query)
    
    def checkins_addcomment(self, checkin_id, text):
        url = self.API_URL + '/checkins/%s/addcomment' % checkin_id
        query = {
            'text': text
        }
        return self.make_api_call(url, method='POST', query=query)
    
    def checkins_deletecomment(self, checkin_id, comment_id):
        url = self.API_URL + '/checkins/%s/deletecomment' % checkin_id
        body = {
            'commentId': comment_id
        }
        return self.make_api_call(url, method='POST', query=body)
        
    
    def tips(self, tip_id):
        url = self.API_URL + '/tips/%s' % tip_id
        return self.make_api_call(url, method='GET')
    # TODO Not tested
    def tips_add(self, venue_id, text, url=None):
        url = self.API_URL + '/tips/add'
        query = {
            'venueId': venue_id,
            'text': text,
            'url': url
        }
        return self.make_api_call(url, method='POST', query=query)
    
    def tips_search(self, ll, limit=None, offset=None, filter=None, query=None):
        url = self.API_URL + '/tips/search'
        query = {
            'll': ll,
            'limit': limit,
            'offset': offset,
            'filter': filter,
            'query': query
        }
        return self.make_api_call(url, method='GET', query=query)

    def tips_marktodo(self, tip_id):
        url = self.API_URL + '/tips/%s/marktodo' % tip_id
        return self.make_api_call(url, method='POST')

    def tips_markdone(self, tip_id):
        url = self.API_URL + '/tips/%s/markdone' % tip_id
        return self.make_api_call(url, method='POST')

    def tips_unmark(self, tip_id):
        url = self.API_URL + '/tips/%s/unmark' % tip_id
        return self.make_api_call(url, method='POST')
    # TODO: Not tested
    def photos(self, photo_id):
        url = self.API_URL + '/photos/%s' % photo_id
        return self.make_api_call(url, method='GET')
    # TODO: Not implemented
    
    # LISTS
    def list_detail(self, list_id):
        url = self.API_URL + '/lists/%s' %list_id
        return self.make_api_call(url, method='GET')
    
    def list_add(self, name, description=None, collaborative=True, photo_id=None):
        url = self.API_URL + '/lists/add'
        query = {
            'name': name,
            'description': description,
            'collaborative': collaborative,
            'photoId': photo_id
        }
        return self.make_api_call(url, method='POST', query=query)

#TODO: add the rest of the lists endpoints
    
    def photos_add(self, photo_path, checkin_id=None, tip_id=None
                   , venue_id=None, broadcast=None
                   , ll=None, ll_acc=None
                   , alt=None, alt_acc=None):
        url = self.API_URL + '/photos/add'
        body = {
            'checkinId': checkin_id,
            'tipId': tip_id,
            'venueId': venue_id,
            'broadcast': broadcast,
            'll': ll,
            'llAcc': ll_acc,
            'alt': alt,
            'alt_acc': alt_acc
        }
        return self.make_api_call(url, method='POST', query=body)
    
    def settings_all(self):
        url = self.API_URL + '/settings/all'
        return self.make_api_call(url, method='GET')
    
    def settings_set(self, setting_id, value):
        url = self.API_URL + '/settings/%s/set' % setting_id
        query = {
            'value': value
        }
        return self.make_api_call(url, method='POST', query=query)