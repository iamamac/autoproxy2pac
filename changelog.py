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
        
        logs = memcache.get('changelog/%s' % name)
        if logs is None or len(logs) < fetchNum:
            logs = ChangeLog.gql("WHERE ruleList = :1 ORDER BY date DESC", rules).fetch(fetchNum)
            memcache.add('changelog/%s' % name, logs)
        
        changes = [{'time'   : (l.date + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
                    'add'    : l.add,
                    'remove' : l.remove} for l in logs]
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(changes[start:fetchNum]))

class ChangelogRssHandler(webapp.RequestHandler):
    def get(self, name):
        name = name.lower()
        rules = RuleList.getList(name)
        if rules is None:
            self.error(404)
            return
        
        # Conditional redirect to FeedBurner
        # @see: http://www.google.com/support/feedburner/bin/answer.py?hl=en&answer=78464
        if(self.request.get('raw', None) is None and        # http://host/path/name.rss?raw
           'FeedBurner' not in self.request.user_agent):    # FeedBurner fetcher
            self.redirect('http://feeds.feedburner.com/%s' % name, permanent=False)
            return
        
        if util.isCachedByBrowser(self, 0, rules.date): return
        
        start = int(self.request.get('start', 0))
        fetchNum = start + int(self.request.get('num', 20))
        if fetchNum > 1000:
            self.error(412)
            return
        
        logs = memcache.get('changelog/%s' % name)
        if logs is None or len(logs) < fetchNum:
            logs = ChangeLog.gql("WHERE ruleList = :1 ORDER BY date DESC", rules).fetch(fetchNum)
            memcache.add('changelog/%s' % name, logs)
        
        self.response.headers['Content-Type'] = 'application/rss+xml'
        
        path = os.path.join(os.path.dirname(__file__), 'changelogRssItem.html')
        rss = RSS2(title="%s 更新记录" % name,
                   link=self.request.relative_url(name),
                   description="beta",
                   language="zh",
                   lastBuildDate=rules.date,
                   
                   items=(RSSItem(title="%d月%d日 %s 更新: 增加 %d 条, 删除 %d 条" % (i.date.month, i.date.day, name, len(i.add), len(i.remove)),
                                  author="gfwlist",
                                  description=template.render(path, {'add':i.add, 'remove':i.remove}),
                                  pubDate=i.date.strftime("%a, %d %b %Y %H:%M:%S GMT")) for i in logs))
        
        rss.write_xml(self.response.out, "utf-8")

class ChangelogHtmlHandler(webapp.RequestHandler):
    def get(self, name):
        rules = RuleList.getList(name.lower())
        if rules is None:
            self.error(404)
            return
        
        path = os.path.join(os.path.dirname(__file__), 'changelog.html')
        self.response.out.write(template.render(path, {'name':name, 'rss':self.request.relative_url('%s.rss' % name)}))

if __name__ == '__main__':
    application = webapp.WSGIApplication([('/changelog/(.*)\.json', ChangelogJsonHandler),
                                          ('/changelog/(.*)\.rss', ChangelogRssHandler),
                                          ('/changelog/(.*)', ChangelogHtmlHandler)])
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
