#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
import re
import util
from datastore import RuleList

pacGenUrlRegxp = re.compile(r'(proxy|http|socks)/([\w.]+)/(\d+)$')

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.redirect("https://autoproxy2pac.appspot.com", permanent=True)

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
                                          ('/(.*)', PacGenHandler)])

    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
