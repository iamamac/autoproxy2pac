from google.appengine.ext import db
import autoproxy2pac

class RuleList(db.Model):
    name = db.StringProperty(required=True)
    url = db.LinkProperty(required=True)
    date = db.StringProperty()
    code = db.TextProperty()
    
    def update(self):
        list, self.date = autoproxy2pac.fetchRuleList(self.url)
        self.code = autoproxy2pac.rule2js(list)
    
    def toDict(self):
        return { 'ruleListUrl'  : self.url,
                 'ruleListDate' : self.date,
                 'ruleListCode' : self.code }
    
    @classmethod
    def getList(cls, name):
        return cls.gql('WHERE name=:1', name).get()
