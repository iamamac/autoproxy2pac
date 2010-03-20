# -*- coding: utf-8 -*-

import logging
import xmlrpclib
from google.appengine.ext import webapp

class FeedBurnerHandler(webapp.RequestHandler):
    '''
    Ping FeedBurner to update the feed immediately
    @see: http://feedburner.google.com/fb/a/ping
    '''
    def post(self):
        url = self.request.get('url')

        try:
            rpc = xmlrpclib.ServerProxy('http://ping.feedburner.google.com/')
            result = rpc.weblogUpdates.ping('', url)

            if result['flerror']: raise xmlrpclib.Fault(1, result['message'])
        except xmlrpclib.Error, e:
            logging.error('Ping FeedBurner for %s failed: %s', url, e)
            self.error(500)
            return

        logging.debug('Pinged FeedBurner for %s', url)
