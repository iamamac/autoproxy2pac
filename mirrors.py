# -*- coding: utf-8 -*-

import random

mirrors = (
            None, # the main site itself
            "http://autoproxy2pac-alfa.appspot.com",
            "http://autoproxy2pac-bravo.appspot.com",
          )

def pick():
    return random.choice(mirrors)
