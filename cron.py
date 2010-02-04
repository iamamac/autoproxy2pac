#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datastore import RuleList

for name, url in (('gfwlist', 'http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt'),):
    r = RuleList.getList(name)
    if r == None:
        r = RuleList(name=name, url=url)
    
    if r.update():
        logging.info('%s updated to %s' , name, r.date)
