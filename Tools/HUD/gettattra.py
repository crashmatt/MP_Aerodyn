'''
Created on 14 Jun 2015

@author: matt
'''
#from dns.rdataclass import NONE

def getattra(obj, attr, default):
    if("[" in attr):
        splits = attr.split("[")
        index = int(splits[1].replace("]", ""))
        thearray = getattr(obj, splits[0], None)
        if(thearray is not None):
            return thearray[index]
        else:
            return default
        
    else:
        return getattr(obj, attr, default)