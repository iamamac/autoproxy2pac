# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.api import memcache

import util
import autoproxy2pac
from models import RuleList

jsFileTemplate = '''/*
 * Provide a javascript function to determine whether a URL is blocked in mainland China
 * You can get this file at http://autoproxy2pac.appspot.com/gfwtest.js
 *
 * Usage: isBlockedByGFW(url), returns true if the URL is blocked
 *
 * Last update: %(ruleListDate)s
 */

// Base64 code from Tyler Akins -- http://rumkin.com
function decode64(_1){var _2="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";var _3="";var _4,_5,_6;var _7,_8,_9,_a;var i=0;_1=_1.replace(/[^A-Za-z0-9\+\/\=]/g,"");do{_7=_2.indexOf(_1.charAt(i++));_8=_2.indexOf(_1.charAt(i++));_9=_2.indexOf(_1.charAt(i++));_a=_2.indexOf(_1.charAt(i++));_4=(_7<<2)|(_8>>4);_5=((_8&15)<<4)|(_9>>2);_6=((_9&3)<<6)|_a;_3=_3+String.fromCharCode(_4);if(_9!=64){_3=_3+String.fromCharCode(_5);}if(_a!=64){_3=_3+String.fromCharCode(_6);}}while(i<_1.length);return _3;};

// Encode the function using Base64 for security purpose
eval(decode64("%(encodedFunc)s"))
'''

jsFuncTemplate = '''function isBlockedByGFW(url) {
  %(proxyVar)s = true;
  %(defaultVar)s = false;

%(ruleListCode)s

  return %(defaultVar)s;
}
'''

def generateJs(rules):
    import base64
    data = { 'proxyVar'   : autoproxy2pac.proxyVar,
             'defaultVar' : autoproxy2pac.defaultVar }
    data.update(rules)
    data['encodedFunc'] = base64.b64encode(jsFuncTemplate % data)
    return jsFileTemplate % data

class JsLibHandler(webapp.RequestHandler):
    def get(self):
        rules = RuleList.getList('gfwlist')
        if rules is None:
            self.error(500)
            return

        if util.isCachedByBrowser(self, util.cacheAgeForRuleRelated, rules.date): return

        js = memcache.get('gfwtest.js')
        if js is None:
            js = generateJs(rules.toDict())
            memcache.add('gfwtest.js', js)

        self.response.headers['Content-Type'] = 'application/x-javascript'
        self.response.out.write(js)

class TestPageHandler(webapp.RequestHandler):
    def get(self):
        if util.isCachedByBrowser(self, util.cacheAgeForStatic): return

        self.response.out.write(util.renderTemplate('gfwtest.html'))
