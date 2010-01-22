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

def getSampleUrlFromRule(rule):
    from urllib import unquote
    rule = unquote(rule.encode()).decode('utf-8', 'ignore')
    if rule.startswith('||'): return 'http://' + rule[2:]
    if rule.startswith('.'): return 'http://' + rule[1:]
    if rule.startswith('|'): return rule[1:]
    rule = rule.replace('wikipedia.org*', 'wikipedia.org/wiki/')
    if not rule.startswith('http'): return 'http://' + rule
    return rule

def generateLogFromDiff(diff):
    from collections import defaultdict
    urlStatus = defaultdict(lambda:{True:[], False:[]})
    log = {'timestamp':diff.date, 'block':[], 'unblock':[], 'rule_adjust':[]}
    
    for type in ('add', 'remove'):
        blocked = type == 'add'
        for rule in getattr(diff, type):
            if rule.startswith('@@'):
                url = getSampleUrlFromRule(rule[2:])
                log['rule_adjust'].append({'from':(), 'to':(rule,), 'sample_url':url})
            else:
                url = getSampleUrlFromRule(rule)
                urlStatus[url][blocked].append(rule)
    
    for url, status in urlStatus.items():
        if status[True] and not status[False]:
            log['block'].append({'rules':status[True], 'sample_url':url})
        elif not status[True] and status[False]:
            log['unblock'].append({'rules':status[False], 'sample_url':url})
        else:
            log['rule_adjust'].append({'from':status[False], 'to':status[True], 'sample_url':url})
    
    return log

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
        
        logs = memcache.get('changelog/%s.log' % name)
        if logs is None or len(logs) < fetchNum:
            diff = ChangeLog.gql("WHERE ruleList = :1 ORDER BY date DESC", rules).fetch(fetchNum)
            logs = map(generateLogFromDiff, diff)
            memcache.add('changelog/%s.log' % name, logs)
        
        self.response.headers['Content-Type'] = 'application/rss+xml'
        
        path = os.path.join(os.path.dirname(__file__), 'changelogRssItem.html')
        rss = RSS2(title="%s 更新记录" % name,
                   link=self.request.relative_url(name),
                   description="beta",
                   language="zh",
                   lastBuildDate=rules.date,
                   
                   items=(RSSItem(title="%d月%d日 %s 更新: 增加 %d 条, 删除 %d 条" % (i['timestamp'].month, i['timestamp'].day, name, len(i['block']), len(i['unblock'])),
                                  author="gfwlist",
                                  description=template.render(path, i),
                                  pubDate=i['timestamp'].strftime("%a, %d %b %Y %H:%M:%S +0800")) for i in logs))
        
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
