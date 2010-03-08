# -*- coding: utf-8 -*-

from google.appengine.ext import webapp

import util

commonProxy = {
                'gappproxy'    : ('GAppProxy', 'PROXY 127.0.0.1:8000'),
                'tor'          : ('Tor', 'PROXY 127.0.0.1:8118; SOCKS 127.0.0.1:9050'),
                'jap'          : ('JAP', 'PROXY 127.0.0.1:4001'),
                'your-freedom' : ('Your Freedom', 'PROXY 127.0.0.1:8080'),
                'wu-jie'       : ('无界', 'PROXY 127.0.0.1:9666'),
                'free-gate'    : ('自由门', 'PROXY 127.0.0.1:8580'),
                'puff'         : ('Puff', 'PROXY 127.0.0.1:1984'),
                'privoxy'      : ('Privoxy + SOCKS', 'PROXY 127.0.0.1:8118'),
                'ssh-d'        : ('ssh -D / MyEnTunnel', 'SOCKS 127.0.0.1:7070'),
              }

class MainHandler(webapp.RequestHandler):
    def get(self):
        if util.isCachedByBrowser(self, util.cacheAgeForStatic): return

        self.response.out.write(util.renderTemplate('index.html',
            commonProxy=((k, v[0]) for k, v in commonProxy.items()),
            gfwlistRss=self.request.relative_url('/changelog/gfwlist.rss'),
        ))

class UsageHandler(webapp.RequestHandler):
    def get(self):
        if util.isCachedByBrowser(self, util.cacheAgeForStatic): return

        url = self.request.get('u')
        if url: url = 'http://%s/pac/%s' % (self.request.host, url)

        self.response.out.write(util.renderTemplate('usage.html',
            url=url,
            browser=util.getBrowserFamily(),
        ))
