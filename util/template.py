# -*- coding: utf-8 -*-

import os
from datetime import datetime
from google.appengine.ext.webapp import template

import settings

def render(template_, **param):
    return template.render(os.path.join(settings.TEMPLATE_DIR, template_), dict(
        is_dev=settings.DEBUG,
        media_url=settings.MEDIA_URL,
        **param), debug=settings.TEMPLATE_DEBUG)

def mtime(template_):
    return datetime.fromtimestamp(os.stat(os.path.join(settings.TEMPLATE_DIR, template_)).st_mtime)
