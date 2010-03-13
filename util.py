# -*- coding: utf-8 -*-

import os
import logging
from google.appengine.ext.webapp import template

import settings

def renderTemplate(_template, **param):
    template_path = os.path.join(settings.TEMPLATE_DIR, _template)
    template_dict = {
        'is_dev': settings.DEBUG,
        'language': 'zh-CN',
        'media_url': settings.MEDIA_URL,
    }
    template_dict.update(param)
    return template.render(template_path, template_dict, debug=settings.TEMPLATE_DEBUG)

def getBrowserFamily():
    ua = os.getenv('HTTP_USER_AGENT')

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
    if result['flerror']: logging.warning('Unable to notify FeedBurner for %s: %s', url, result['message'])
