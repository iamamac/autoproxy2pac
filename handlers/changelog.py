# -*- coding: utf-8 -*-

from datetime import timedelta
from google.appengine.ext import webapp
from google.appengine.api import memcache
import django.utils.simplejson as json
from django.utils.feedgenerator import DefaultFeed as Feed

import util
from models import RuleList, ChangeLog

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

class JsonHandler(webapp.RequestHandler):
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

class FeedHandler(webapp.RequestHandler):
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

        self.response.headers['Content-Type'] = Feed.mime_type

        f = Feed(title="%s 更新记录" % name,
                 link=self.request.relative_url(name),
                 description="beta",
                 language="zh")

        for item in logs:
            f.add_item(title="%d月%d日 %s 更新: 增加 %d 条, 删除 %d 条" % (item['timestamp'].month, item['timestamp'].day, name, len(item['block']), len(item['unblock'])),
                       link='',
                       description=util.renderTemplate('changelogRssItem.html', **item),
                       author_name="gfwlist",
                       pubdate=item['timestamp'])

        f.write(self.response.out, 'utf-8')

class HtmlHandler(webapp.RequestHandler):
    def get(self, name):
        rules = RuleList.getList(name.lower())
        if rules is None:
            self.error(404)
            return

        self.response.out.write(util.renderTemplate('changelog.html',
            name=name,
            rss=self.request.relative_url('%s.rss' % name)
        ))
