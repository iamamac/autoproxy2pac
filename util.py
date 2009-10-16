def getBrowserFamily(headers):
    ua = headers['User-Agent']
    
    if 'MSIE' in ua:
        return 'IE'
    elif 'Chrome' in ua:
        return 'Chrome'
    else:
        return None
