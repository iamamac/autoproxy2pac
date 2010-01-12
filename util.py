# -*- coding: utf-8 -*-
import os
import logging
import autoproxy2pac
from datastore import RuleList

commonProxy = { 'gappproxy'    : ('GAppProxy', 'PROXY 127.0.0.1:8000'),
                'tor'          : ('Tor', 'PROXY 127.0.0.1:8118; SOCKS 127.0.0.1:9050'),
                'jap'          : ('JAP', 'PROXY 127.0.0.1:4001'),
                'your-freedom' : ('Your Freedom', 'PROXY 127.0.0.1:8080'),
                'wu-jie'       : ('无界', 'PROXY 127.0.0.1:9666'),
                'free-gate'    : ('自由门', 'PROXY 127.0.0.1:8580'),
                'puff'         : ('Puff', 'PROXY 127.0.0.1:1984'),
                'privoxy'      : ('Privoxy + SOCKS', 'PROXY 127.0.0.1:8118'),
              }

privoxyConfCode = '''
  if(host == "p.p" || dnsDomainIs(host, "config.privoxy.org")) return PROXY;
'''

def getBrowserFamily():
    ua = os.environ['HTTP_USER_AGENT']
    
    if 'MSIE' in ua:
        return 'IE'
    elif 'Chrome' in ua:
        return 'Chrome'
    else:
        return None

# Static pages (main page, etc.): 1 h
cacheAgeForStatic = 3600
# Rule related content (PAC file, etc.): 10 min
cacheAgeForRuleRelated = 600

def isCachedByBrowser(handler, age=0, lastModified=None, etag=None):
    '''
    Check browser cache
    @see: http://www.mnot.net/cache_docs/
    
    @return: True if the page is cached (no need to generate the content)
    '''
    if handler.request.headers.get('If-None-Match', 0) == etag or handler.request.headers.get('If-Modified-Since', 0) == lastModified:
        handler.error(304)
        return True
    handler.response.headers['Cache-Control'] = age > 0 and 'public, max-age=%d' % age or 'public, no-cache'
    if lastModified: handler.response.headers['Last-Modified'] = lastModified
    if etag: handler.response.headers['ETag'] = etag
    return False

def notifyRssUpdate(url):
    '''
    Ping FeedBurner to update the feed immediately
    @see: http://feedburner.google.com/fb/a/ping
    '''
    import xmlrpclib
    rpc = xmlrpclib.ServerProxy('http://ping.feedburner.google.com/')
    result = rpc.weblogUpdates.ping('', url)
    if result['flerror']: logging.warning('Unable to notify FeedBurner for %s', url)

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
    if getBrowserFamily() == 'Chrome':
        proxyString = proxyString.replace('SOCKS', 'SOCKS5')
    
    configs = { 'proxyString'   : proxyString,
                'defaultString' : "DIRECT" }
    if proxy == 'privoxy': configs['customCodePost'] = privoxyConfCode
    pac = autoproxy2pac.generatePac(rules.toDict(), configs, autoproxy2pac.defaultPacTemplate)
    
    handler.response.headers['Content-Type'] = 'application/x-ns-proxy-autoconfig'
    handler.response.out.write(pac)
