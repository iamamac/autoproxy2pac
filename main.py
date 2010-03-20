# -*- coding: utf-8 -*-

import os
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from settings import DEBUG
from handlers import *

# Log a message each time this module get loaded.
logging.info('Loading %s, app version = %s', __name__, os.getenv('CURRENT_VERSION_ID'))

# A hack to be able to get the status of a Response instance, read-only
webapp.Response.status = property(lambda self: self._Response__status[0])

application = webapp.WSGIApplication([
    ('/', pac_config.MainHandler),
    ('/usage', pac_config.UsageHandler),
    ('/pac/', pac_generate.DownloadHandler),
    ('/pac/(.*)', pac_generate.OnlineHandler),
    ('/gfwtest.js', gfwtest.JsLibHandler),
    ('/gfwtest', gfwtest.TestPageHandler),
    ('/changelog/(.*)\.json', changelog.JsonHandler),
    ('/changelog/(.*)\.rss', changelog.FeedHandler),
    ('/changelog/(.*)', changelog.HtmlHandler),
    ('/tasks/feed_ping', tasks.feedping.FeedBurnerHandler),
    ('/tasks/update', tasks.update.Handler),
], debug=DEBUG)

def main():
    if DEBUG: logging.getLogger().setLevel(logging.DEBUG)

    if os.getenv('AUTH_DOMAIN') != 'gmail.com':
        logging.warn('Fixing auth domain (%r)', os.getenv('AUTH_DOMAIN'))
        os.environ['AUTH_DOMAIN'] = 'gmail.com'

    run_wsgi_app(application)

if __name__ == '__main__':
    main()
