from datastore import RuleList

print 'Content-Type: text/plain'
print ''

for name, url in (('gfwlist', 'http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt'),):
    r = RuleList.getList(name)
    if r == None:
        r = RuleList(name=name, url=url)
    
    r.update()
    r.put()
    print('Update %s to %s' % (name, r.date))
