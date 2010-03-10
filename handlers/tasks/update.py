# -*- coding: utf-8 -*-

import logging
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.api.labs import taskqueue

from models import RuleList

class Handler(webapp.RequestHandler):
    def get(self):
        for name, url in (('gfwlist', 'http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt'),):
            r = RuleList.getList(name)
            if r == None:
                r = RuleList(name=name, url=url)

            if r.update():
                logging.info('%s updated to %s' , name, r.date)
                if name == 'gfwlist': memcache.delete('gfwtest.js')
                memcache.delete('changelog/%s' % name)
                memcache.delete('changelog/%s.log' % name)
                taskqueue.add(url='/tasks/feed_ping', params={'url':'http://feeds.feedburner.com/%s' % name})
