#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import os, re
import util
from datastore import RuleList

pacGenUrlRegxp = re.compile(r'(proxy|http|socks)/([\w.]+)/(\d+)$')

class MainHandler(webapp.RequestHandler):
    def get(self):
        if util.isCachedByBrowser(self, util.cacheAgeForStatic): return
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path,
            { 'commonProxy' : ((k, v[0]) for k, v in util.commonProxy.items()) }))
    
    def post(self):
        proxy = self.request.get('name')
        if proxy not in util.commonProxy:
            proxy = "%s %s:%s" % (self.request.get('type'), self.request.get('host'), self.request.get('port'))
        
        self.response.headers['Content-Disposition'] = 'attachment; filename="autoproxy.pac"'
        self.response.headers['Cache-Control'] = 'max-age=600'  # Fix for IE
        util.generatePacResponse(self, proxy)

class UsageHandler(webapp.RequestHandler):
    def get(self):
        if util.isCachedByBrowser(self, util.cacheAgeForStatic): return
        
        url = self.request.get('u')
        if url: url = 'http://%s/pac/%s' % (self.request.host, url)
        
        path = os.path.join(os.path.dirname(__file__), 'usage.html')
        self.response.out.write(template.render(path,
            { 'url'     : url,
              'browser' : util.getBrowserFamily() }))

class PacGenHandler(webapp.RequestHandler):
    def get(self, param):
        rules = RuleList.getList('gfwlist')
        if rules is None:
            self.error(500)
            return
        
        if util.isCachedByBrowser(self, util.cacheAgeForRuleRelated, rules.date): return
        
        proxy = param = param.lower()
        if proxy not in util.commonProxy:
            match = pacGenUrlRegxp.match(param)
            if match is None:
                self.error(404)
                return
            type, host, port = match.groups()
            type = 'SOCKS' if type == 'socks' else 'PROXY'
            proxy = "%s %s:%s" % (type, host, port)
        
        util.generatePacResponse(self, proxy, rules)

if __name__ == '__main__':
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/usage', UsageHandler),
                                          ('/pac/(.*)', PacGenHandler)])
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
