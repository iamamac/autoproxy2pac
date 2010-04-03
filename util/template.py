# -*- coding: utf-8 -*-

import os
from datetime import datetime
from google.appengine.api import users
from google.appengine.ext.webapp import template

import settings

def render(template_, **param):
    currentUrl = os.getenv('PATH_INFO')
    template_path = os.path.join(settings.TEMPLATE_DIR, template_)
    template_dict = {
        'gfwlist_rss': '/changelog/gfwlist.rss',
        'is_dev': settings.DEBUG,
        'language': 'zh-CN',
        'login_url': users.create_login_url(currentUrl),
        'logout_url': users.create_logout_url(currentUrl),
        'media_url': settings.MEDIA_URL,
        'user': users.get_current_user(),
        'url_protocol': 'https://' if os.getenv('HTTPS') == 'on' else 'http://',
    }
    template_dict.update(param)
    return template.render(template_path, template_dict, debug=settings.TEMPLATE_DEBUG)

def mtime(template_):
    return datetime.fromtimestamp(os.stat(os.path.join(settings.TEMPLATE_DIR, template_)).st_mtime)
