#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import os, re
import util
from datastore import RuleList
import gfwtest

pacGenUrlRegxp = re.compile(r'(proxy|http|socks)/([\w.]+)/(\d+)$')

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.headers['Cache-Control'] = 'public, max-age=3600'
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path,
            { 'commonProxy' : ((k, v[0]) for k, v in util.commonProxy.items()),
              'isIE'        : util.getBrowserFamily(self.request.headers) == 'IE' }))
    
    def post(self):
        proxy = self.request.get('name')
        if proxy not in util.commonProxy:
            proxy = "%s %s:%s" % (self.request.get('type'), self.request.get('host'), self.request.get('port'))
        
        self.response.headers['Content-Disposition'] = 'attachment; filename="autoproxy.pac"'
        self.response.headers['Cache-Control'] = 'max-age=600'  # Fix for IE
        util.generatePacResponse(self, proxy)

class PacGenHandler(webapp.RequestHandler):
    def get(self, param):
        rules = RuleList.getList('gfwlist')
        if rules is None:
            self.error(500)
            return
        
        # Enable browser cache, see http://www.mnot.net/cache_docs/
        if self.request.headers.get('If-Modified-Since') == rules.date:
            self.error(304)
            return
        self.response.headers['Cache-Control'] = 'public, max-age=600'
        self.response.headers['Last-Modified'] = rules.date
        
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
                                          ('/pac/(.*)', PacGenHandler),
                                          ('/gfwtest.js', gfwtest.JsGenHandler),
                                          ('/gfwtest', gfwtest.TestPageHandler)],
                                         debug=True)
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
