from google.appengine.ext import db
from google.appengine.api import memcache
import autoproxy2pac

class RuleList(db.Model):
    name = db.StringProperty(required=True)
    url = db.LinkProperty(required=True)
    date = db.StringProperty()
    raw = db.TextProperty()
    code = db.TextProperty()
    
    def update(self):
        self.raw, timestamp = autoproxy2pac.fetchRuleList(self.url)
        if timestamp == self.date: return False
        
        self.code = autoproxy2pac.rule2js(self.raw)
        self.date = timestamp
        memcache.set(self.name, self)
        self.put()
        
        return True
    
    def toDict(self):
        return { 'ruleListUrl'  : self.url,
                 'ruleListDate' : self.date,
                 'ruleListCode' : self.code }
    
    @classmethod
    def getList(cls, name):
        data = memcache.get(name)
        if data is not None: return data
        
        data = cls.gql('WHERE name=:1', name).get()
        memcache.add(name, data)
        return data
