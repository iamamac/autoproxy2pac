#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import os
import autoproxy2pac
from datastore import RuleList

jsTemplate = '''/*
 * Provide a javascript function to determine whether a URL is blocked in mainland China
 * You can get this file at https://autoproxy2pac.appspot.com/gfwtest.js
 *
 * Usage: isBlockedByGFW(url), returns true if the URL is blocked
 *
 * Last update: %(ruleListDate)s
 */
function isBlockedByGFW(url) {
  %(proxyVar)s = true;
  %(defaultVar)s = false;

%(ruleListCode)s

  return %(defaultVar)s
}
'''

class JsGenHandler(webapp.RequestHandler):
    def get(self):
        rules = RuleList.getList('gfwlist')
        if rules == None: return
        
        js = autoproxy2pac.generatePac(rules.toDict(), (), jsTemplate)
        
        self.response.headers['Content-Type'] = 'application/x-javascript'
        self.response.headers['Last-Modified'] = rules.date
        self.response.out.write(js)

class TestPageHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'gfwtest.html')
        self.response.out.write(template.render(path, None))
