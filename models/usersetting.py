# -*- coding: utf-8 -*-

from google.appengine.ext import db

class UserSetting(db.Model):
    defaultProxy = db.StringProperty(required=True)
    pacName = db.StringProperty(required=True)
    customRules = db.StringListProperty()
    lastModified = db.DateTimeProperty(required=True, auto_now=True)
