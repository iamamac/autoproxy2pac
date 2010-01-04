# -*- coding: utf-8 -*-
import os
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
