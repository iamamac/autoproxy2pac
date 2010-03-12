# -*- coding: utf-8 -*-

from functools import wraps
from google.appengine.api import memcache

from settings import CACHE_ENABLED

class memcached(object):
    '''
    Decorate any function or method whose return value to keep in memcache

    @param key: Can be a string or a function (takes the same arguments as the
                wrapped function, and returns a string key)
    @param time: Optional expiration time, either relative number of seconds from
                 current time (up to 1 month), or an absolute Unix epoch time
    @param namespace: An optional namespace for the key

    @note: Set CACHE_ENABLED to False to globally disable memcache
    '''
    def __init__(self, key, time=0, namespace=None):
        self.key = key
        self.time = time
        self.namespace = namespace

    def __call__(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            key = self.key(*args, **kwargs) if callable(self.key) else self.key

            data = memcache.get(key)
            if data is not None: return data

            data = f(*args, **kwargs)
            memcache.set(key, data, self.time, self.namespace)
            return data

        return wrapped if CACHE_ENABLED else f
