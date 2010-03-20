# -*- coding: utf-8 -*-

import logging
import re
import urlparse
from google.appengine.ext import webapp
from google.appengine.api import memcache

import autoproxy2pac
from models import RuleList
from pac_config import commonProxy
from util import useragent, webcached
from settings import DEBUG, MAIN_SERVER, MIRRORS, RATELIMIT_ENABLED, RATELIMIT_DURATION, RATELIMIT_QUOTA

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
    if useragent.family() == 'Chrome':
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
    @webcached('public,max-age=600')  # 10min
    def get(self, param):
        # Redirect to usage page for visits from links (obviously not a browser PAC fetcher)
        if MAIN_SERVER and 'Referer' in self.request.headers:
            self.redirect("/usage?u=" + param, permanent=False)
            return

        rules = RuleList.getList('gfwlist')
        if rules is None:
            self.error(500)
            return

        self.response.headers['ETag'] = '"' + rules.date.replace(',', '').replace(' ', '') + '"'
        self.lastModified(rules.date)

        # Load balance
        if MAIN_SERVER:
            mirror = self.pickMirror()
            if mirror:
                mirror = urlparse.urljoin(mirror, param)
                logging.debug('Redirect the PAC fetcher to %s', mirror)
                if not DEBUG:
                    # A fixed server for a rate-limiting cycle
                    self.response.headers['Cache-Control'] = 'public,max-age=%d' % RATELIMIT_DURATION * 3600
                    self.redirect(mirror, permanent=False)
                    return

        if RATELIMIT_ENABLED and self.isRateLimited(): return

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

    def pickMirror(self):
        return MIRRORS[hash(self.request.remote_addr) % len(MIRRORS)]

    def isRateLimited(self):
        param = {'ip':self.request.remote_addr, 'ua':self.request.user_agent}

        key = '%(ua)s@%(ip)s' % param
        rate = memcache.incr(key, namespace='rate')  # incr won't refresh the expiration time
        if rate is None:
            rate = 1
            memcache.add(key, 1, RATELIMIT_DURATION * 3600, namespace='rate')

        quota = RATELIMIT_QUOTA(**param)
        if rate > quota:
            if rate == quota + 1:
                logging.info('%(ip)s has reached the rate limit (%(qt)d per %(dur)dh), UA="%(ua)s"', dict(qt=quota, dur=RATELIMIT_DURATION, **param))
            logging.debug('%(ip)s is banned on full fetch #%(rt)d, UA="%(ua)s"', dict(rt=rate, **param))
            self.error(403)
            return True

        return False
