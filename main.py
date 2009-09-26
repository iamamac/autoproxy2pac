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
import os, re
import autoproxy2pac
from datastore import RuleList

commonProxy = { 'gappproxy'    : 'PROXY 127.0.0.1:8000',
                'tor'          : 'SOCKS 127.0.0.1:9050',
                'jap'          : 'PROXY 127.0.0.1:4001',
                'your-freedom' : 'PROXY 127.0.0.1:8080',
                'wu-jie'       : 'PROXY 127.0.0.1:9666',
                'free-gate'    : 'PROXY 127.0.0.1:8580',
                'puff'         : 'PROXY 127.0.0.1:1984',
              }

pacGenUrlRegxp = re.compile(r'(proxy|http|socks)/([\w.]+)/(\d+)$')

class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {}))
    
    def post(self):
        rules = RuleList.getList('gfwlist')
        if rules == None: return
        configs = { 'proxyString'   : "%s %s:%s" % (self.request.get('type'), self.request.get('ip'), self.request.get('port')),
                    'defaultString' : "DIRECT" }
        pac = autoproxy2pac.generatePac(rules.toDict(), configs, autoproxy2pac.defaultPacTemplate)

        self.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
        self.response.headers['Content-Disposition'] = 'attachment; filename="autoproxy.pac"'
        self.response.headers['Cache-Control'] = 'max-age=600'  # Fix for IE
        self.response.out.write(pac)

class PacGenHandler(webapp.RequestHandler):
    def get(self, param):
        param = param.lower()
        proxyString = commonProxy.get(param)
        if proxyString == None:
            match = pacGenUrlRegxp.match(param)
            if match == None: return
            type, host, port = match.groups()
            type = 'SOCKS' if type == 'socks' else 'PROXY'
            proxyString = "%s %s:%s" % (type, host, port)
        
        rules = RuleList.getList('gfwlist')
        if rules == None: return
        configs = { 'proxyString'   : proxyString,
                    'defaultString' : "DIRECT" }
        pac = autoproxy2pac.generatePac(rules.toDict(), configs, autoproxy2pac.defaultPacTemplate)
        
        self.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
        self.response.headers['Last-Modified'] = rules.date
        self.response.headers['Cache-Control'] = 'max-age=600'  # Fix for IE
        self.response.out.write(pac)

if __name__ == '__main__':
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/pac/(.*)', PacGenHandler)],
                                         debug=True)
    
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(application)
