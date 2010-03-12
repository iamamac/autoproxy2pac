# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.api import memcache

import autoproxy2pac
from util import memcached

class RuleList(db.Model):
    name = db.StringProperty(required=True)
    url = db.LinkProperty(required=True)
    date = db.StringProperty()
    raw = db.TextProperty()
    code = db.TextProperty()

    def update(self):
        rawOld = self.raw
        self.raw, timestamp = autoproxy2pac.fetchRuleList(self.url)
        if timestamp == self.date: return False

        self.code = autoproxy2pac.rule2js(self.raw)
        self.date = timestamp
        memcache.set(self.name, self, namespace='rule')
        self.put()

        if rawOld:
            diff = ChangeLog.new(self, rawOld, self.raw)
            if diff: diff.put()

        return True

    def toDict(self):
        return { 'ruleListUrl'  : self.url,
                 'ruleListDate' : self.date,
                 'ruleListCode' : self.code }

    @classmethod
    @memcached(key=(lambda _, name:name), namespace='rule')
    def getList(cls, name):
        return cls.gql('WHERE name=:1', name).get()

class ChangeLog(db.Model):
    ruleList = db.ReferenceProperty(RuleList, required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    add = db.StringListProperty()
    remove = db.StringListProperty()

    @classmethod
    def new(cls, ruleList, old, new):
        ret = ChangeLog(ruleList=ruleList)

        from difflib import SequenceMatcher
        toSeq = lambda raw: [l for l in raw.splitlines()[1:] if l and not l.startswith('!')]
        old = toSeq(old)
        new = toSeq(new)
        for tag, i1, i2, j1, j2 in SequenceMatcher(a=old, b=new).get_opcodes():
            if tag != 'equal':
                ret.remove.extend(old[i1:i2])
                ret.add.extend(new[j1:j2])

        # Ignore unmodified rules (just moved to another place)
        for line in set(ret.add).intersection(set(ret.remove)):
            ret.add.remove(line)
            ret.remove.remove(line)

        if ret.add or ret.remove:
            return ret
        else:
            return None
