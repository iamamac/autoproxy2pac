# -*- coding: utf-8 -*-

import os
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from settings import DEBUG, MAIN_SERVER, CACHE_ENABLED, RATELIMIT_ENABLED, PAC_URL_PREFIX
from handlers import *

# Log a message each time this module get loaded.
logging.debug(
    'Loading %s %s, MAIN_SERVER = %s, CACHE_ENABLED = %s, RATELIMIT_ENABLED = %s, PAC_URL_PREFIX = "%s"',
    os.getenv('APPLICATION_ID'), os.getenv('CURRENT_VERSION_ID'),
    MAIN_SERVER, CACHE_ENABLED, RATELIMIT_ENABLED, PAC_URL_PREFIX,
)

# A hack to be able to get the status of a Response instance, read-only
webapp.Response.status = property(lambda self: self._Response__status[0])

urlMapping = [
    ('/tasks/update', tasks.update.Handler),
    ('/%s(.+)' % PAC_URL_PREFIX, pac_generate.OnlineHandler),
]
if MAIN_SERVER: urlMapping += [
    ('/', pac_config.MainHandler),
    ('/usage', pac_config.UsageHandler),
    ('/pac/', pac_generate.DownloadHandler),
    ('/gfwtest.js', gfwtest.JsLibHandler),
    ('/gfwtest', gfwtest.TestPageHandler),
    ('/changelog/(.*)\.json', changelog.JsonHandler),
    ('/changelog/(.*)\.rss', changelog.FeedHandler),
    ('/changelog/(.*)', changelog.HtmlHandler),
    ('/tasks/feed_ping', tasks.feedping.FeedBurnerHandler),
]
application = webapp.WSGIApplication(urlMapping, DEBUG)

def main():
    if DEBUG: logging.getLogger().setLevel(logging.DEBUG)

    if os.getenv('AUTH_DOMAIN') != 'gmail.com':
        logging.warn('Fixing auth domain (%r)', os.getenv('AUTH_DOMAIN'))
        os.environ['AUTH_DOMAIN'] = 'gmail.com'

    run_wsgi_app(application)

if __name__ == '__main__':
    main()
