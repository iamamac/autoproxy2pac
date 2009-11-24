#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.api import memcache
import simplejson as json
from datastore import RuleList, ChangeLog
from datetime import timedelta

class ChangelogJsonHandler(webapp.RequestHandler):
    def get(self, name):
        name = name.lower()
        rules = RuleList.getList(name)
        if rules is None:
            self.error(404)
            return
        
        # Enable browser cache, see http://www.mnot.net/cache_docs/
        if self.request.headers.get('If-Modified-Since') == rules.date:
            self.error(304)
            return
        self.response.headers['Cache-Control'] = 'public, max-age=600'
        self.response.headers['Last-Modified'] = rules.date
        
        JSON = memcache.get('changelog/%s.json' % name)
        if JSON is None:
            logs = ChangeLog.gql("WHERE ruleList = :1 ORDER BY date DESC", rules).fetch(
                                 limit=int(self.request.get('num', 50)),
                                 offset=int(self.request.get('start', 0)))
            JSON = json.dumps([{'time'   : (l.date + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
                                'add'    : l.add,
                                'remove' : l.remove} for l in logs])
            memcache.add('changelog/%s.json' % name, JSON)
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(JSON)

if __name__ == '__main__':
    application = webapp.WSGIApplication([('/changelog/(.*)\.json', ChangelogJsonHandler)])
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
