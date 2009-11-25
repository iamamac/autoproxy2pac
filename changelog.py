#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
import os
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
        
        start = int(self.request.get('start', 0))
        fetchNum = start + int(self.request.get('num', 50))
        if fetchNum > 1000:
            self.error(412)
            return
        
        changes = memcache.get('changelog/%s' % name)
        if changes is None or len(changes) < fetchNum:
            logs = ChangeLog.gql("WHERE ruleList = :1 ORDER BY date DESC", rules).fetch(fetchNum)
            changes = [{'time'   : (l.date + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
                        'add'    : l.add,
                        'remove' : l.remove} for l in logs]
            memcache.add('changelog/%s' % name, changes)
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(changes[start:fetchNum]))

class ChangelogHtmlHandler(webapp.RequestHandler):
    def get(self, name):
        rules = RuleList.getList(name.lower())
        if rules is None:
            self.error(404)
            return
        
        path = os.path.join(os.path.dirname(__file__), 'changelog.html')
        self.response.out.write(template.render(path, {'name':name}))

if __name__ == '__main__':
    application = webapp.WSGIApplication([('/changelog/(.*)\.json', ChangelogJsonHandler),
                                          ('/changelog/(.*)', ChangelogHtmlHandler)])
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
