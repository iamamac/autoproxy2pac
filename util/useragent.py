# -*- coding: utf-8 -*-

import os

def family():
    ua = os.getenv('HTTP_USER_AGENT')

    if 'MSIE' in ua:
        return 'IE'
    elif 'Chrome' in ua:
        return 'Chrome'
    else:
        return None
