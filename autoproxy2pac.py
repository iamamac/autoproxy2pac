#!/usr/bin/env python

'''
A tool to automatically download autoproxy's GFW list and convert it to a PAC file
So you can bypass GFW's blockade on almost every browser

@version: 0.1
@requires: python 2.6

@author: Meng Xiangliang @ 9#, Tsinghua University
@contact: 911mxl <AT> gmail (e-mail), mengxl (twitter)

@see: AutoProxy add-on for Firefox (https://addons.mozilla.org/en-US/firefox/addon/11009)

@todo:
- Read parameters from command-line
- Generate PAC file using shExpMatch function instead of regular expression, should be faster,
  but it's already fast enough on Safari 4
'''

pacFilepath = "fuckgfw.pac"
gfwlistUrl = "http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt"
proxyString = "PROXY 166.111.139.13:9876"
directAccessString = "DIRECT"

# Download GFW list
print("Fetching GFW list from %s ..." % gfwlistUrl)

import urllib, base64
from contextlib import closing
with closing(urllib.urlopen(gfwlistUrl)) as response:
    gfwlist = base64.decodestring(response.read())

# Generate PAC file
print("Generating %s ..." % pacFilepath)

with open(pacFilepath, 'w') as f:
    proxyVar = "proxy"
    directAccessVar = "direct"
    
    # PAC header
    f.write('''function FindProxyForURL(url, host) {
  %s = "%s";
  %s = "%s";

''' % (directAccessVar, directAccessString, proxyVar, proxyString))
    
    # The syntax of the list is based on Adblock Plus filter rules (http://adblockplus.org/en/filters)
    #   Filter options (those parts start with "$") is not supported
    # AutoProxy Add-on for Firefox has a Javascript implementation
    #   http://github.com/lovelywcm/autoproxy/blob/master/chrome/content/filterClasses.js
    for line in gfwlist.splitlines()[1:]:
        # Ignore the first line ([AutoProxy x.x]), empty lines and comments
        if line and not line.startswith("!"):
            retString = proxyVar
            
            # Exceptions
            if line.startswith("@@"):
                line = line[2:]
                retString = directAccessVar
            
            # Regular expressions
            if line.startswith("/") and line.endswith("/"):
                jsRegexp = line[1:-1]
            
            # Other cases
            else:
                import re
                # Remove multiple wildcards
                jsRegexp = re.sub(r"\*+", r"*", line)
                # Remove anchors following separator placeholder
                jsRegexp = re.sub(r"\^\|$", r"^", jsRegexp, 1)
                # Escape special symbols
                jsRegexp = re.sub(r"(\W)", r"\\\1", jsRegexp)
                # Replace wildcards by .*
                jsRegexp = re.sub(r"\\\*", r".*", jsRegexp)
                # Process separator placeholders
                jsRegexp = re.sub(r"\\\^", r"(?:[^\w\-.%\u0080-\uFFFF]|$)", jsRegexp)
                # Process extended anchor at expression start
                jsRegexp = re.sub(r"^\\\|\\\|", r"^[\w\-]+:\/+(?!\/)(?:[^\/]+\.)?", jsRegexp, 1)
                # Process anchor at expression start
                jsRegexp = re.sub(r"^\\\|", "^", jsRegexp, 1)
                # Process anchor at expression end
                jsRegexp = re.sub(r"\\\|$", "$", jsRegexp, 1)
                # Remove leading wildcards
                jsRegexp = re.sub(r"^(\.\*)", "", jsRegexp, 1)
                # Remove trailing wildcards
                jsRegexp = re.sub(r"(\.\*)$", "", jsRegexp, 1)
                
                if jsRegexp == "":
                    jsRegexp = ".*"
                    print("WARNING: There is one rule that matches all URL, which is highly *NOT* recommended: %s", line)
            
            f.write('''  if(/%s/i.test(url)) return %s;\n''' % (jsRegexp, retString))
    
    # PAC footer
    f.write('''
  return %s
}
''' % directAccessVar)
