# -*- coding: utf-8 -*-

import os

DEBUG = os.getenv('SERVER_SOFTWARE', 'Dev').startswith('Dev')

MAIN_SERVER = os.getenv('APPLICATION_ID', 'autoproxy2pac') == 'autoproxy2pac'

TEMPLATE_DEBUG = DEBUG

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

MEDIA_URL = '/static/'

CACHE_ENABLED = not DEBUG

RATELIMIT_ENABLED = not DEBUG

try:
    # Settings not under version control
    from settings2 import *
except ImportError:
    # Base URL of the mirrors, None stands for the main server itself
    MIRRORS = (None,)

    # QUOTA times of retrieval per DURATION (unit: hour) is allowed in maximum
    RATELIMIT_DURATION = 0
    RATELIMIT_QUOTA = lambda ip, ua: 0
