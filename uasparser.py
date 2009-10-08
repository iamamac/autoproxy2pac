"""
A python interface to http://user-agent-string.info/
A python version of http://user-agent-string.info/download/UASparser

By Hicro Kee (http://hicrokee.com)
email: hicrokee AT gmail DOT com

Usage:

from uasparser import UASparser

uas_parser = UASparser('/path/to/your/cache/folder')

result = uas_parser.parse('YOUR_USERAGENT_STRING',entire_url='ua_icon,os_icon') #only 'ua_icon' or 'os_icon' or both are allowed in entire_url 


Examples:

from uasparser import UASparser
uas = UASparser()
test = ['SonyEricssonK750i/R1L Browser/SEMC-Browser/4.2 Profile/MIDP-2.0 Configuration/CLDC-1.1',
        'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.8.1.18) Gecko/20081029 Firefox/2.0.0.18',
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; en-us) AppleWebKit/525.26.2 (KHTML, like Gecko) Version/3.2 Safari/525.26.12',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows XP 5.1) Lobo/0.98.4',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; )',
        'Opera/9.80 (Windows NT 5.1; U; cs) Presto/2.2.15 Version/10.00',
        'boxee (alpha/Darwin 8.7.1 i386 - 0.9.11.5591)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; CSM-NEWUSER; GTB6; byond_4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 1.1.4322; .NET CLR 3.0.04506.648; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; InfoPath.1)',
        'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',
        ]

for item in test:
    res = uas.parse(item)
    print "---%s: %s @ %s" % (res['typ'],res['ua_name'],res['os_name'])

"""

import os

import urllib2,re,time
try:
    import cPickle as pickle
except:
    import pickle

class UASException(Exception):
    pass

class UASparser:
    
    ini_url  = 'http://user-agent-string.info/rpc/get_data.php?key=free&format=ini'
    ver_url  = 'http://user-agent-string.info/rpc/get_data.php?key=free&format=ini&ver=y'
    info_url = 'http://user-agent-string.info'
    os_img_url = 'http://user-agent-string.info/pub/img/os/%s'
    ua_img_url = 'http://user-agent-string.info/pub/img/ua/%s'

    cache_file_name = 'cache' 
    cache_dir = ''
    cache_data = None
    update_interval = 3600*24*10 # 10 days
    
    def __init__(self,cache_dir=None):
        """
        Create an UASparser to parse useragent strings.
        cache_dir should be appointed or set to the path of program by default
        """
        self.cache_dir = cache_dir and cache_dir or os.path.abspath( os.path.dirname(__file__) )
        if not os.access(self.cache_dir, os.W_OK):
            raise UASException("Cache directory %s is not writable.")
        self.cache_file_name = os.path.join( self.cache_dir, self.cache_file_name)
    
    def parse(self,useragent,entire_url=''):
        """
        Get the information of an useragent string
        Args:
            useragent: String, an useragent string
            entire_url: String, write the key labels which you want to get an entire url split by comma, expected 'ua_icon' or 'os_icon'.
        """
        ret = {
               'typ':'unknown',
               'ua_family':'unknown',
               'ua_name':'unknown',
               'ua_url':'unknown',
               'ua_company':'unknown',
               'ua_company_url':'unknown',
               'ua_icon':'unknown.png',
               'ua_info_url':'unknown',
               'os_family':'unknown',
               'os_name':'unknown',
               'os_url':'unknown',
               'os_company':'unknown',
               'os_company_url':'unknown',
               'os_icon':'unknown.png',
               }
        
        os_index = ['os_family','os_name','os_url','os_company','os_company_url','os_icon']
        ua_index = ['ua_family','ua_name','ua_url','ua_company','ua_company_url','ua_icon','','ua_info_url']
        
        if 'ua_icon' in entire_url: ret['ua_icon'] = self.ua_img_url % ret['ua_icon']
        if 'os_icon' in entire_url: ret['os_icon'] = self.os_img_url % ret['os_icon']
        
        def toPythonReg(reg):
            reg_l = reg[1:reg.rfind('/')] # modify the re into python format
            reg_r = reg[reg.rfind('/')+1:]
            flag = 0
            if 's' in reg_r: flag = flag | re.S
            if 'i' in reg_r: flag = flag | re.I
            return re.compile(reg_l,flag)            
        
        #Check argument
        if not useragent:
            raise UASException("Excepted argument useragent is not given.")
        
        #Load cache data
        data = self.loadData()
        
        #Is it a spider?
        for index in data['robots']:
            test = data['robots'][index]
            if test[0] == useragent:
                ret['typ'] = 'Robot'
                for i in range(1,len(test)+1): #fill out the structure.
                    if i < 6:
                        ret[ua_index[i-1]] = test[i]
                    elif i==6:
                        ret[ua_index[i-1]] = ( 'ua_icon' in entire_url and self.ua_img_url or "%s") % test[i]
                    elif i==7:
                        if test[7]: #OS detail
                            for j in range(1,len(data['os'][test[7]])):
                                ret[os_index[j]] = data['os'][test[7]][j]
                    elif i==8:
                        ret[ua_index[i-1]] = ''.join([self.info_url,test[i]])
                
                return ret
        
        #A browser
        id_browser = None
        for index in data['browser_reg']:
            test = data['browser_reg'][index]
            test_rg = toPythonReg(test[0]).findall(useragent) #All regular expression should be in python format
            if test_rg:
                id_browser = test[1] #Bingo
                info = test_rg[0]
                break

        # Get broser detail
        if id_browser:
            _index = ['ua_family','ua_url','ua_company','ua_company_url','ua_icon','ua_info_url']
            try:
                if data['browser'].has_key(id_browser): #Any better method to figure out it?
                    for i in range(1,len(data['browser'][id_browser])+1):
                        if i <= 4:
                            ret[_index[i-1]] = data['browser'][id_browser][i]
                        elif i == 5:
                            ret[_index[i-1]] = ( 'ua_icon' in entire_url and self.ua_img_url or "%s") % data['browser'][id_browser][i]
                        else:
                            ret[_index[i-1]] = "".join([self.info_url,data['browser'][id_browser][i]])
            except:
                pass
            
            try:
                ret['typ'] = data['browser_type'][data['browser'][id_browser][0]][0]
                ret['ua_name'] = "%s %s" % ( data['browser'][id_browser][1], info )
            except:
                pass
        
        # Get OS detail
        if data['browser_os'].has_key(id_browser):
            try:
                os_id = int(data['browser_os'][id_browser][0])
                for i in range(0,len(data['os'][os_id])):
                    if i<5:
                        ret[os_index[i]] = data['os'][os_id][i]
                    else:
                        ret[os_index[i]] = ( 'os_icon' in entire_url and self.os_img_url or "%s") % data['os'][os_id][i]
                return ret
            except:
                pass
        
        #Try to match an OS
        os_id = None  
        for index in data['os_reg']:
            test = data['os_reg'][index]
            test_rg = toPythonReg(test[0]).match(useragent)
            if test_rg:
                os_id = test[1]
                break

        # Get OS detail
        if os_id and data['os'].has_key(os_id): 
            for i in range(0,len(data['os'][os_id])):
                if i<5:
                    ret[os_index[i]] = data['os'][os_id][i]
                else:
                    ret[os_index[i]] = ( 'os_icon' in entire_url and self.os_img_url or "%s") % data['os'][os_id][i]
                    
        return ret   
    
    def _parseIniFile(self,file):
        """
        Parse an ini file into a dictionary structure
        """
        data = {}
        current_section = 'unknown'        
        section_pat = re.compile(r'^\[(\S+)\]$')
        option_pat = re.compile(r'^(\d+)\[\]\s=\s"(.*)"$')
        
        #step by line
        for line in file.split("\n"):
            option = option_pat.findall(line)
            if option: #do something for option
                if data[current_section].has_key(option[0][0]):
                    data[current_section][option[0][0]].append(option[0][1])
                else:
                    data[current_section][option[0][0]] = [option[0][1],]
            else:
                section = section_pat.findall(line) #do something for section
                if section:
                    current_section = section[0]
                    data[current_section] = {}
        return data
    
    def _fetchURL(self,url):
        """
        Get remote context by a given url
        """
        resq = urllib2.Request(url)
        context = urllib2.urlopen(resq)
        return context.read()
    
    def _checkCache(self):
        """
        check whether the cache available or not?
        """
        cache_file = self.cache_file_name
        if not os.path.exists(cache_file):
            return False
        else:
            mtime = os.path.getmtime(cache_file)
            if mtime < time.time() - self.update_interval:
                return False

        return True
    
    def updateData(self):
        """
        Check whether data is out-of-date
        """
        ver_data = None
        
        #Check the latest version first
        #pass if no need to update
        try:
            ver_data = self._fetchURL(self.ver_url)
            if os.path.exists(self.cache_file_name):
                cache_file = open(self.cache_file_name,'rb')
                data = pickle.load(cache_file)
                if data['version'] == ver_data:
                    return True
        except:
            raise UASException("Failed to get version of lastest data")
        
        try:
            cache_file = open(self.cache_file_name,'wb')
            ini_file = self._fetchURL(self.ini_url)
            ini_data = self._parseIniFile(ini_file)
            if ver_data:
                ini_data['version'] = ver_data
        except:
            raise UASException("Failed to download cache data")
        
        pickle.dump(ini_data, cache_file)
            
        return True
        
    def loadData(self):
        """
        start to load cache data
        """
        if not self._checkCache():
            self.updateData()
        else:
            if self.cache_data: #no need to load
                return self.cache_data
                
        self.cache_data = pickle.load(open(self.cache_file_name,'rb'))
        
        return self.cache_data

#simple test
#uas = UASparser()
#print uas.parse('SonyEricssonK750i/R1L Browser/SEMC-Browser/4.2 Profile/MIDP-2.0 Configuration/CLDC-1.1','os_icon')
