# -*- coding: utf-8 -*-

import os

DEBUG = os.getenv('SERVER_SOFTWARE').startswith('Dev')

TEMPLATE_DEBUG = DEBUG

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

MEDIA_URL = '/static/'
