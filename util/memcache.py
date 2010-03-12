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

class responsecached(object):
    '''
    Decorate RequestHandler.get/post/etc. to keep the response in memcache
    A convenient wrapper of memcached

    @note: Multiple memcache items may be generated using the default key algorithm
    '''
    def __init__(self, time=0, key=None, namespace='response'):
        self.time = time
        self.key = key if key else lambda h, *_: h.request.path_qs
        self.namespace = namespace

    def __call__(self, f):
        @wraps(f)
        def wrapped(handler, *args):
            @memcached(self.key, self.time, self.namespace)
            def getResponse(handler, *args):
                f(handler, *args)
                return handler.response

            # In `WSGIApplication.__call__`, `handler.response` is just a reference
            # of the local variable `response`, whose `wsgi_write` method is called.
            # So just assign a new response object to `handler.response` will not work.
            handler.response.__dict__ = getResponse(handler, *args).__dict__

        return wrapped
