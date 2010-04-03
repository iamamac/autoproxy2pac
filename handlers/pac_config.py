# -*- coding: utf-8 -*-

from google.appengine.ext import webapp

from settings import PAC_URL_PREFIX, PRESET_PROXIES
from util import template, useragent, webcached

class MainHandler(webapp.RequestHandler):
    @webcached(('public,max-age=3600', 'private,max-age=3600'), 'Cookie')  # 1h
    def get(self):
        self.lastModified(template.mtime('index.html'))
        self.response.out.write(template.render('index.html',
            presetProxies=((k, v[0]) for k, v in PRESET_PROXIES.items()),
            pacUrlPrefix=PAC_URL_PREFIX,
        ))

class UsageHandler(webapp.RequestHandler):
    @webcached('public,max-age=86400')  # 24h
    def get(self):
        self.lastModified(template.mtime('usage.html'))

        url = self.request.get('u')
        if url: url = 'http://%s/%s%s' % (self.request.host, PAC_URL_PREFIX, url)

        self.response.out.write(template.render('usage.html',
            url=url,
            browser=useragent.family(),
        ))
