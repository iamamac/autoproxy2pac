# -*- coding: utf-8 -*-

import re
import urlparse
from google.appengine.ext import webapp

import util
import autoproxy2pac
import mirrors
from models import RuleList
from pac_config import commonProxy

pacGenUrlRegxp = re.compile(r'(proxy|http|socks)/([\w.]+)/(\d+)$')

privoxyConfCode = '''
  if(host == "p.p" || dnsDomainIs(host, "config.privoxy.org")) return PROXY;
'''

def generatePacResponse(handler, proxy, rules=None):
    '''
    @param handler: the RequestHandler instance
    @param proxy: a proxy name defined in commonProxy or the proxy string as PAC's return value
    '''
    if rules is None:
        rules = RuleList.getList('gfwlist')
        if rules is None:
            handler.error(500)
            return

    proxyString = (commonProxy.get(proxy) or (None, proxy))[1]

    # Chrome expects 'SOCKS5' instead of 'SOCKS', see http://j.mp/pac-test
    if util.getBrowserFamily() == 'Chrome':
        proxyString = proxyString.replace('SOCKS', 'SOCKS5')

    configs = { 'proxyString'   : proxyString,
                'defaultString' : "DIRECT" }
    if proxy == 'privoxy': configs['customCodePost'] = privoxyConfCode
    pac = autoproxy2pac.generatePac(rules.toDict(), configs, autoproxy2pac.defaultPacTemplate)

    handler.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
    handler.response.out.write(pac)

class DownloadHandler(webapp.RequestHandler):
    def get(self):
        proxy = self.request.get('name')
        if proxy not in commonProxy:
            proxy = "%s %s:%s" % (self.request.get('type'), self.request.get('host'), self.request.get('port'))

        self.response.headers['Content-Disposition'] = 'attachment; filename="autoproxy.pac"'
        self.response.headers['Cache-Control'] = 'max-age=600'  # Fix for IE
        generatePacResponse(self, proxy)

class OnlineHandler(webapp.RequestHandler):
    def get(self, param):
        # Redirect to usage page for visits from links (obviously not a browser PAC fetcher)
        if 'Referer' in self.request.headers:
            self.redirect("/usage?u=" + param, permanent=False)
            return

        if 'System.Net.AutoWebProxyScriptEngine' in self.request.headers['User-Agent']:
            self.error(403)
            return

        rules = RuleList.getList('gfwlist')
        if rules is None:
            self.error(500)
            return

        if util.isCachedByBrowser(self, util.cacheAgeForRuleRelated, rules.date): return

        # Load balance
        mirror = mirrors.pick()
        if mirror:
            self.redirect(urlparse.urljoin(mirror, param), permanent=False)
            return

        proxy = param = param.lower()
        if proxy not in commonProxy:
            match = pacGenUrlRegxp.match(param)
            if match is None:
                self.error(404)
                return
            type, host, port = match.groups()
            type = 'SOCKS' if type == 'socks' else 'PROXY'
            proxy = "%s %s:%s" % (type, host, port)

        generatePacResponse(self, proxy, rules)
