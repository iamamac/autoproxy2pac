#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import os
import autoproxy2pac

class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {}))
    
    def post(self):
        ruleListUrl = "http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt"
        
        ruleList, ruleListDate = autoproxy2pac.fetchRuleList(ruleListUrl)
        rules = { 'ruleListUrl'  : ruleListUrl,
                  'ruleListDate' : ruleListDate,
                  'ruleListCode' : autoproxy2pac.rule2js(ruleList) }
        configs = { 'proxyString'   : "%s %s:%s" % (self.request.get('type'), self.request.get('ip'), self.request.get('port')),
                    'defaultString' : "DIRECT" }
        pac = autoproxy2pac.generatePac(rules, configs, autoproxy2pac.defaultPacTemplate)

        self.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
        self.response.headers['Content-Disposition'] = 'attachment; filename="autoproxy.pac"'
        self.response.headers['Cache-Control'] = 'max-age=600'  # Fix for IE
        self.response.out.write(pac)

class PacGenHandler(webapp.RequestHandler):
    def get(self, type, host, port):
        ruleListUrl = "http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt"
        
        ruleList, ruleListDate = autoproxy2pac.fetchRuleList(ruleListUrl)
        rules = { 'ruleListUrl'  : ruleListUrl,
                  'ruleListDate' : ruleListDate,
                  'ruleListCode' : autoproxy2pac.rule2js(ruleList) }
        configs = { 'proxyString'   : "%s %s:%s" % ('PROXY' if type == 'http' else 'SOCKS', host, port),
                    'defaultString' : "DIRECT" }
        pac = autoproxy2pac.generatePac(rules, configs, autoproxy2pac.defaultPacTemplate)

        self.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
        self.response.headers['Last-Modified'] = ruleListDate
        self.response.headers['Cache-Control'] = 'max-age=600'  # Fix for IE
        self.response.out.write(pac)

if __name__ == '__main__':
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/pac/(http|socks)/([\w.]+)/(\d+)', PacGenHandler)],
                                         debug=True)
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
