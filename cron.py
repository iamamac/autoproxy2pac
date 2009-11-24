#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.api import memcache
from datastore import RuleList
import logging

for name, url in (('gfwlist', 'http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt'),):
    r = RuleList.getList(name)
    if r == None:
        r = RuleList(name=name, url=url)
    
    if r.update():
        logging.info('%s updated to %s' , name, r.date)
        if name == 'gfwlist': memcache.delete('gfwtest.js')
        memcache.delete('changelog/%s.json' % name)
