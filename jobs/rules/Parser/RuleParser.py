# This code is published under GPL v2 License Terms
#
# Descrpition: General Purpose rule parser
#
# Author: Pablo Rincon Crespo 
# Author: Josh Smith
#
# 5/12/2009

import re,sys
from binascii import *

class Rule:
    raw=''
    type=''
    proto=''
    rawsources=''
    rawsrcports=''
    direc=''
    rawdestinations=''
    rawdesports=''
    rawoptions=''
    active=1

    # We should implement all the options as attibutes, and this list should be empty in newer versions
    options=[]

    contents=[]
    uricontents=[]
    flow=None
    msg=''
    rev=''
    sid =''
    #isHTTP = False
    
    def __init__(self,rule):

	try:
		p = re.compile(r'^(?P<general>[^\(]+)\s*\((?P<rawoptions>.*)\)\s*$')
		if rule.startswith('#'):
			self.active = 0
			self.raw = rule.lstrip('# ')
		else:
			self.raw = rule
			
		m = p.search(rule)
		general = m.group("general")
		rawoptions = m.group("rawoptions")

		if general != None and rawoptions != None:
			pg = re.compile(r'(?P<type>[^\s]+)\s+(?P<proto>[^\s]+)\s+(?P<rawsources>[^\s]+)\s+(?P<rawsrcports>[^\s]+)\s+(?P<direc>[^\s]+)\s+(?P<rawdestinations>[^\s]+)\s+(?P<rawdesports>[^\s]+)\s*')
			m = pg.search(general)

			self.type = m.group('type')
			self.proto = m.group('proto')
			self.rawsources = m.group('rawsources')
			self.rawsrcports = m.group('rawsrcports')
			self.direc = m.group('direc')
			self.rawdestinations = m.group('rawdestinations')
			self.rawdesports = m.group('rawdesports')
			self.rawoptions = rawoptions
            
			po = re.compile(r'\s*([^;]+[^\\])\s*;')
			optlist = po.findall(rawoptions)

			for i in optlist:
				pi = re.compile(r'^(?P<key>[^:]+)(\s*:\s*(?P<value>.*))?\s*$')
				mi = pi.search(i)
				k = mi.group("key")
				v = mi.group("value")
				if v is None:
					v = True

				if k == "sid":
					self.sid = v
					continue
				if k == "rev":
					self.rev = v
					continue
       
		else:
			print "Error loading rule " +str(rule)
	except NameError as e:
		print ('Typeerror while reading rule contents')
		print('========== BEGIN =============')
		print e
		print sys.exc_info
		print('=========== END ==============')

	except ImportError as e:
		print('General Error in rule constructor')
		print('========== BEGIN =============')
		print rule
		print '---'
		print optlist
		print 'Exception: %s' % (e)
		print('=========== END ==============')
		return
		
    def __str__(self):
        r = "\nGeneral Fields:\n"

        r = r + "\n" + "Options in raw: "+ self.rawoptions + "\n"
        return r

