# -*- coding: utf-8 -*-

import os

DEBUG = os.getenv('SERVER_SOFTWARE', 'Dev').startswith('Dev')

MAIN_SERVER = os.getenv('APPLICATION_ID', 'autoproxy2pac') == 'autoproxy2pac'

TEMPLATE_DEBUG = DEBUG

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

MEDIA_URL = '/static/'

CACHE_ENABLED = not DEBUG

RATELIMIT_ENABLED = True

PAC_URL_PREFIX = 'pac/' if MAIN_SERVER else ''

PRESET_PROXIES = {
    'gappproxy'    : ('GAppProxy', 'PROXY 127.0.0.1:8000'),
    'tor'          : ('Tor', 'PROXY 127.0.0.1:8118; SOCKS 127.0.0.1:9050'),
    'jap'          : ('JAP', 'PROXY 127.0.0.1:4001'),
    'your-freedom' : ('Your Freedom', 'PROXY 127.0.0.1:8080'),
    'wu-jie'       : ('无界', 'PROXY 127.0.0.1:9666'),
    'free-gate'    : ('自由门', 'PROXY 127.0.0.1:8580'),
    'puff'         : ('Puff', 'PROXY 127.0.0.1:1984'),
    'privoxy'      : ('Privoxy + SOCKS', 'PROXY 127.0.0.1:8118'),
    'ssh-d'        : ('ssh -D / MyEnTunnel', 'SOCKS 127.0.0.1:7070'),
}

try:
    # Settings not under version control
    from settings2 import *
except ImportError:
    # Base URL of the mirrors, None stands for the main server itself
    MIRRORS = (None,)

    # QUOTA times of retrieval per DURATION (unit: hour) is allowed in maximum
    RATELIMIT_DURATION = 0
    RATELIMIT_QUOTA = lambda ip, ua: 0
