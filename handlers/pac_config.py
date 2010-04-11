# -*- coding: utf-8 -*-

from google.appengine.api import users
from google.appengine.ext import webapp

from models import UserSetting
from settings import PAC_URL_PREFIX, PAC_USER_URL_PREFIX, PRESET_PROXIES
from util import template, useragent, webcached

class MainHandler(webapp.RequestHandler):
    @webcached(('public,max-age=3600', 'private,max-age=3600'), 'Cookie')  # 1h
    def get(self):
        user = users.get_current_user()

        self.lastModified(template.mtime('index.html'))
        self.response.out.write(template.render('index.html',
            presetProxies=((k, v[0]) for k, v in PRESET_PROXIES.items()),
            pacUrlPrefix=PAC_URL_PREFIX,
            pacUserUrlPrefix=PAC_USER_URL_PREFIX,
            userSetting=UserSetting.get_by_key_name(user.user_id()) if user else None,
        ))

    def post(self):
        user = users.get_current_user()
        if not user or not self.request.get('customize'): return

        pacName = self.request.get('pacname', '').lower()
        if pacName != user.nickname().lower():
            self.error(400)
            return

        UserSetting(
            key_name=user.user_id(),
            defaultProxy=self.request.get('proxy'),
            pacName=pacName,
            customRules=self.request.get('addrules').splitlines(),
        ).put()

        if self.request.get('usage') != 'online':
            self.redirect('/%s%s%s?download' % (PAC_URL_PREFIX, PAC_USER_URL_PREFIX, pacName), permanent=False)

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
