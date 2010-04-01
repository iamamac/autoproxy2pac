# -*- coding: utf-8 -*-

import logging
import re
from google.appengine.ext import webapp
from google.appengine.api import memcache

import autoproxy2pac
from models import RuleList
from util import useragent, webcached
from settings import DEBUG, MAIN_SERVER, PRESET_PROXIES, MIRRORS, RATELIMIT_ENABLED, RATELIMIT_DURATION, RATELIMIT_QUOTA

privoxyConfCode = '''
  if(host == "p.p" || dnsDomainIs(host, "config.privoxy.org")) return PROXY;
'''

class Handler(webapp.RequestHandler):
    @webcached('public,max-age=600')  # 10min
    def get(self, urlpart):
        urlpart = urlpart.lower()
        download = self.request.get('download') is not None

        # Redirect to usage page for visits from links (obviously not a browser PAC fetcher)
        if MAIN_SERVER and not download and 'Referer' in self.request.headers:
            self.redirect("/usage?u=" + urlpart, permanent=False)
            return

        proxyString = self.parseProxyString(urlpart)
        if not proxyString:
            self.error(404)
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
                mirror = '%s/%s?%s' % (mirror, urlpart, self.request.query_string)
                logging.debug('Redirect the PAC fetcher to %s', mirror)
                if not DEBUG:
                    # A fixed server for a rate-limiting cycle
                    self.response.headers['Cache-Control'] = 'public,max-age=%d' % (RATELIMIT_DURATION * 3600)
                    self.redirect(mirror, permanent=False)
                    return

        if RATELIMIT_ENABLED and self.isRateLimited(): return

        customRules = self.request.get_all('c')
        customJs = autoproxy2pac.rule2js('\n'.join([''] + customRules))

        if urlpart == 'privoxy': customJs = privoxyConfCode + customJs
        configs = {
            'proxyString': proxyString,
            'defaultString': 'DIRECT',
            'customCodePre': customJs,
        }
        pac = autoproxy2pac.generatePac(rules.toDict(), configs, autoproxy2pac.defaultPacTemplate)

        self.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
        if download: self.response.headers['Content-Disposition'] = 'attachment; filename="autoproxy.pac"'
        self.response.out.write(pac)

    urlPartRegxp = re.compile(r'(proxy|http|socks)/([\w.]+)/(\d+)$')

    def parseProxyString(self, urlpart):
        if urlpart in PRESET_PROXIES:
            ps = PRESET_PROXIES[urlpart][1]
        else:
            match = self.urlPartRegxp.match(urlpart)
            if match is None: return None
            type, host, port = match.groups()
            type = 'SOCKS' if type == 'socks' else 'PROXY'
            ps = '%s %s:%s' % (type, host, port)

        # Chrome expects 'SOCKS5' instead of 'SOCKS', see http://j.mp/pac-test
        if useragent.family() == 'Chrome':
            ps = ps.replace('SOCKS', 'SOCKS5')

        return ps

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
            if not DEBUG:
                self.error(403)
                return True

        return False
