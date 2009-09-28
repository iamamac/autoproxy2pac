from google.appengine.ext import db
from google.appengine.api import memcache
import autoproxy2pac

class RuleList(db.Model):
    name = db.StringProperty(required=True)
    url = db.LinkProperty(required=True)
    date = db.StringProperty()
    code = db.TextProperty()
    
    def update(self):
        list, self.date = autoproxy2pac.fetchRuleList(self.url)
        self.code = autoproxy2pac.rule2js(list)
        memcache.set(self.name, self)
    
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
