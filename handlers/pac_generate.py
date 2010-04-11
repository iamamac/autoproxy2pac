# -*- coding: utf-8 -*-

import logging
import re
from base64 import urlsafe_b64decode, urlsafe_b64encode
from calendar import timegm
from datetime import datetime
from email.utils import formatdate, parsedate
from urllib import unquote
from google.appengine.ext import webapp
from google.appengine.api import memcache

import autoproxy2pac
from models import RuleList, UserSetting
from util import useragent, webcached
from settings import DEBUG, MAIN_SERVER, PRESET_PROXIES, MIRRORS, RATELIMIT_ENABLED, RATELIMIT_DURATION, RATELIMIT_QUOTA, MAX_CUSTOM_RULE_NUMBER_FOR_MIRROR, \
    PAC_USER_URL_PREFIX

privoxyConfCode = '''
  if(host == "p.p" || dnsDomainIs(host, "config.privoxy.org")) return PROXY;
'''

class Handler(webapp.RequestHandler):
    @webcached('public,max-age=600')  # 10min
    def get(self, urlpart):
        download = self.request.get('download', None) is not None

        # Redirect to usage page for visits from links (obviously not a browser PAC fetcher)
        if MAIN_SERVER and not download and 'Referer' in self.request.headers:
            self.redirect("/usage?u=" + urlpart, permanent=False)
            return

        if not self.parseRequest(urlpart):
            self.error(404)
            return

        rules = RuleList.getList('gfwlist')
        if rules is None:
            self.error(500)
            return

        pacTime = formatdate(timegm(max(self.settingTime, datetime(*parsedate(rules.date)[:6])).timetuple()), False, True)
        self.response.headers['ETag'] = '"' + pacTime.replace(',', '').replace(' ', '') + '"'
        self.lastModified(pacTime)

        # Load balance
        if MAIN_SERVER and len(self.customRules) <= MAX_CUSTOM_RULE_NUMBER_FOR_MIRROR:
            mirror = self.pickMirror()
            if mirror:
                query = ['e=' + urlsafe_b64encode(r) for r in self.customRules]
                if download: query.append('download')
                mirror = '%s%s?%s' % (mirror, self.proxyDict['urlpart'], '&'.join(query))
                logging.debug('Redirect the PAC fetcher to %s', mirror)
                if not DEBUG:
                    # A fixed server for a rate-limiting cycle
                    self.response.headers['Cache-Control'] = 'public,max-age=%d' % (RATELIMIT_DURATION * 3600)
                    self.redirect(mirror, permanent=False)
                    return

        if RATELIMIT_ENABLED and self.isRateLimited(): return

        customJs = autoproxy2pac.rule2js('\n'.join([''] + self.customRules))
        if self.proxyDict['name'] == 'privoxy': customJs = privoxyConfCode + customJs
        configs = {
            'proxyString': self.proxyString,
            'defaultString': 'DIRECT',
            'customCodePre': customJs,
        }
        pac = autoproxy2pac.generatePac(rules.toDict(), configs, autoproxy2pac.defaultPacTemplate)

        self.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
        if download: self.response.headers['Content-Disposition'] = 'attachment; filename="autoproxy.pac"'
        self.response.out.write(pac)

    userPacRegxp = re.compile(r'^%s([^/\s]+)(?:/(.+))?$' % PAC_USER_URL_PREFIX)
    proxyRegxp = re.compile(r'''^(?P<urlpart>
        (?P<name> [^/\s]+) |
        (?P<type> proxy|http|socks) / (?P<host> [^/\s]+) / (?P<port> \d+)
    )$''', re.VERBOSE)

    def parseRequest(self, urlpart):
        self.customRules = self.request.get_all('c')
        self.customRules += (urlsafe_b64decode(r.encode('ascii')) for r in self.request.get_all('e'))

        match = self.userPacRegxp.match(unquote(urlpart).strip())
        if match:
            setting = UserSetting.gql('WHERE pacName=:1', match.group(1).lower()).get()
            if setting is None: return

            urlpart = match.group(2) or setting.defaultProxy
            self.customRules += setting.customRules
            self.settingTime = setting.lastModified
        else:
            self.settingTime = datetime.min

        match = self.proxyRegxp.match(urlpart.lower())
        if match is None: return
        self.proxyDict = match.groupdict()

        if self.proxyDict['name']:
            if self.proxyDict['name'] not in PRESET_PROXIES: return
            self.proxyString = PRESET_PROXIES[self.proxyDict['name']][1]
        elif self.proxyDict['type']:
            self.proxyDict['type'] = 'SOCKS' if self.proxyDict['type'] == 'socks' else 'PROXY'
            self.proxyString = '%(type)s %(host)s:%(port)s' % self.proxyDict

        # Chrome expects 'SOCKS5' instead of 'SOCKS', see http://j.mp/pac-test
        if useragent.family() == 'Chrome':
            self.proxyString = self.proxyString.replace('SOCKS ', 'SOCKS5 ')

        return True

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
