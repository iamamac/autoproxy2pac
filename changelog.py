#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
import os
from datetime import timedelta
import simplejson as json
from PyRSS2Gen import RSS2, RSSItem
import util
from datastore import RuleList, ChangeLog

class ChangelogJsonHandler(webapp.RequestHandler):
    def get(self, name):
        name = name.lower()
        rules = RuleList.getList(name)
        if rules is None:
            self.error(404)
            return
        
        if util.isCachedByBrowser(self, util.cacheAgeForRuleRelated, rules.date): return
        
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

class ChangelogRssHandler(webapp.RequestHandler):
    def get(self, name):
        name = name.lower()
        rules = RuleList.getList(name)
        if rules is None:
            self.error(404)
            return
        
        if util.isCachedByBrowser(self, util.cacheAgeForRuleRelated, rules.date): return
        
        start = int(self.request.get('start', 0))
        fetchNum = start + int(self.request.get('num', 20))
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
        
        self.response.headers['Content-Type'] = 'application/rss+xml'
        
        path = os.path.join(os.path.dirname(__file__), 'changelogRssItem.html')
        rss = RSS2(title="%s 近期更新内容" % name,
                   link=self.request.relative_url(name),
                   description="beta",
                   language="zh",
                   lastBuildDate=rules.date,
                   
                   items=(RSSItem(title="",
                                  description=template.render(path, i),
                                  pubDate=i['time']) for i in changes))
        
        rss.write_xml(self.response.out, "utf8")

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
                                          ('/changelog/(.*)\.rss', ChangelogRssHandler),
                                          ('/changelog/(.*)', ChangelogHtmlHandler)])
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
